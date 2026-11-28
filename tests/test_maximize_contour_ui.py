"""Application-owned F/fullscreen requests in a disposable compositor."""
from pathlib import Path
import os,tempfile,json,subprocess,time,signal,unittest
NEEDED=['QUICKINTOSH_TEST_QS','QUICKINTOSH_TEST_PRIVATE_RUNTIME','QUICKINTOSH_TEST_PRIVATE_WAYLAND','QUICKINTOSH_TEST_PRIVATE_HYPRLAND']
@unittest.skipUnless(all(os.getenv(k) for k in NEEDED),'Private compositor required')
class MaximizeContour(unittest.TestCase):
 def test_maximize_bottom_pixels(self):
  with tempfile.TemporaryDirectory(prefix='qi-app-fullscreen-') as tmp:
   root=Path(tmp)
   (root/'shell.qml').write_text('''import QtQuick
import QtQuick.Window
import Quickshell.Wayland
import Quickshell
import Quickshell.Io
ShellRoot {
 Window{id:win;visible:true;title:'Application fullscreen QA';width:600;height:400;color:'#00ff00'
 Item{anchors.fill:parent;focus:true;Keys.onPressed:event=>{if(event.key===Qt.Key_F){win.visibility=win.visibility===Window.FullScreen ? Window.Windowed:Window.FullScreen;event.accepted=true}}}}
 PanelWindow{anchors{top:true;left:true;right:true}implicitHeight:28;exclusiveZone:28;color:'#000000';WlrLayershell.keyboardFocus:WlrKeyboardFocus.None}
 IpcHandler{target:'qa';function ready():string{return 'ready'}}
}''')
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_CACHE_HOME=tmp+'/.cache',XDG_STATE_HOME=tmp+'/.state',XDG_RUNTIME_DIR=os.environ[NEEDED[1]],WAYLAND_DISPLAY=os.environ[NEEDED[2]],HYPRLAND_INSTANCE_SIGNATURE=os.environ[NEEDED[3]])
   env.pop('DISPLAY',None)
   def ctl(*args):return subprocess.check_output(['hyprctl',*args],env=env,text=True,timeout=5)
   def window():return next((w for w in json.loads(ctl('-j','clients')) if w['title']=='Application fullscreen QA'),None)
   with (root/'log').open('w') as log:p=subprocess.Popen([os.environ[NEEDED[0]],'-p',tmp],env=env,stdout=log,stderr=log,start_new_session=True)
   try:
    deadline=time.monotonic()+20
    while not window():
     self.assertIsNone(p.poll(),(root/'log').read_text());self.assertLess(time.monotonic(),deadline);time.sleep(.1)
    address=window()['address'];ctl('eval','hl.dispatch(hl.dsp.focus({window="address:'+address+'"}))')
    config=(Path(__file__).resolve().parents[1]/'modules/hyprland-lua/hyprland.lua').read_text()
    helper=config[config.index('hl.workspace_rule({workspace="f[1]"'):config.index('configurableBind("ALT + F", toggleDecoratedZoom')]
    ctl('eval',helper+'\nqiZoomTest=toggleDecoratedZoom')
    ctl('eval','hl.config({general={border_size=0},decoration={rounding=30}});qiZoomTest()')
    time.sleep(.5)
    print('BASELINE',window(),flush=True)
    plugin=Path('/tmp/qi-maximize-plugin.path').read_text().strip()+'/lib/quickintosh-maximize-contour.so'
    subprocess.run(['grim','-l','1','/tmp/qi-maximize-before.png'],env=env,check=True,timeout=15)
    print('LOAD',ctl('plugin','load',plugin),flush=True);ctl('eval','hl.config({general={border_size=0},decoration={rounding=30}})');time.sleep(.5)
    from PIL import Image
    out=Path('/home/pg/.local/state/quickintosh/reviews/maximize-dock');out.mkdir(parents=True,exist_ok=True)
    subprocess.run(['grim','-l','1',str(out/'maximized.png')],env=env,check=True,timeout=15)
    image=Image.open(out/'maximized.png').convert('RGB');w=window();x,y=w['at'];width,height=w['size']
    print('CORNER_PIXELS',image.getpixel((x+1,y+1)),image.getpixel((x+1,y+height-2)),image.getpixel((x+width-2,y+height-2)))
    self.assertLess(image.getpixel((x+1,y+1))[1],100)
    self.assertGreater(image.getpixel((x+1,y+height-2))[1],230)
    self.assertGreater(image.getpixel((x+width-2,y+height-2))[1],230)
    self.assertEqual(w['fullscreen'],1)
    ctl('eval',helper+'\nqiZoomTest=toggleDecoratedZoom;qiZoomTest()');time.sleep(.4);self.assertEqual(window()['fullscreen'],0)
    ctl('plugin','unload',plugin)
    print('MAXIMIZED_SQUARE_BOTTOM_ROUND_TOP_OK')
   finally:
    os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
if __name__=='__main__':unittest.main()
