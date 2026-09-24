"""Portable skill and local-reference validation shared by this package's checks."""
from pathlib import Path
import re
import yaml

IGNORED={'.git','.venv','node_modules','.worktrees','.tmp','__pycache__','build'}
ALLOWED={'name','description','license','compatibility','metadata','allowed-tools'}

def files(root):
    for path in root.rglob('*'):
        if not set(path.relative_to(root).parts)&IGNORED and path.is_file():
            yield path

def validate_skill(path):
    errors=[]
    text=path.read_text()
    parts=text.split('---',2)
    try:
        front=yaml.safe_load(parts[1]) if len(parts)==3 and not parts[0].strip() else None
    except yaml.YAMLError:
        front=None
    if not isinstance(front,dict):
        return [f'{path}: missing or invalid YAML frontmatter'],{}
    name=front.get('name')
    if not isinstance(name,str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',name) or len(name)>64 or name!=path.parent.name:
        errors.append(f'{path}: invalid name or directory mismatch')
    description=front.get('description')
    if not isinstance(description,str) or not 1<=len(description)<=1024:
        errors.append(f'{path}: description must contain 1-1024 characters')
    if set(front)-ALLOWED:
        errors.append(f'{path}: unsupported portable frontmatter')
    metadata=front.get('metadata',{})
    if not isinstance(metadata,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in metadata.items()):
        errors.append(f'{path}: metadata must map strings to strings')
    if not parts[-1].strip() or re.search(r'\[TODO\b|\bTODO:|\bTBD\b',text):
        errors.append(f'{path}: unfinished skill')
    return errors,front

def validate_links(root):
    errors=[]
    for path in files(root):
        if path.is_symlink():
            errors.append(f'{path}: do not publish symlinks')
            continue
        if path.suffix!='.md':
            continue
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text()):
            if '://' in link or link.startswith(('mailto:','#')):
                continue
            target=(path.parent/link.split('#')[0]).resolve()
            if not target.is_relative_to(root.resolve()) or not target.exists():
                errors.append(f'{path}: broken or escaping link {link}')
    return errors
