import json
from pathlib import Path
import shutil
import tempfile
import unittest
from validate import validate, ROOT

class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)/'package'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('.git','.venv','node_modules','.worktrees','.tmp','__pycache__'))
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

if __name__=="__main__":
    unittest.main()
