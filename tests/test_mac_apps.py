import importlib.util
from pathlib import Path
import plistlib
import struct
import subprocess
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

    def test_image_falls_back_without_mount_tool(self):
        def extract(source, destination):
            destination.mkdir(parents=True)
            (destination / 'Example.app').mkdir()
        with patch.object(manager.shutil, 'which', return_value=None), \
             patch.object(manager, 'extract_image', side_effect=extract):
            with manager.disk_image(self.root / 'Example.dmg') as image:
                self.assertTrue((image / 'Example.app').is_dir())
                temporary = image.parent
            self.assertFalse(temporary.exists())

    def test_image_unmounts_even_when_install_fails(self):
        mounted = False
        commands = []
        def run(command, **kwargs):
            nonlocal mounted
            commands.append(command)
            mounted = '-u' not in command
            return subprocess.CompletedProcess(command, 0, '')
        with patch.object(manager.shutil, 'which', return_value='darling-dmg'), \
             patch.object(Path, 'is_mount', lambda _: mounted), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(manager.subprocess, 'run', side_effect=run):
            with self.assertRaisesRegex(ValueError, 'installation failure'):
                with manager.disk_image(self.root / 'Example.dmg') as image:
                    temporary = image.parent
                    raise ValueError('installation failure')
        self.assertFalse(temporary.exists())
        self.assertIn('ro', commands[0])
        self.assertIn('-u', commands[-1])

    def test_busy_mount_is_retained_without_recursive_deletion(self):
        mounted = False
        def run(command, **kwargs):
            nonlocal mounted
            if '-u' in command:
                raise subprocess.CalledProcessError(1, command)
            mounted = True
            return subprocess.CompletedProcess(command, 0, '')
        with patch.object(manager.shutil, 'which', return_value='darling-dmg'), \
             patch.object(Path, 'is_mount', lambda _: mounted), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(manager.subprocess, 'run', side_effect=run), \
             patch.object(manager.shutil, 'rmtree') as cleanup:
            with self.assertRaises(subprocess.CalledProcessError):
                with manager.disk_image(self.root / 'Example.dmg'):
                    pass
            cleanup.assert_not_called()


if __name__ == '__main__':
    unittest.main()
