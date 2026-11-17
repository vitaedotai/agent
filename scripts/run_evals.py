"""Run the behavioural cases in evals/cases.json against a live model, several times each.

A trial installs only the named skills, sends the request, and scores the reply per
statement. Plain checks (a pattern, a forbidden tool call) cost nothing; the `judge`
statements for a trial are graded together in one extra model call. Nothing is sent,
saved or booked: the cases are fictional and the stub tools do nothing.

  ANTHROPIC_API_KEY=... python3 scripts/run_evals.py --dry-run     # plan and call count, no calls
  ANTHROPIC_API_KEY=... python3 scripts/run_evals.py               # all cases, 3 runs each
  ANTHROPIC_API_KEY=... python3 scripts/run_evals.py --case outreach-missing-facts --runs 5

Exit code 0 when every case meets the bar, 1 when one does not, 2 on a usage error.
Replies are written to evals/results/ (untracked): read the failures, and some passes,
because a judge can be satisfied for the wrong reason.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / 'evals' / 'cases.json'
DEFAULT_MODEL = 'claude-haiku-5-5'
DEFAULT_RUNS = 3
DEFAULT_MAX_CALLS = 120
CHECK_TYPES = {'absent', 'present', 'no_tool_call', 'judge'}
MAX_TOKENS = 1500
JUDGE_MAX_TOKENS = 600

PREAMBLE = (
    'You are an AI assistant for recruiters. The skills below are installed, and nothing '
    'else is. Follow them when the request fits.\n\n'
)


def load_cases(path=CASES):
    return json.loads(Path(path).read_text())['cases']


def skill_names(root=ROOT):
    return sorted(p.parent.name for p in (root / 'skills').glob('*/SKILL.md'))


def problems(cases, root=ROOT):
    """Structural errors in the case file; empty when it is sound."""
    errors, seen = [], set()
    installed = set(skill_names(root))
    for case in cases:
        cid = case.get('id', '?')
        if cid in seen:
            errors.append(f'{cid}: duplicate id')
        seen.add(cid)
        for key in ('id', 'title', 'skills', 'request', 'checks'):
            if not case.get(key):
                errors.append(f'{cid}: missing {key}')
        for name in case.get('skills', []):
            if name != 'all' and name not in installed:
                errors.append(f'{cid}: unknown skill {name}')
        ids = set()
        for check in case.get('checks', []):
            kind = check.get('type')
            if kind not in CHECK_TYPES:
                errors.append(f"{cid}: unknown check type {kind}")
            if not check.get('id') or not check.get('statement'):
                errors.append(f'{cid}: a check needs an id and a statement')
            if check.get('id') in ids:
                errors.append(f"{cid}: duplicate check {check.get('id')}")
            ids.add(check.get('id'))
            if kind in ('absent', 'present'):
                try:
                    re.compile(check.get('pattern', ''))
                except re.error:
                    errors.append(f"{cid}/{check.get('id')}: bad pattern")
            if kind == 'no_tool_call' and check.get('tool') not in {t['name'] for t in case.get('tools', [])}:
                errors.append(f"{cid}/{check.get('id')}: tool is not defined on the case")
    return errors


def build_system(case, root=ROOT):
    names = skill_names(root) if case['skills'] == ['all'] else case['skills']
    parts = [PREAMBLE]
    for name in names:
        parts.append(f'<skill name="{name}">\n{(root / "skills" / name / "SKILL.md").read_text()}\n</skill>\n')
    if case.get('context'):
        parts.append(f"\nSession facts (fictional test data; nothing here is real):\n{case['context']}\n")
    return ''.join(parts)


def planned_calls(cases, runs):
    return sum(runs * (1 + any(c['type'] == 'judge' for c in case['checks'])) for case in cases)


def estimate_input_tokens(cases, runs, root=ROOT):
    """Rough input size (4 characters per token); the real count comes from the API."""
    total = 0
    for case in cases:
        total += runs * (len(build_system(case, root)) + len(case['request'])) // 4
        if any(c['type'] == 'judge' for c in case['checks']):
            total += runs * 800
    return total


def call_anthropic(model, system, user, tools=None, max_tokens=MAX_TOKENS, temperature=1.0):
    key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    base = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.anthropic.com').rstrip('/')
    body = {'model': model, 'max_tokens': max_tokens, 'temperature': temperature,
            'system': system, 'messages': [{'role': 'user', 'content': user}]}
    if tools:
        body['tools'] = tools
    request = urllib.request.Request(
        f'{base}/v1/messages', data=json.dumps(body).encode(), method='POST',
        headers={'x-api-key': key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = json.load(response)
            break
        except urllib.error.HTTPError as error:
            if error.code in (429, 500, 502, 503, 529) and attempt < 2:
                time.sleep(2 ** attempt * 2)
                continue
            raise RuntimeError(f'model call failed: HTTP {error.code}') from None
    blocks = data.get('content', [])
    usage = data.get('usage', {})
    return {
        'text': '\n'.join(b.get('text', '') for b in blocks if b.get('type') == 'text'),
        'tool_calls': [b['name'] for b in blocks if b.get('type') == 'tool_use'],
        'tokens_in': usage.get('input_tokens', 0),
        'tokens_out': usage.get('output_tokens', 0),
    }


def judge(statements, case, reply, model, call):
    """Grade the judge statements for one reply. An unreadable answer fails every statement."""
    listing = '\n'.join(f"{s['id']}: {s['statement']}" for s in statements)
    system = ('You grade an AI assistant\'s reply against statements. Mark a statement true only if the '
              'reply clearly satisfies it; if it is unclear, mark it false. Answer with one JSON object '
              'that maps each statement id to true or false, and nothing else.')
    user = (f"Facts given to the assistant:\n{case.get('context', '(none)')}\n\n"
            f"The user's request:\n{case['request']}\n\n<reply>\n{reply['text'] or '(no text, tool call only)'}\n</reply>\n\n"
            f"Statements:\n{listing}")
    out = call(model, system, user, None, JUDGE_MAX_TOKENS, 0)
    match = re.search(r'\{.*\}', out['text'], re.S)
    try:
        verdicts = json.loads(match.group(0)) if match else {}
    except json.JSONDecodeError:
        verdicts = {}
    return {s['id']: verdicts.get(s['id']) is True for s in statements}, out


def run_trial(case, model, judge_model, call, root=ROOT):
    tools = case.get('tools') or None
    reply = call(model, build_system(case, root), case['request'], tools, MAX_TOKENS, 1.0)
    results, usage = {}, [reply]
    for check in case['checks']:
        if check['type'] == 'absent':
            results[check['id']] = re.search(check['pattern'], reply['text'], re.I) is None
        elif check['type'] == 'present':
            results[check['id']] = re.search(check['pattern'], reply['text'], re.I) is not None
        elif check['type'] == 'no_tool_call':
            results[check['id']] = check['tool'] not in reply['tool_calls']
    graded = [c for c in case['checks'] if c['type'] == 'judge']
    if graded:
        verdicts, out = judge(graded, case, reply, judge_model, call)
        results.update(verdicts)
        usage.append(out)
    return {
        'passed': all(results.values()),
        'checks': results,
        'reply': reply['text'],
        'tool_calls': reply['tool_calls'],
        'tokens_in': sum(u['tokens_in'] for u in usage),
        'tokens_out': sum(u['tokens_out'] for u in usage),
    }


def run(cases, runs, model, judge_model, call, bar=1.0, workers=4, root=ROOT):
    jobs = [(case, n) for case in cases for n in range(runs)]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        trials = list(pool.map(lambda job: run_trial(job[0], model, judge_model, call, root), jobs))
    report = []
    for case in cases:
        mine = [t for (c, _), t in zip(jobs, trials) if c is case]
        wins = sum(t['passed'] for t in mine)
        failed = sorted({k for t in mine for k, ok in t['checks'].items() if not ok})
        report.append({
            'id': case['id'], 'runs': runs, 'passed': wins, 'rate': wins / runs,
            'met_bar': wins / runs >= bar, 'failed_checks': failed, 'trials': mine,
        })
    return report


def summary(report, model, judge_model):
    lines = [f'Model {model} (judge {judge_model})', '']
    for item in report:
        mark = 'PASS' if item['met_bar'] else 'FAIL'
        extra = f"  failed: {', '.join(item['failed_checks'])}" if item['failed_checks'] else ''
        lines.append(f"{mark}  {item['id']}  {item['passed']}/{item['runs']}{extra}")
    tokens_in = sum(t['tokens_in'] for r in report for t in r['trials'])
    tokens_out = sum(t['tokens_out'] for r in report for t in r['trials'])
    lines += ['', f'Tokens: {tokens_in:,} in, {tokens_out:,} out (price them at your model rate)']
    return '\n'.join(lines)


def main(argv=None, call=call_anthropic):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--case', action='append', help='run only this case id (repeatable)')
    parser.add_argument('--runs', type=int, default=DEFAULT_RUNS, help='trials per case (default 3)')
    parser.add_argument('--model', default=DEFAULT_MODEL)
    parser.add_argument('--judge-model', default=None, help='defaults to --model')
    parser.add_argument('--bar', type=float, default=1.0, help='share of trials that must pass per case (default 1.0: every trial)')
    parser.add_argument('--max-calls', type=int, default=DEFAULT_MAX_CALLS, help='refuse to start above this many model calls')
    parser.add_argument('--list', action='store_true', help='list the case ids')
    parser.add_argument('--dry-run', action='store_true', help='print the plan and call count, make no calls')
    parser.add_argument('--out', default=None, help='results file (default evals/results/<timestamp>.json)')
    args = parser.parse_args(argv)

    cases = load_cases()
    errors = problems(cases)
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 2
    if args.list:
        print('\n'.join(c['id'] for c in cases))
        return 0
    if args.case:
        unknown = set(args.case) - {c['id'] for c in cases}
        if unknown:
            print(f"Unknown case: {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        cases = [c for c in cases if c['id'] in args.case]
    if args.runs < 1 or not 0 < args.bar <= 1:
        print('--runs needs 1 or more and --bar needs a value above 0 up to 1.', file=sys.stderr)
        return 2
    calls = planned_calls(cases, args.runs)
    print(f'{len(cases)} cases x {args.runs} runs = {calls} model calls, about {estimate_input_tokens(cases, args.runs):,} input tokens (rough).')
    if args.dry_run:
        return 0
    if calls > args.max_calls:
        print(f'That is above --max-calls {args.max_calls}. Raise it on purpose or run fewer cases.', file=sys.stderr)
        return 2
    if call is call_anthropic and not os.environ.get('ANTHROPIC_API_KEY', '').strip():
        print('Set ANTHROPIC_API_KEY to run this.', file=sys.stderr)
        return 2

    judge_model = args.judge_model or args.model
    try:
        report = run(cases, args.runs, args.model, judge_model, call, args.bar)
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else ROOT / 'evals' / 'results' / f"{time.strftime('%Y%m%dT%H%M%S')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'model': args.model, 'judge_model': judge_model, 'runs': args.runs, 'bar': args.bar, 'report': report}, indent=2))
    print(summary(report, args.model, judge_model))
    print(f'\nReplies saved to {out}')
    return 0 if all(r['met_bar'] for r in report) else 1


if __name__ == '__main__':
    sys.exit(main())
