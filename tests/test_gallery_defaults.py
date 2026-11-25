"""Verify a single image tile without removing resizing, and fresh defaults."""
from pathlib import Path
import os,tempfile,unittest
import test_qml_interface as qml
SOURCE=os.environ.get('QUICKINTOSH_TEST_SOURCE','')
@unittest.skipUnless(SOURCE and qml.QS,'Set QUICKINTOSH_TEST_SOURCE and QUICKINTOSH_TEST_QS')
class GalleryDefaults(unittest.TestCase):
 def test_gallery_and_clock_default_preserve_user_choice(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);source=Path(SOURCE)
   for folder,module,name in [('services','qs.services','WidgetRegistry'),('rosa/services','qs.rosa.services','IslandConfig')]:
    target=root/folder;target.mkdir(parents=True)
    text=(source/folder/(name+'.qml')).read_text().replace('Quickshell.env("HOME")',repr(directory))
    (target/(name+'.qml')).write_text(text)
    (target/'I18n.qml').write_text('pragma Singleton\nimport Quickshell\nSingleton{function tr(text){return text}function t(text){return text}}')
    (target/'qmldir').write_text('module '+module+'\nsingleton '+name+' '+name+'.qml\nsingleton I18n I18n.qml\n')
   (root/'.config/lickintosh/rosa').mkdir(parents=True)
   output=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
import qs.services
import qs.rosa.services as Rosa
Scope{
 Timer{interval:120;running:true;onTriggered:{
  if(WidgetRegistry.tilesOf('image').length!==1 || WidgetRegistry.tilesOf('personalclock').length!==3){Qt.exit(21);return}
  if(WidgetRegistry.galleryTypes.filter(t=>t.type==='clock').length!==1 || WidgetRegistry.galleryTypes.some(t=>t.type==='personalclock') || WidgetRegistry.tilesOf('clock').length!==5){Qt.exit(25);return}
  const sizes=WidgetRegistry.sizesOf('image','')
  for(const size of ['s','m','l','portrait','banner','wide','tall','square'])if(!sizes.includes(size)){Qt.exit(22);return}
  if(Rosa.IslandConfig.on('clock')){Qt.exit(23);return}
  Rosa.IslandConfig.style={srcClock:true}
  if(!Rosa.IslandConfig.on('clock')){Qt.exit(24);return}
  console.log('SINGLE_IMAGE_RESIZING_AND_OPT_IN_CLOCK_OK');Qt.quit()
 }}
}''')
   self.assertIn('SINGLE_IMAGE_RESIZING_AND_OPT_IN_CLOCK_OK',output)
if __name__=='__main__':unittest.main()
