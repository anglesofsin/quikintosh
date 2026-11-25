import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from app_catalog import AppCatalog

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'applications').mkdir()
    def tearDown(self):self.temp.cleanup()
    def desktop(self,name,extra=''):
        p=self.root/'applications'/(name+'.desktop')
        p.write_text('[Desktop Entry]\nType=Application\nName=Installed Editor\nExec=/bin/sh\nStartupWMClass=EditorWindow\n'+extra)
        return p
    def test_requires_registered_application_not_window_title(self):
        self.desktop('org.example.Editor');catalog=AppCatalog([self.root])
        self.assertEqual(catalog.sanitize([{'key':'Any random window','name':'Installed Editor'}]),[])
        result=catalog.sanitize([{'key':'EditorWindow','name':'Some document title'}])
        self.assertEqual(result[0]['name'],'Installed Editor');self.assertEqual(result[0]['key'],'EditorWindow')
        self.assertEqual(result[0]['desktopId'],'org.example.Editor.desktop')
    def test_hidden_helpers_and_missing_executables_are_excluded(self):
        for extra in ['Hidden=true\n','NoDisplay=true\n','TryExec=/definitely/not/installed\n']:
            with self.subTest(extra=extra):
                self.desktop('org.example.Editor',extra)
                self.assertEqual(AppCatalog([self.root]).sanitize([{'key':'EditorWindow'}]),[])
    def test_uninstalled_cached_app_is_removed(self):
        path=self.desktop('org.example.Editor');catalog=AppCatalog([self.root]);rows=catalog.sanitize([{'key':'EditorWindow'}]);path.unlink()
        self.assertEqual(catalog.sanitize(rows),[])
    def test_aliases_deduplicate_without_losing_window_identity(self):
        self.desktop('org.example.Editor');rows=AppCatalog([self.root]).sanitize([{'key':'EditorWindow'},{'key':'org.example.Editor.desktop'}])
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['key'],'EditorWindow')
    def test_user_hidden_override_does_not_reveal_system_entry(self):
        self.desktop('org.example.Editor','Hidden=true\n')
        system=self.root/'system';(system/'applications').mkdir(parents=True)
        (system/'applications/org.example.Editor.desktop').write_text('[Desktop Entry]\nType=Application\nName=Editor\nExec=/bin/sh\n')
        self.assertEqual(AppCatalog([self.root,system]).sanitize([{'key':'org.example.Editor'}]),[])

    def test_refresh_reuses_unchanged_desktop_parse_and_invalidates_edits(self):
        path=self.desktop('org.example.Editor');catalog=AppCatalog([self.root])
        import configparser
        original=configparser.ConfigParser.read
        with patch.object(configparser.ConfigParser,'read',autospec=True,side_effect=original) as read:
            catalog.refresh();first=read.call_count
            catalog.updated=-100;catalog.refresh();self.assertEqual(read.call_count,first)
            path.write_text(path.read_text().replace('Installed Editor','Changed Editor'))
            catalog.updated=-100;catalog.refresh();self.assertGreater(read.call_count,first)
            self.assertEqual(catalog.sanitize([{'key':'EditorWindow'}])[0]['name'],'Changed Editor')

if __name__=='__main__':unittest.main()
