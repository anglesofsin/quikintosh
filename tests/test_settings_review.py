"""Run against an assembled source: QI_SETTINGS_SOURCE=/nix/store/… python3 tests/test_settings_review.py."""
import collections
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

SOURCE = os.environ.get('QI_SETTINGS_SOURCE')
REVIEW = Path(__file__).resolve().parents[1] / 'modules/lickintosh/settings-review/review.py'

@unittest.skipUnless(SOURCE, 'set QI_SETTINGS_SOURCE to an assembled source before settings-review')
class SettingsReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.source = Path(SOURCE)
        for relative in ['ui/settings/pages', 'ui/settings/widgets', 'settingsapp', 'assets/i18n']:
            shutil.copytree(cls.source / relative, cls.root / relative)
        for path in cls.root.rglob('*'):
            path.chmod(0o755 if path.is_dir() else 0o644)
        subprocess.run(['python3', str(REVIEW), str(cls.root)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_dock_controls_and_bindings_survive_regrouping(self):
        before = (self.source / 'ui/settings/pages/DockPage.qml').read_text()
        after = (self.root / 'ui/settings/pages/DockPage.qml').read_text()
        pattern = r'(?:ShellConfig\.options\.[\w.]+|WidgetState\.[\w.]+)'
        self.assertEqual(collections.Counter(re.findall(pattern, before)),
                         collections.Counter(re.findall(pattern, after)))
        for name in ['Size & Magnification', 'Folders & Trash', 'Recent Applications']:
            self.assertIn(name, after)

    def test_lock_preview_preserves_every_control(self):
        before = (self.source / 'ui/settings/pages/LockScreenPage.qml').read_text()
        after = (self.root / 'ui/settings/pages/LockScreenPage.qml').read_text()
        pattern = r'root\.cfg\.[\w.]+'
        self.assertEqual(collections.Counter(re.findall(pattern, before)),
                         collections.Counter(re.findall(pattern, after)))
        self.assertLess(after.index('title: I18n.tr("Aperçu")'),
                        after.index('title: I18n.tr("Apparence de l'))

    def test_capture_all_preferences_retained(self):
        before = (self.source / 'ui/settings/pages/CapturePage.qml').read_text()
        after = (self.root / 'ui/settings/pages/CapturePage.qml').read_text()
        keys = set(re.findall(r'ShellConfig\.options\.capture\.(\w+)', before))
        self.assertEqual(keys, set(re.findall(r'root\.cfg\.(\w+)', after)))
        self.assertEqual(after.count('SettingsPathRow{'), 2)

    def test_enum_dimming_has_three_choices(self):
        after = (self.root / 'ui/settings/pages/WidgetsPage.qml').read_text()
        self.assertIn("['auto','always','never'][index]", after)
        self.assertNotIn('checked:WidgetState.dimWidgets', after)

if __name__ == '__main__':
    unittest.main()
