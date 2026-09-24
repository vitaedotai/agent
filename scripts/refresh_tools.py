"""Refresh public schemas only. No credentials and no tools/call requests."""
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.request import Request, urlopen

ENDPOINT='https://mcp.vitae.ai/mcp'
ROOT=Path(__file__).resolve().parents[1]

def discover():
    tools=[]
    cursor=None
    seen=set()
    while True:
        payload={'jsonrpc':'2.0','id':1,'method':'tools/list','params':{'cursor':cursor} if cursor else {}}
        request=Request(ENDPOINT,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'})
        with urlopen(request,timeout=30) as response:
            text=response.read().decode()
        if text.lstrip().startswith('{'):
            result=json.loads(text)
        else:
            events=[json.loads(line[5:].strip()) for line in text.splitlines() if line.startswith('data:')]
            result=next((event for event in events if event.get('id')==1),{})
        if 'error' in result or 'result' not in result:
            raise ValueError('Public MCP tool discovery failed; no snapshot written')
        tools.extend(result['result']['tools'])
        cursor=result['result'].get('nextCursor')
        if not cursor:
            break
        if cursor in seen:
            raise ValueError('Repeated discovery cursor; no snapshot written')
        seen.add(cursor)
    if not tools or len({t['name'] for t in tools})!=len(tools):
        raise ValueError('Empty or duplicate public tools; no snapshot written')
    return tools

def render(snapshot):
    rows=['# Public Vitae tools','',f"Retrieved: {snapshot['retrievedAt']} from unauthenticated `tools/list` at `{ENDPOINT}`.",'',
          'This is a schema snapshot, not customer data. Live schemas and account permissions take precedence. Read [tools.json](tools.json) only when you need exact parameters. Descriptions can mention tools that are not exposed; check actual availability.', '',
          'Read-only annotations do not describe every approval rule. Vitae enforces mutation permissions and approval requirements on the server. A pending approval is not a completed write.', '',
          '| Tool | Read-only hint | Purpose |','| --- | --- | --- |']
    for tool in snapshot['tools']:
        description=tool.get('description','').replace('|','\\|').replace('\n',' ')
        rows.append(f"| `{tool['name']}` | {'Yes' if tool.get('annotations',{}).get('readOnlyHint') else 'No'} | {description} |")
    return '\n'.join(rows)+'\n'

if __name__=='__main__':
    snapshot={'endpoint':ENDPOINT,'retrievedAt':datetime.now(timezone.utc).isoformat(),'tools':discover()}
    target=ROOT/'skills/vitae/references'
    target.mkdir(parents=True,exist_ok=True)
    (target/'tools.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    (target/'tools.md').write_text(render(snapshot))
    print(f"Refreshed {len(snapshot['tools'])} public tool schemas")
