"""Application-owned F/fullscreen requests in a disposable compositor."""
from pathlib import Path
import os,tempfile,json,subprocess,time,signal,unittest
NEEDED=['QUICKINTOSH_TEST_QS','QUICKINTOSH_TEST_PRIVATE_RUNTIME','QUICKINTOSH_TEST_PRIVATE_WAYLAND','QUICKINTOSH_TEST_PRIVATE_HYPRLAND']
@unittest.skipUnless(all(os.getenv(k) for k in NEEDED),'Private compositor required')
class AppFullscreen(unittest.TestCase):
 def test_application_f_after_maximize(self):
  with tempfile.TemporaryDirectory(prefix='qi-app-fullscreen-') as tmp:
   root=Path(tmp)
   (root/'shell.qml').write_text('''import QtQuick
import QtQuick.Window
import Quickshell
import Quickshell.Io
ShellRoot {
 Window{id:win;visible:true;title:'Application fullscreen QA';width:600;height:400;color:'#202022'
 Item{anchors.fill:parent;focus:true;Keys.onPressed:event=>{if(event.key===Qt.Key_F){win.visibility=win.visibility===Window.FullScreen ? Window.Windowed:Window.FullScreen;event.accepted=true}}}}
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
    for maximized in [False,True]:
     if maximized:ctl('eval','qiZoomTest()')
     ctl('eval','hl.dispatch(hl.dsp.send_shortcut({mods="",key="F",window="address:'+address+'"}))');time.sleep(.5)
     self.assertEqual(window()['fullscreen'],2,(root/'log').read_text())
     ctl('eval','hl.dispatch(hl.dsp.send_shortcut({mods="",key="F",window="address:'+address+'"}))');time.sleep(.5)
     self.assertIn(window()['fullscreen'],[0,1])
    print('APPLICATION_F_FULLSCREEN_AND_EXIT_OK')
   finally:
    os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
if __name__=='__main__':unittest.main()
