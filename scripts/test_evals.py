import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import re
import tempfile
import unittest
from run_evals import (
    ROOT, build_system, estimate_input_tokens, judge, load_cases, main, planned_calls,
    problems, run, run_trial, skill_names,
)


def reply(text='', tools=()):
    return {'text': text, 'tool_calls': list(tools), 'tokens_in': 10, 'tokens_out': 5}


def fake(text='Draft only.', tools=(), verdicts=None):
    """A model stand-in: the judge call (temperature 0) answers `verdicts`, trials answer `text`."""
    seen = []

    def call(model, system, user, tools_arg, max_tokens, temperature):
        seen.append((model, temperature))
        if temperature == 0:
            return reply(json.dumps(verdicts if verdicts is not None else {}))
        return reply(text, tools)
    call.seen = seen
    return call


def all_true(case):
    return {c['id']: True for c in case['checks'] if c['type'] == 'judge'}


class CaseFileTests(unittest.TestCase):
    def test_cases_are_sound(self):
        self.assertEqual(problems(load_cases()), [])

    def test_every_documented_case_has_a_runnable_case(self):
        headings = re.findall(r'^## (.+)$', (ROOT / 'evals/recruiting.md').read_text(), re.M)
        titles = [c['title'] for c in load_cases()]
        for heading in headings:
            self.assertTrue(any(t.startswith(heading) for t in titles), heading)

    def test_unknown_skill_tool_and_pattern_are_caught(self):
        case = {'id': 'x', 'title': 't', 'skills': ['nope'], 'request': 'r', 'checks': [
            {'id': 'a', 'type': 'absent', 'pattern': '(', 'statement': 's'},
            {'id': 'b', 'type': 'no_tool_call', 'tool': 'gone', 'statement': 's'}]}
        errors = ' '.join(problems([case]))
        self.assertIn('unknown skill', errors)
        self.assertIn('bad pattern', errors)
        self.assertIn('not defined', errors)


class PromptTests(unittest.TestCase):
    def test_only_the_named_skill_is_installed(self):
        case = next(c for c in load_cases() if c['id'] == 'partial-skill-install')
        system = build_system(case)
        self.assertIn('<skill name="recruitment-workflow">', system)
        self.assertNotIn('<skill name="candidate-screening">', system)
        self.assertIn(case['context'], system)

    def test_all_installs_every_skill(self):
        case = next(c for c in load_cases() if c['id'] == 'vitae-skills-full-bundle')
        system = build_system(case)
        for name in skill_names():
            self.assertIn(f'<skill name="{name}">', system)
        self.assertEqual(len(skill_names()), 11)


class ScoringTests(unittest.TestCase):
    def case(self, cid):
        return next(c for c in load_cases() if c['id'] == cid)

    def test_clean_reply_passes(self):
        case = self.case('outreach-missing-facts')
        trial = run_trial(case, 'm', 'j', fake(verdicts=all_true(case)))
        self.assertTrue(trial['passed'])

    def test_pattern_check_fails_an_invented_salary(self):
        case = self.case('outreach-missing-facts')
        trial = run_trial(case, 'm', 'j', fake('Salary is £90,000.', verdicts=all_true(case)))
        self.assertFalse(trial['passed'])
        self.assertFalse(trial['checks']['no-salary-figure'])

    def test_a_forbidden_tool_call_fails(self):
        case = self.case('vitae-skills-alone')
        trial = run_trial(case, 'm', 'j', fake('Here.', tools=['search_skills'], verdicts=all_true(case)))
        self.assertFalse(trial['checks']['no-competency-lookup'])

    def test_a_false_verdict_fails_and_a_missing_one_counts_as_false(self):
        case = self.case('screening-missing-evidence')
        verdicts = all_true(case)
        verdicts['recruiter-decides'] = False
        del verdicts['asks-for-example']
        trial = run_trial(case, 'm', 'j', fake(verdicts=verdicts))
        self.assertEqual(sorted(k for k, ok in trial['checks'].items() if not ok),
                         ['asks-for-example', 'recruiter-decides'])

    def test_an_unreadable_judge_reply_fails_every_statement(self):
        case = self.case('screening-missing-evidence')
        graded = [c for c in case['checks'] if c['type'] == 'judge']
        verdicts, _ = judge(graded, case, reply('x'), 'j',
                            lambda *a: reply('I think it is fine.'))
        self.assertFalse(any(verdicts.values()))

    def test_the_judge_uses_its_own_model_at_temperature_zero(self):
        case = self.case('screening-missing-evidence')
        call = fake(verdicts=all_true(case))
        run_trial(case, 'writer', 'grader', call)
        self.assertEqual(call.seen, [('writer', 1.0), ('grader', 0)])

    def test_the_bar_decides_the_case(self):
        case = self.case('screening-missing-evidence')
        # Trials run one at a time here so the sequence of verdicts is predictable.
        passes = [True, True, False]
        sequence = []
        for ok in passes:
            sequence.append({k: ok for k in all_true(case)})
        pending = iter(sequence)

        def fixed(model, system, user, tools, max_tokens, temperature):
            return reply(json.dumps(next(pending))) if temperature == 0 else reply('ok')
        report = run([case], 3, 'm', 'j', fixed, bar=1.0, workers=1)
        self.assertEqual(report[0]['passed'], 2)
        self.assertFalse(report[0]['met_bar'])
        pending = iter(sequence)
        report = run([case], 3, 'm', 'j', fixed, bar=0.6, workers=1)
        self.assertTrue(report[0]['met_bar'])


class CommandTests(unittest.TestCase):
    def run_main(self, argv, call=None):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv, call) if call else main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_dry_run_counts_calls_and_makes_none(self):
        cases = load_cases()
        code, out, _ = self.run_main(['--dry-run', '--runs', '2'])
        self.assertEqual(code, 0)
        self.assertIn(f'{planned_calls(cases, 2)} model calls', out)
        self.assertGreater(estimate_input_tokens(cases, 2), 0)

    def test_it_refuses_to_start_above_the_call_cap(self):
        code, _, err = self.run_main(['--runs', '50', '--max-calls', '10'], call=fake())
        self.assertEqual(code, 2)
        self.assertIn('--max-calls', err)

    def test_unknown_case_is_a_usage_error(self):
        code, _, err = self.run_main(['--case', 'nope', '--dry-run'])
        self.assertEqual(code, 2)

    def test_exit_code_follows_the_bar_and_results_are_written(self):
        case = load_cases()[0]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'r.json'
            code, out, _ = self.run_main(
                ['--case', case['id'], '--runs', '1', '--out', str(path)], call=fake(verdicts=all_true(case)))
            self.assertEqual(code, 0)
            self.assertIn('PASS', out)
            self.assertEqual(json.loads(path.read_text())['report'][0]['id'], case['id'])
            code, out, _ = self.run_main(
                ['--case', case['id'], '--runs', '1', '--out', str(path)], call=fake(verdicts={}))
            self.assertEqual(code, 1)
            self.assertIn('FAIL', out)


if __name__ == '__main__':
    unittest.main()
