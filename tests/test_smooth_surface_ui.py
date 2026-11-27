"""Raster coverage and notch top geometry on a private Wayland compositor."""
from pathlib import Path
import os,tempfile,json,subprocess,time,signal,unittest
from PIL import Image
REQUIRED=['QUICKINTOSH_TEST_SOURCE','QUICKINTOSH_TEST_QS','QUICKINTOSH_TEST_PRIVATE_RUNTIME','QUICKINTOSH_TEST_PRIVATE_WAYLAND','QUICKINTOSH_TEST_PRIVATE_HYPRLAND']
@unittest.skipUnless(all(os.getenv(k) for k in REQUIRED),'Private compositor required')
class SmoothSurface(unittest.TestCase):
 def test_analytic_edge_and_notch(self):
  with tempfile.TemporaryDirectory(prefix='qi-edge-') as tmp:
   root=Path(tmp)
   for entry in Path(os.environ[REQUIRED[0]]).iterdir():
    if entry.name!='shell.qml':(root/entry.name).symlink_to(entry,target_is_directory=entry.is_dir())
   (root/'shell.qml').write_text('''import QtQuick
import QtQuick.Window
import Quickshell
import Quickshell.Io
import 'island-shelf'
ShellRoot{
 Window{id:win;visible:true;title:'Smooth surface QA';width:400;height:320;color:'#0030ff'
 ShelfRoundedSurface{id:surface;x:40;y:40;width:240;height:180;radius:52;color:'black';property bool notch:false;topLeftRadius:notch ? 0:radius;topRightRadius:notch ? 0:radius
 Rectangle{anchors.fill:parent;color:'white'}}}
 IpcHandler{target:'edge';function state():string{return JSON.stringify({x:win.x+surface.x,y:win.y+surface.y,width:surface.width,height:surface.height})}function notch(on:bool):void{surface.notch=on}}
}''')
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_CACHE_HOME=tmp+'/.cache',XDG_STATE_HOME=tmp+'/.state',XDG_RUNTIME_DIR=os.environ[REQUIRED[2]],WAYLAND_DISPLAY=os.environ[REQUIRED[3]],HYPRLAND_INSTANCE_SIGNATURE=os.environ[REQUIRED[4]])
   env.pop('DISPLAY',None);qs=os.environ[REQUIRED[1]]
   out=Path('/home/pg/.local/state/quickintosh/reviews/smooth-corners');out.mkdir(parents=True,exist_ok=True)
   with (out/'qml.log').open('w') as log:p=subprocess.Popen([qs,'-p',tmp],env=env,stdout=log,stderr=log,start_new_session=True)
   def ipc(*args):return subprocess.check_output([qs,'-p',tmp,'ipc','call','edge',*args],env=env,text=True,stderr=subprocess.DEVNULL,timeout=5)
   try:
    end=time.monotonic()+20
    while True:
     self.assertIsNone(p.poll(),(out/'qml.log').read_text())
     try:box=json.loads(ipc('state'));break
     except subprocess.CalledProcessError:self.assertLess(time.monotonic(),end);time.sleep(.15)
    time.sleep(.5)
    clients=json.loads(subprocess.check_output(['hyprctl','-j','clients'],env=env,text=True))
    client=next(w for w in clients if w['title']=='Smooth surface QA')
    box['x']=client['at'][0]+40;box['y']=client['at'][1]+40
    for notch in [False,True]:
     ipc('notch',str(notch).lower());time.sleep(.3)
     image=out/('notch.png' if notch else 'rounded.png')
     subprocess.run(['grim','-l','1',str(image)],env=env,check=True,timeout=15)
     im=Image.open(image).convert('RGB').crop((box['x'],box['y'],box['x']+box['width'],box['y']+box['height']))
     # White children must be clipped too; corners reveal the blue backdrop.
     self.assertGreater(im.getpixel((120,90))[0],245)
     self.assertLess(im.getpixel((0,179))[0],10)
     if notch:self.assertGreater(im.getpixel((0,0))[0],245)
     else:self.assertLess(im.getpixel((0,0))[0],10)
     partial=sum(1 for r,g,b in im.get_flattened_data() if 8<r<247)
     self.assertGreater(partial,25)
     im.resize((720,540)).save(out/('notch-detail.png' if notch else 'rounded-detail.png'))
     print('EDGE_COVERAGE',notch,partial)
   finally:
    if p.poll() is None:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
   log=(out/'qml.log').read_text()
   for error in ['ERROR','ReferenceError','TypeError','Binding loop']:self.assertNotIn(error,log)
if __name__=='__main__':unittest.main()
