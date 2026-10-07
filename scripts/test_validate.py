import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile
from validate import validate, ROOT
from package import package

class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)/'package'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('.git','.venv','node_modules','.worktrees','.tmp','__pycache__','build'))
    def tearDown(self):
        self.temp.cleanup()
    def test_valid_package(self):
        self.assertEqual(validate(self.root),[])
    def test_broken_reference(self):
        (self.root/'README.md').write_text('[missing](does-not-exist.md)')
        self.assertTrue(any('broken' in error for error in validate(self.root)))

    def test_connector_drift(self):
        path=self.root/'.mcp.json'
        data=json.loads(path.read_text())
        data['mcpServers']['vitae']['url']='https://example.com/mcp'
        path.write_text(json.dumps(data))
        self.assertTrue(any('connector drift' in error for error in validate(self.root)))
    def test_native_manifest_version_drift(self):
        path=self.root/'.grok-plugin/plugin.json'
        data=json.loads(path.read_text()); data['version']='9.9.9'
        path.write_text(json.dumps(data))
        self.assertTrue(any('version drift' in error for error in validate(self.root)))
    def test_schema_tampering(self):
        path=self.root/'schemas/agent-plugin.schema.json'
        path.write_text(path.read_text()+' ')
        self.assertTrue(any('digest' in error for error in validate(self.root)))

    def test_missing_bundled_recruiting_skill(self):
        (self.root/'skills/candidate-outreach/SKILL.md').unlink()
        self.assertTrue(any('catalog' in error for error in validate(self.root)))

    def test_individual_skill_cannot_require_sibling(self):
        path=self.root/'skills/candidate-outreach/SKILL.md'
        path.write_text(path.read_text()+'\n[other](../job-intake/SKILL.md)\n')
        self.assertTrue(any('individual skill' in error for error in validate(self.root)))

    def test_native_plugin_cannot_omit_bundled_skill(self):
        path=self.root/'.grok-plugin/plugin.json'
        data=json.loads(path.read_text()); data['skills'].pop()
        path.write_text(json.dumps(data))
        self.assertTrue(any('Grok skills' in error for error in validate(self.root)))

    def test_upload_bundles_skills_and_connector_without_environment_files(self):
        tracked=[str(p.relative_to(self.root)) for p in self.root.rglob('*') if p.is_file()]
        tracked.append('skills/vitae/.env')
        with patch('package.subprocess.check_output',return_value='\0'.join(tracked)):
            output=package(self.root)
        with ZipFile(output) as archive:
            names=archive.namelist()
            self.assertIn('plugin.json',names)
            self.assertIn('mcp.json',names)
            self.assertEqual(sum(name.endswith('/SKILL.md') for name in names),10)
            self.assertNotIn('skills/vitae/.env',names)
            self.assertFalse(any(name.startswith('scripts/') for name in names))

if __name__=="__main__":
    unittest.main()
