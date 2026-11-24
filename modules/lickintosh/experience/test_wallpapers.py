import importlib.util
from pathlib import Path
import tempfile
import unittest
from PIL import Image

spec = importlib.util.spec_from_file_location('wallpapers', Path(__file__).with_name('wallpapers.py'))
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)


class WallpaperTests(unittest.TestCase):
    def test_inventory_unicode_uppercase_and_hidden_directories(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '.hidden').mkdir()
            (root / '.hidden/skip.png').touch()
            for name in ['Foto #1 á.PNG', 'clip.MP4', 'skip.txt']:
                (root / name).touch()
            rows = backend.inventory(root)
            self.assertEqual(len(rows), 2)
            self.assertEqual(sum(item['video'] for item in rows), 1)

    def test_thumbnail_cache_is_bounded_and_invalidates_changed_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'wide.png'
            Image.new('RGB', (1600, 900), 'blue').save(source)
            original = source.read_bytes()
            row = backend.inventory(root)[0]
            cache = root / '.cache'
            first = backend.make_thumbnail(row, cache)
            self.assertEqual(source.read_bytes(), original)
            with Image.open(first) as image:
                self.assertLessEqual(image.width, 480)
                self.assertLessEqual(image.height, 320)
            stamp = first.stat().st_mtime_ns
            self.assertEqual(backend.make_thumbnail(row, cache).stat().st_mtime_ns, stamp)
            Image.new('RGB', (500, 500), 'red').save(source)
            second = backend.make_thumbnail(backend.inventory(root)[0], cache)
            self.assertNotEqual(first, second)


if __name__ == '__main__':
    unittest.main()
