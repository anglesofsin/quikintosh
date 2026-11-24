"""Content regressions for glyph extraction; run with Pillow/NumPy and rsvg."""
import os,sys,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
sys.argv=['test',os.environ.get('RSVG_CONVERT','rsvg-convert')]
import importlib.util
spec=importlib.util.spec_from_file_location('materials',Path(__file__).with_name('fast-renderer.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Materials(unittest.TestCase):
 def test_clip_definitions_survive(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'clipped.svg';p.write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><defs><clipPath id="cut"><rect width="256" height="256"/></clipPath></defs><rect width="64" height="64" fill="#202035"/><g transform="scale(.25)" clip-path="url(#cut)"><path fill="white" d="M128 24L152 96L232 128L152 152L128 232L104 152L24 128L104 104Z"/></g></svg>''')
   fields,_=m.prepare({'source':str(p)});self.assertGreater(float(fields['ink'].max()),.5);self.assertGreater(float((fields['ink']>.2).mean()),.05)
 def test_transparent_logo_is_not_empty(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'logo.png';im=Image.new('RGBA',(64,64));draw=ImageDraw.Draw(im);draw.ellipse((16,16,48,48),fill=(0,0,0,255));im.save(p)
   fields,_=m.prepare({'source':str(p)});self.assertGreater(float(fields['ink'].max()),.5)
 def test_provider_uses_installed_artwork(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'app.png';Image.new('RGBA',(16,16),'red').save(p);m.icon_catalog={'regression-app':p}
   self.assertEqual(m.path('image://icon/regression-app'),p)
   self.assertTrue(m.path('image://icon/'+str(p)).samefile(p))
if __name__=='__main__':unittest.main(argv=['test'])
