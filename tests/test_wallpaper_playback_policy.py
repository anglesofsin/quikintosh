"""Visibility/fullscreen policy without touching the host compositor."""
from pathlib import Path
import os,tempfile,subprocess,shutil,unittest
ROOT=Path(__file__).resolve().parents[1]
QS=os.environ.get('QUICKINTOSH_TEST_QS') or shutil.which('qs')
@unittest.skipUnless(QS,'Quickshell required')
class PlaybackPolicy(unittest.TestCase):
 def test_workspace_fullscreen_maximized_and_power(self):
  with tempfile.TemporaryDirectory(prefix='qi-playback-policy-') as tmp:
   home=Path(tmp);shutil.copy2(ROOT/'modules/lickintosh/live-backdrop/playback-policy.js',home/'policy.js')
   (home/'shell.qml').write_text('''import QtQuick
import Quickshell
import "policy.js" as Policy
ShellRoot{
 Timer{interval:10;running:true;onTriggered:{
 const monitors=[{id:0,name:'A',activeWorkspace:{id:2},specialWorkspace:{id:-99}},{id:1,name:'B',activeWorkspace:{id:3}}];
 const opts={videoEnabled:true,pauseFullscreen:true,pauseMaximized:false};
 const c={monitor:0,workspace:{id:2},fullscreen:2,mapped:true};
 function expect(clients,wanted,options=opts,battery=false,game=false){const got=Policy.pauseReason(clients,monitors,'A',options,battery,game);if(got!==wanted)throw Error(JSON.stringify({wanted,got,clients}))}
 expect([c],'fullscreen');expect([Object.assign({},c,{workspace:{id:1}})],'');
 expect([Object.assign({},c,{monitor:1,workspace:{id:3}})],'');
 expect([Object.assign({},c,{workspace:{id:-99}})],'fullscreen');
 expect([Object.assign({},c,{workspace:{id:-98}})],'');
 expect([Object.assign({},c,{fullscreen:1})],'');
 expect([Object.assign({},c,{fullscreen:1})],'maximized',Object.assign({},opts,{pauseMaximized:true}));
 expect([Object.assign({},c,{fullscreen:3})],'fullscreen');
 expect([Object.assign({},c,{mapped:false})],'');expect([Object.assign({},c,{hidden:true})],'');
 expect([],'disabled',Object.assign({},opts,{videoEnabled:false}));
 expect([],'battery',Object.assign({},opts,{videoPauseBattery:true}),true);
 expect([],'game-mode',opts,false,true);
 console.log('PLAYBACK_POLICY_OK');Qt.quit()
 }}
}''')
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_CACHE_HOME=tmp+'/.cache',QT_QPA_PLATFORM='offscreen',DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
   for key in ['DISPLAY','WAYLAND_DISPLAY','HYPRLAND_INSTANCE_SIGNATURE']:env.pop(key,None)
   result=subprocess.run([QS,'-p',tmp],env=env,capture_output=True,text=True,timeout=15)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertIn('PLAYBACK_POLICY_OK',result.stdout+result.stderr)
if __name__=='__main__':unittest.main()
