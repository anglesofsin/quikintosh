"""Native drag UI smoke, hover-only behavior and Transform placement."""
from pathlib import Path
import os,tempfile,json,subprocess,time,signal,unittest
KEYS=['QUICKINTOSH_TEST_SOURCE','QUICKINTOSH_TEST_QS','QUICKINTOSH_TEST_PRIVATE_RUNTIME','QUICKINTOSH_TEST_PRIVATE_WAYLAND','QUICKINTOSH_TEST_PRIVATE_HYPRLAND']
@unittest.skipUnless(all(os.getenv(k) for k in KEYS),'Private compositor required')
class DragSurfaces(unittest.TestCase):
 def test_drag_hover_and_transform_placement(self):
  with tempfile.TemporaryDirectory(prefix='qi-drag-surfaces-') as tmp:
   root=Path(tmp)
   for entry in Path(os.environ[KEYS[0]]).iterdir():
    if entry.name!='shell.qml':(root/entry.name).symlink_to(entry,target_is_directory=entry.is_dir())
   (root/'shell.qml').write_text('''import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
import qs.components
import qs.rosa.services
import qs.island_shelf
ShellRoot{
 ScreenEdges{}
 DragBasket{id:basket}
 TransformWindow{}
 Dock{id:dockRoot}
 IpcHandler{target:'dragQA';function state():string{return JSON.stringify({basket:basket.visible,transform:ShelfState.transformOpen})}function transform():void{ShelfState.transformOpen=true}}
 Component.onCompleted:{ShellConfig.options.edges.roundedCorners=true;ShelfState.basketPosition=Qt.point(600,400);ShelfState.basketOpen=true}
}'''.replace('import qs.island_shelf',"import 'island-shelf'\nimport qs.ui.dock"))
   # Instrument the actual surface without replacing its handlers or geometry.
   dock=root/'tahoedock';original=dock.resolve();dock.unlink();dock.mkdir()
   for entry in original.iterdir():(dock/entry.name).symlink_to(entry,target_is_directory=entry.is_dir())
   p=dock/'TahoeDockSurface.qml';s=p.read_text();p.unlink();s=s.replace("target:'dock'", "target:'dock'\n  function dragReview():void{root.trackDrag(plate,{x:plate.width/2,y:plate.height/2})}\n  function dragFinish():void{root.finishDragLens()}\n  function lens():string{return JSON.stringify({strength:root.lensStrength,zooms:root.lensLayout.zooms,drag:root.dragLensActive})}",1);p.write_text(s)
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_CACHE_HOME=tmp+'/.cache',XDG_STATE_HOME=tmp+'/.state',XDG_RUNTIME_DIR=os.environ[KEYS[2]],WAYLAND_DISPLAY=os.environ[KEYS[3]],HYPRLAND_INSTANCE_SIGNATURE=os.environ[KEYS[4]])
   env.pop('DISPLAY',None);qs=os.environ[KEYS[1]]
   out=Path('/home/pg/.local/state/quickintosh/reviews/maximize-dock');out.mkdir(parents=True,exist_ok=True)
   with (out/'drag.log').open('w') as log:p=subprocess.Popen([qs,'-p',tmp],env=env,stdout=log,stderr=log,start_new_session=True)
   def ipc(target,*args):return subprocess.check_output([qs,'-p',tmp,'ipc','call',target,*args],env=env,text=True,stderr=subprocess.DEVNULL,timeout=5)
   def ctl(*args):return subprocess.check_output(['hyprctl',*args],env=env,text=True,timeout=5)
   try:
    deadline=time.monotonic()+25
    while True:
     self.assertIsNone(p.poll(),(out/'drag.log').read_text())
     try:
      if json.loads(ipc('dragQA','state'))['basket']:break
     except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
     self.assertLess(time.monotonic(),deadline);time.sleep(.15)
    time.sleep(.5);ipc('dock','dragReview');time.sleep(.3);lens=json.loads(ipc('dock','lens'));self.assertTrue(lens['drag']);self.assertGreater(lens['strength'],.9);self.assertGreater(max(lens['zooms']),1)
    subprocess.run(['grim','-l','1',str(out/'drag-basket-dock.png')],env=env,check=True,timeout=15)
    self.assertFalse(json.loads(ipc('dragQA','state'))['transform'])
    ipc('dock','dragFinish');ipc('dragQA','transform');time.sleep(1.5)
    windows=json.loads(ctl('-j','clients'));w=next(w for w in windows if w['title']=='Quickintosh Transform');m=next(m for m in json.loads(ctl('-j','monitors')) if m['id']==w['monitor'])
    self.assertLessEqual(abs(w['at'][0]+w['size'][0]-(m['x']+m['width']/m['scale']-8)),2)
    self.assertLessEqual(abs(w['at'][1]+w['size'][1]-(m['y']+m['height']/m['scale']-8)),2)
    self.assertFalse(any('kdeconnect' in w['class'].lower() for w in windows))
    subprocess.run(['grim','-l','1',str(out/'transform-position.png')],env=env,check=True,timeout=15)
    print('DRAG_LENS_AND_TRANSFORM_BOTTOM_RIGHT_OK')
   finally:
    if p.poll() is None:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
   text=(out/'drag.log').read_text()
   for error in ['Failed to load configuration','ReferenceError','TypeError','Binding loop']:self.assertNotIn(error,text)
if __name__=='__main__':unittest.main()
