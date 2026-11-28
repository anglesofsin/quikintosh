"""The native glass stage accepts the actual earlier banner replacement."""
from pathlib import Path
import re,unittest
ROOT=Path(__file__).parents[1]
class BannerAssemblyTests(unittest.TestCase):
 def test_current_banner_is_already_in_its_own_scope(self):
  source=(ROOT/'modules/lickintosh/notification-polish/NotifPopup.qml').read_text()
  self.assertRegex(source,r"GlassBackdrop\s*\{[^}]*\belement\s*:\s*['\"]notifpopup['\"]")
  self.assertIn('visible:!bannerGlass.nativeOverride',source)
 def test_integration_reuses_or_migrates_without_overwriting_banner(self):
  code=(ROOT/'modules/lickintosh/compositor/integrate.py').read_text()
  a=code.index("p='ui/topbar/statusarea/notifcenter/NotifPopup.qml'");b=code.index("write(p,s)",a)+len('write(p,s)')
  class File:
   def __init__(self,text):self.text=text
   def read_text(self):return self.text
  class Root:
   def __init__(self,text):self.file=File(text)
   def __truediv__(self,path):return self.file
  for original in [(ROOT/'modules/lickintosh/notification-polish/NotifPopup.qml').read_text(),"GlassBackdrop{element:'notifcenter'}"]:
   output={};env={'r':Root(original),'re':re,'write':lambda name,text:output.update(text=text)};exec(code[a:b],env)
   self.assertIn('notifpopup',output['text'])
   if 'bannerGlass' in original:self.assertEqual(original,output['text'])
  with self.assertRaises(ValueError):exec(code[a:b],{'r':Root('Item{}'),'re':re,'write':lambda *_:None})
if __name__=='__main__':unittest.main()
