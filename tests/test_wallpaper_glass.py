"""Render real crossfade slots and check pixels, including their empty layer."""
from pathlib import Path
import os,tempfile,unittest
import test_qml_interface as qml
SOURCE=os.environ.get('QUICKINTOSH_TEST_SOURCE','')
try:
 from PIL import Image
except ImportError:Image=None
@unittest.skipUnless(SOURCE and qml.QS and Image,'Set QUICKINTOSH_TEST_SOURCE/QUICKINTOSH_TEST_QS and install Pillow')
class WallpaperGlass(unittest.TestCase):
 def render(self,fixed):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);services=root/'services';services.mkdir()
   (services/'qmldir').write_text('module qs.services\nsingleton ShellConfig ShellConfig.qml\n')
   (services/'ShellConfig.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject{property var options:({wallpaper:{fit:"fill",backgroundColor:"#000000"}})}')
   (root/'GlassWallpaper.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject{function sourceUrl(path){return path ? "file://"+path:""}}')
   (root/'qmldir').write_text('singleton GlassWallpaper GlassWallpaper.qml\nWallpaperCrossfade WallpaperCrossfade.qml\nWallpaperSlot WallpaperSlot.qml\n')
   for name in ['WallpaperSlot.qml','WallpaperCrossfade.qml']:
    text=(Path(SOURCE)/'components/glass'/name).read_text()
    if not fixed:text=text.replace(';visible:slot.path!=="" && slot.imageStatus===Image.Ready','')
    if fixed and name=='WallpaperSlot.qml':text=text.replace('Rectangle{anchors.fill:parent;z:-1;color:', 'Rectangle{anchors.fill:parent;z:-1;visible:slot.path!=="" && slot.imageStatus===Image.Ready;color:')
    (root/name).write_text(text)
   Image.new('RGB',(80,80),'#e03050').save(root/'first.png');Image.new('RGB',(80,80),'#20b080').save(root/'second.png')
   output=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
Scope{
 FloatingWindow{implicitWidth:80;implicitHeight:80;color:"transparent"
  WallpaperCrossfade{id:wall;anchors.fill:parent;path:"'''+str(root/"first.png")+'''";duration:100}
 }
 Timer{interval:550;running:true;onTriggered:wall.grabToImage(result=>{result.saveToFile("'''+str(root/'initial.png')+'''");wall.path="'''+str(root/'second.png')+'''";next.start()})}
 Timer{id:next;interval:550;onTriggered:wall.grabToImage(result=>{result.saveToFile("'''+str(root/'changed.png')+'''");Qt.quit()})}
}''')
   return [Image.open(root/name).convert('RGB').getpixel((40,40)) for name in ['initial.png','changed.png']]
 def test_empty_slot_does_not_cover_the_wallpaper(self):
  before=self.render(False);after=self.render(True)
  self.assertEqual(before[0],(0,0,0),'The fixture must reproduce the black initial backdrop')
  self.assertEqual(after,[(224,48,80),(32,176,128)])
if __name__=='__main__':unittest.main()
