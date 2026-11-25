"""Offscreen behavior tests for media timing and desktop playback policy."""
from pathlib import Path
import os,tempfile,unittest
import test_qml_interface as qml
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(qml.QS,'Set QUICKINTOSH_TEST_QS for offscreen checks')
class CreativeWidgets(unittest.TestCase):
 def test_focus_policy_and_slideshow(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);services=root/'services';services.mkdir();types=root/'types';types.mkdir()
   source=ROOT/'modules/lickintosh/creative-widgets'
   (services/'CreativeMedia.qml').write_text((source/'CreativeMedia.qml').read_text())
   (types/'MediaPlaylist.qml').write_text((source/'MediaPlaylist.qml').read_text().replace('@MEDIA_PYTHON@',os.sys.executable))
   (types/'qmldir').write_text('module qs.types\nMediaPlaylist MediaPlaylist.qml\n')
   stubs={'DesktopFiles':'property bool desktopFocused:true','WidgetState':"property string galleryZone:'';property string editingId:''"}
   for name,body in stubs.items():(services/(name+'.qml')).write_text('pragma Singleton\nimport Quickshell\nSingleton{'+body+'}')
   (services/'qmldir').write_text('module qs.services\n'+''.join('singleton '+n+' '+n+'.qml\n' for n in ['CreativeMedia',*stubs]))
   rosa=root/'rosa/services';rosa.mkdir(parents=True)
   (rosa/'IslandBus.qml').write_text('pragma Singleton\nimport Quickshell\nSingleton{property bool locked:false}')
   (rosa/'qmldir').write_text('module qs.rosa.services\nsingleton IslandBus IslandBus.qml\n')
   output=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
import qs.services
import qs.types
import qs.rosa.services as Rosa
Scope{
 MediaPlaylist{id:list;widgetData:({id:'list',mediaFiles:['a.jpg','b.gif','c.mp4'],mediaInterval:15})}
 function check(ok,code){if(!ok)Qt.exit(code)}
 Timer{interval:80;running:true;onTriggered:{
  check(CreativeMedia.desktopActive,20)
  DesktopFiles.desktopFocused=false;check(!CreativeMedia.desktopActive,21)
  DesktopFiles.desktopFocused=true;WidgetState.galleryZone='desktop';check(!CreativeMedia.desktopActive,22)
  WidgetState.galleryZone='';WidgetState.editingId='editing';check(!CreativeMedia.desktopActive,23)
  WidgetState.editingId='';Rosa.IslandBus.locked=true;check(!CreativeMedia.desktopActive,24)
  Rosa.IslandBus.locked=false;check(CreativeMedia.desktopActive,25)
  check(list.path==='a.jpg' && list.interval===15000,26)
  list.next();check(list.path==='b.gif',27);list.next();check(list.video,28);list.next();check(list.path==='a.jpg',29)
  list.widgetData={id:'list',mediaFiles:['b.gif','a.jpg'],mediaInterval:900,mediaShuffle:true}
  check(list.path==='a.jpg' && list.interval===900000,30)
  for(let i=0;i<20;i++){const before=list.path;list.next();check(before!==list.path,31)}
  CreativeMedia.frame('preview','ignored');check(!CreativeMedia.frames.preview,32)
  CreativeMedia.poster('a','file:///a');check(CreativeMedia.posters.a==='file:///a',33)
  for(let i=0;i<180;i++)CreativeMedia.poster('image'+i,'file:///poster'+i)
  check(Object.keys(CreativeMedia.posters).length===160,34)
  console.log('CREATIVE_POLICY_PLAYLIST_OK');Qt.quit()
 }}
}''')
   self.assertIn('CREATIVE_POLICY_PLAYLIST_OK',output)
if __name__=='__main__':unittest.main()
