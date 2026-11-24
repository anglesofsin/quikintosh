import importlib.util
from pathlib import Path
import plistlib
import struct
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'modules/lickintosh/mac-apps/manager.py'
spec = importlib.util.spec_from_file_location('mac_apps', SOURCE)
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


class Applications(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, value in [('DATA', self.root / 'data'), ('APPLICATIONS', self.root / 'data/Applications'),
                            ('DESKTOPS', self.root / 'desktops'), ('PREFIX', self.root / 'prefix')]:
            patcher = patch.object(manager, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def bundle(self, name='Example.app', cpu=0x01000007):
        path = self.root / name
        (path / 'Contents/MacOS').mkdir(parents=True)
        (path / 'Contents/MacOS/example').write_bytes(b'\xcf\xfa\xed\xfe' + struct.pack('<I', cpu) + b'\0' * 24)
        with (path / 'Contents/Info.plist').open('wb') as stream:
            plistlib.dump({'CFBundleExecutable': 'example', 'CFBundleName': 'Example'}, stream)
        return path

    def test_install_publishes_copy_and_launcher_preserving_links(self):
        path = self.bundle('Example "Quoted" %.app')
        (path / 'Contents/alias').symlink_to('MacOS/example')
        installed = manager.install_app(path)
        self.assertTrue((installed / 'Contents/alias').is_symlink())
        entry = next(manager.DESKTOPS.glob('*.desktop')).read_text()
        self.assertIn('quickintosh-mac open "', entry)
        self.assertIn('%%.app', entry)
        self.assertIn('\\"Quoted\\"', entry)
        with self.assertRaises(ValueError):
            manager.install_app(path)

    def test_reject_apple_silicon_only(self):
        with self.assertRaisesRegex(ValueError, 'Apple Silicon'):
            manager.install_app(self.bundle(cpu=0x0100000c))
        self.assertFalse(manager.APPLICATIONS.exists())

    def test_reject_missing_executable(self):
        path = self.bundle()
        (path / 'Contents/MacOS/example').unlink()
        with self.assertRaisesRegex(ValueError, 'missing'):
            manager.metadata(path)

    def test_eject_protects_host_volumes(self):
        for path in ('/Volumes/SystemRoot', '/Volumes/DarlingEmulatedDrive', '/home/pg'):
            with self.assertRaises(ValueError):
                manager.eject(path)

    def test_remove_never_trashes_arbitrary_bundle(self):
        path = self.bundle()
        with patch('sys.argv', ['quickintosh-mac', 'remove', str(path)]), patch.object(manager.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'Only applications'):
                manager.main()
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
