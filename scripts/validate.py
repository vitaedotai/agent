"""Offline schema and semantic checks; does not assert live client acceptance."""
import hashlib
import json
from pathlib import Path
import re
import sys
from jsonschema import validators, FormatChecker
from skill_format import validate_skill, validate_links

ROOT=Path(__file__).resolve().parents[1]
MANIFESTS=['plugin.json','mcp.json','.mcp.json','server.json','gemini-extension.json',
           '.claude-plugin/plugin.json','.claude-plugin/marketplace.json',
           '.cursor-plugin/plugin.json','.cursor-plugin/mcp.json',
           '.grok-plugin/plugin.json','.grok-plugin/marketplace.json',
           '.agents/plugins/marketplace.json']
ENDPOINT='https://mcp.vitae.ai/mcp'
SKILLS={'vitae','job-intake','hiring-scorecard','sourcing-strategy',
        'candidate-screening','candidate-outreach','interview-invitation',
        'interview-kit','candidate-presentation','recruitment-workflow'}

def walk(value):
    if isinstance(value,dict):
        for key,child in value.items():
            yield key,child
            yield from walk(child)
    elif isinstance(value,list):
        for child in value:
            yield from walk(child)

def validate(root=ROOT):
    errors=[]
    try:
        docs={name:json.loads((root/name).read_text()) for name in MANIFESTS}
        version=docs['plugin.json']['version']
        if not re.fullmatch(r'\d+\.\d+\.\d+',version):
            errors.append('invalid release version')
        for name,data in docs.items():
            for key,value in walk(data):
                if key=='version' and value!=version:
                    errors.append(f'{name}: release version drift')
                if key in {'skills','mcpServers','logo','composerIcon','contextFileName'}:
                    paths=value if isinstance(value,list) else [value]
                    for path in paths:
                        if not isinstance(path,str):
                            continue
                        target=(root/path).resolve()
                        if Path(path).is_absolute() or not target.is_relative_to(root.resolve()) or not target.exists():
                            errors.append(f'{name}: invalid component path {path}')
        for source in json.loads((root/'schemas/sources.json').read_text()):
            if hashlib.sha256((root/'schemas'/source['file']).read_bytes()).hexdigest()!=source['sha256']:
                errors.append(f"schema digest changed: {source['file']}")
        for name,schema_name in [('plugin.json','agent-plugin'),('mcp.json','agent-mcp'),('.cursor-plugin/plugin.json','cursor-plugin'),('server.json','mcp-server')]:
            schema=json.loads((root/f'schemas/{schema_name}.schema.json').read_text())
            cls=validators.validator_for(schema)
            cls.check_schema(schema)
            errors.extend(f'{name}: {error.json_path}: {error.message}' for error in cls(schema,format_checker=FormatChecker()).iter_errors(docs[name]))
        for name,transport in [('mcp.json','streamable-http'),('.mcp.json','http'),('.cursor-plugin/mcp.json','http'),('.grok-plugin/plugin.json','http')]:
            servers=docs[name]['mcpServers']
            if set(servers)!={'vitae'} or servers['vitae']!={'type':transport,'url':ENDPOINT}:
                errors.append(f'{name}: connector drift or unexpected credentials')
        if docs['gemini-extension.json']['mcpServers']!={'vitae':{'httpUrl':ENDPOINT}}:
            errors.append('Gemini connector drift')
        if docs['server.json']['remotes']!=[{'type':'streamable-http','url':ENDPOINT}]:
            errors.append('Registry connector drift')
        for name in ['plugin.json','.claude-plugin/plugin.json','.cursor-plugin/plugin.json','.grok-plugin/plugin.json','gemini-extension.json']:
            if docs[name]['name']!='vitae':
                errors.append(f'{name}: identity drift')
        for name in ['.claude-plugin/marketplace.json','.grok-plugin/marketplace.json']:
            entries=docs[name]['plugins']
            if len(entries)!=1 or entries[0]['name']!='vitae' or entries[0]['source']!='./':
                errors.append(f'{name}: invalid package source')
        codex=docs['.agents/plugins/marketplace.json']['plugins'][0]
        if codex['source']!={'source':'local','path':'./'} or codex['policy']!={'installation':'AVAILABLE','authentication':'ON_INSTALL'}:
            errors.append('invalid Codex source or authentication policy')
        catalog=json.loads((root/'catalog.json').read_text())
        entries=catalog['skills']
        names=[entry['name'] for entry in entries]
        found={str(p.relative_to(root)) for p in (root/'skills').glob('*/SKILL.md')}
        if (catalog['version']!=version or len(names)!=len(set(names))
            or set(names)!=SKILLS or found!={entry['path'] for entry in entries}):
            errors.append('skill catalog completeness or version drift')
        for entry in entries:
            if entry['path']!=f"skills/{entry['name']}/SKILL.md":
                errors.append('skill catalog path must match name')
                continue
            path=root/entry['path']
            skill_errors,front=validate_skill(path)
            errors.extend(skill_errors)
            if front.get('metadata',{}).get('version')!=version:
                errors.append(f'{path}: skill version drift')
            if front.get('description')!=entry['description']:
                errors.append(f'{path}: catalog description drift')
            if validate_links(path.parent):
                errors.append(f'{path}: individual skill has missing or escaping references')
        if docs['.grok-plugin/plugin.json']['skills']!=[f"./skills/{entry['name']}" for entry in entries]:
            errors.append('Grok skills do not match catalog')
        snapshot=json.loads((root/'skills/vitae/references/tools.json').read_text())
        tools=snapshot['tools']
        names=[tool['name'] for tool in tools]
        if snapshot['endpoint']!=ENDPOINT or not snapshot['retrievedAt'] or not tools or len(names)!=len(set(names)):
            errors.append('invalid public tool snapshot')
        for tool in tools:
            validators.validator_for(tool['inputSchema']).check_schema(tool['inputSchema'])
        errors.extend(validate_links(root))
    except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:
        errors.append(f'invalid package: {exc}')
    return errors

if __name__=='__main__':
    errors=validate()
    print('\n'.join(errors) if errors else 'Vitae package validation passed')
    sys.exit(bool(errors))
