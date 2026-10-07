"""Build an OpenAI portable ZIP from public tracked package files."""
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def package(root=ROOT):
    manifest = json.loads((root / 'plugin.json').read_text())
    catalog = json.loads((root / 'catalog.json').read_text())
    tracked = subprocess.check_output(
        ['git', '-C', str(root), 'ls-files', '-z'], text=True
    ).split('\0')
    required = {'plugin.json', 'mcp.json', 'LICENSE', 'README.md', 'CONTRIBUTING.md'}
    files = sorted(required | {
        path for path in tracked
        if path.startswith(('skills/', 'assets/', 'docs/', 'evals/'))
        and not any(part.startswith('.env') for part in Path(path).parts)
    })
    for entry in catalog['skills']:
        if entry['path'] not in files:
            raise ValueError(f"Skill is not tracked: {entry['path']}")
    output = root / 'build' / f"vitae-{manifest['version']}.zip"
    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, 'w', compression=ZIP_DEFLATED) as archive:
        for name in files:
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (root / name).read_bytes())
    return output


if __name__ == '__main__':
    print(package())
