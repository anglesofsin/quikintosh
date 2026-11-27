"""Real special-workspace transitions; never operate on the user's compositor."""
from pathlib import Path
import json,os,signal,subprocess,tempfile,time,unittest
REQUIRED=['QUICKINTOSH_TEST_SOURCE','QUICKINTOSH_TEST_QS','QUICKINTOSH_TEST_PRIVATE_RUNTIME','QUICKINTOSH_TEST_PRIVATE_WAYLAND','QUICKINTOSH_TEST_PRIVATE_HYPRLAND']
@unittest.skipUnless(all(os.environ.get(k) for k in REQUIRED),'Built shell and private compositor required')
class DesktopFocusUI(unittest.TestCase):
 def test_thirty_special_workspace_roundtrips(self):
  runtime=Path(os.environ[REQUIRED[2]]).resolve()
  self.assertFalse(runtime.is_relative_to(Path('/run/user')/str(os.getuid())))
  with tempfile.TemporaryDirectory(prefix='qi-special-focus-') as tmp:
   root=Path(tmp);source=Path(os.environ[REQUIRED[0]])
   for entry in source.iterdir():
    if entry.name!='shell.qml':(root/entry.name).symlink_to(entry,target_is_directory=entry.is_dir())
   (root/'shell.qml').write_text('''import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import qs.services
import qs.ui.topbar.menubar.globalmenu
ShellRoot{
 id:qa;property int specialEvents:0
 Connections{target:Hyprland;function onRawEvent(event){if(event.name==='activespecialv2')qa.specialEvents++}}
 FloatingWindow{visible:true;title:'Special focus QA';implicitWidth:400;implicitHeight:300;color:'#303033'}
 IpcHandler{target:'focusQA';function state():string{return JSON.stringify({events:qa.specialEvents,desktop:GlobalMenuService.desktopMode,visible:GlobalMenuService.currentWindowVisible,window:GlobalMenuService.currentToplevel?.lastIpcObject,monitor:GlobalMenuService.focusedMonitor})}}
}''')
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_STATE_HOME=tmp+'/.state',XDG_CACHE_HOME=tmp+'/.cache',XDG_RUNTIME_DIR=str(runtime),WAYLAND_DISPLAY=os.environ[REQUIRED[3]],HYPRLAND_INSTANCE_SIGNATURE=os.environ[REQUIRED[4]],DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
   env.pop('DISPLAY',None)
   def ctl(*args):return subprocess.check_output(['hyprctl',*args],env=env,text=True,timeout=5)
   qs=os.environ[REQUIRED[1]]
   with (root/'log').open('w') as log:process=subprocess.Popen([qs,'-p',tmp],env=env,stdout=log,stderr=log,start_new_session=True)
   try:
    def state():
     self.assertIsNone(process.poll(),(root/'log').read_text())
     result=subprocess.run([qs,'-p',tmp,'ipc','call','focusQA','state'],env=env,capture_output=True,text=True,timeout=5)
     return json.loads(result.stdout)
    def await_state(desktop):
     end=time.monotonic()+3;last={}
     while time.monotonic()<end:
      try:
       last=state()
       if last['desktop']==desktop:return last
      except (ValueError,KeyError):pass
      time.sleep(.025)
     self.fail(f'Expected desktop={desktop}, got {last}\n'+(root/'log').read_text()[-2500:])
    end=time.monotonic()+10;client=None
    while time.monotonic()<end:
     clients=json.loads(ctl('-j','clients'));client=next((w for w in clients if w['title']=='Special focus QA'),None)
     if client:break
     self.assertIsNone(process.poll(),(root/'log').read_text());time.sleep(.1)
    self.assertIsNotNone(client)
    ctl('eval','hl.dispatch(hl.dsp.window.move({workspace="special:qa-focus",follow=false,window="address:'+client['address']+'"}))')
    await_state(True)
    for _ in range(30):
     ctl('eval','hl.dispatch(hl.dsp.workspace.toggle_special("qa-focus"))');await_state(False)
     ctl('eval','hl.dispatch(hl.dsp.workspace.toggle_special("qa-focus"))');await_state(True)
    self.assertGreaterEqual(state()['events'],60,'Missing real special-workspace socket events')
    print('SPECIAL_WORKSPACE_FINDER_30_REAL_ROUNDTRIPS_OK')
   finally:
    if process.poll() is None:
     os.killpg(process.pid,signal.SIGTERM)
     try:process.wait(timeout=4)
     except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
if __name__=='__main__':unittest.main()
