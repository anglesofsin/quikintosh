"""Optional real presentation test; requires a separate Wayland compositor."""
from pathlib import Path
import json,os,re,subprocess,tempfile,unittest
QS=os.environ.get('QUICKINTOSH_TEST_QS','')
RUNTIME=os.environ.get('QUICKINTOSH_TEST_PRIVATE_RUNTIME','')
WAYLAND=os.environ.get('QUICKINTOSH_TEST_PRIVATE_WAYLAND','')
@unittest.skipUnless(QS and RUNTIME and WAYLAND,'Private compositor and native QML plugin required')
class FramePacing(unittest.TestCase):
 def test_native_and_optional_cap(self):
  self.assertNotEqual(Path(RUNTIME).resolve(),Path(os.environ.get('XDG_RUNTIME_DIR','/run/user/'+str(os.getuid()))).resolve())
  rates={}
  for cap in [0,30]:
   with tempfile.TemporaryDirectory() as directory:
    Path(directory,'shell.qml').write_text('''import QtQuick
import Quickshell
import Quickintosh.Render
Scope{
 Component.onCompleted:{FramePacer.maximumFps=CAP;FramePacer.measuring=true}
 FloatingWindow{visible:true;implicitWidth:200;implicitHeight:100;Rectangle{width:20;height:20;color:'red';NumberAnimation on x{from:0;to:150;duration:1000;loops:Animation.Infinite}}}
 Timer{interval:4000;running:true;onTriggered:{console.log('FPS_RESULT',JSON.stringify(FramePacer.statistics()));Qt.quit()}}
}'''.replace('=CAP','='+str(cap)))
    env=dict(os.environ,HOME=directory,XDG_CONFIG_HOME=directory+'/.config',XDG_STATE_HOME=directory+'/.state',XDG_CACHE_HOME=directory+'/.cache',XDG_RUNTIME_DIR=RUNTIME,WAYLAND_DISPLAY=WAYLAND,QT_QPA_PLATFORM='wayland',HYPRLAND_INSTANCE_SIGNATURE='')
    for key in ['DISPLAY','DBUS_SESSION_BUS_ADDRESS']:env.pop(key,None)
    result=subprocess.run([QS,'-p',directory],env=env,capture_output=True,text=True,timeout=12)
    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    match=re.search(r'FPS_RESULT (\[.*\])',result.stdout+result.stderr);self.assertIsNotNone(match)
    active=[row for row in json.loads(match[1]) if row['active'] and row['samples']>20];self.assertTrue(active)
    rates[cap]=max(row['fps'] for row in active)
    if cap:self.assertLess(rates[cap],cap+3)
    print('Presented FPS',cap,active)
  self.assertGreater(rates[0],rates[30]*1.25,'Use a private output faster than 30 Hz')
if __name__=='__main__':unittest.main()
