"""All generated bitmap artwork stays inside its logical icon box."""
from pathlib import Path
import ast,re,json,unittest
from PIL import Image
ROOT=Path(__file__).parents[1]/'modules/lickintosh/island-shelf'
class IconBounds(unittest.TestCase):
 def test_every_generated_asset_has_bounded_bitmap(self):
  text=(ROOT/'ShelfIcon.qml').read_text();mapping=ast.literal_eval(re.search(r'generated:\((\{.*?\})\)',text)[1]);bounds=json.loads(re.search(r'opticalBounds:(\{.*\})',text)[1])
  for asset in set(mapping.values()):
   with self.subTest(asset=asset):
    im=Image.open(ROOT/'icons/ai'/(asset+'-bounded.png'));im.load();im.close();box=bounds[asset]
    self.assertEqual(list(im.size),box[:2]);self.assertEqual(box[2:4],[0,0]);self.assertEqual(box[:2],box[4:6])
 def test_supplied_laptop_retains_translucent_screen(self):
  source=Image.open(ROOT/'icons/ai/laptop-user-bounded.png');im=source.convert('RGBA');source.close();self.assertEqual(im.getpixel((im.width//2,im.height//3))[:3],(255,255,255));self.assertLess(im.getpixel((im.width//2,im.height//3))[3],128)
if __name__=='__main__':unittest.main()
