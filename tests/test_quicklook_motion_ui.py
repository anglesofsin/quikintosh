"""Actual Quick Look opening and reversible closing on a private compositor."""
from pathlib import Path
import os,tempfile,time,json,subprocess,signal,unittest
KEYS=['QUICKINTOSH_TEST_QS','QUICKINTOSH_TEST_PRIVATE_RUNTIME','QUICKINTOSH_TEST_PRIVATE_WAYLAND','QUICKINTOSH_TEST_PRIVATE_HYPRLAND']
@unittest.skipUnless(all(os.getenv(k) for k in KEYS),'Private compositor required')
class Motion(unittest.TestCase):
 def test_open_close_reverse(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   for e in Path('/tmp/qi-quicklook-review').iterdir():
    if e.name!='shell.qml':(root/e.name).symlink_to(e,target_is_directory=e.is_dir())
   (root/'shell.qml').write_text('''import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
import qs.quicklook
ShellRoot{
 QuickLookWindow{id:preview;property double requestedAt:0;property double firstFrame:0;FrameAnimation{running:preview.visible && preview.presented;onTriggered:if(preview.firstFrame===0)preview.firstFrame=Date.now()}}
 IpcHandler{target:'qa';function openPreview():void{preview.requestedAt=Date.now();preview.firstFrame=0;QuickLookState.enabled=true;QuickLookState.show(['/tmp/qi-review-art.png'],0,'desktop')}function closePreview():void{QuickLookState.close()}function state():string{return JSON.stringify({latency:preview.firstFrame ? preview.firstFrame-preview.requestedAt:-1,opened:QuickLookState.opened,enabled:QuickLookState.enabled,visible:preview.visible,presented:preview.presented,kind:preview.kind})}}
}''')
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_STATE_HOME=tmp+'/.state',XDG_CACHE_HOME=tmp+'/.cache',XDG_RUNTIME_DIR=os.environ[KEYS[1]],WAYLAND_DISPLAY=os.environ[KEYS[2]],HYPRLAND_INSTANCE_SIGNATURE=os.environ[KEYS[3]])
   env.pop('DISPLAY',None);qs=os.environ[KEYS[0]]
   with (root/'log').open('w') as log:p=subprocess.Popen([qs,'-p',tmp],env=env,stdout=log,stderr=log,start_new_session=True)
   def ipc(*args):return subprocess.check_output([qs,'-p',tmp,'ipc','call','qa',*args],env=env,text=True,stderr=subprocess.DEVNULL,timeout=5)
   try:
    end=time.monotonic()+30
    while True:
     self.assertIsNone(p.poll(),(root/'log').read_text())
     try:ipc('state');break
     except (subprocess.CalledProcessError,subprocess.TimeoutExpired):self.assertLess(time.monotonic(),end);time.sleep(.1)
    for _ in range(8):
     ipc('openPreview');time.sleep(.04);s=json.loads(ipc('state'));self.assertTrue(s['visible'],str(s)+'\n'+(root/'log').read_text());self.assertEqual(s['kind'],'image',str(s))
     ipc('closePreview');time.sleep(.02);ipc('openPreview');time.sleep(.14);self.assertTrue(json.loads(ipc('state'))['presented'])
     s=json.loads(ipc('state'));self.assertGreaterEqual(s['latency'],0);print('FIRST_FRAME_MS',s['latency']);self.assertLess(s['latency'],200) # Software-compositor regression bound; product target remains 100ms.
     ipc('closePreview');time.sleep(.2);self.assertFalse(json.loads(ipc('state'))['visible'])
    out=Path('/home/pg/.local/state/quickintosh/reviews/file-microinteractions');out.mkdir(parents=True,exist_ok=True);ipc('openPreview');time.sleep(.2);subprocess.run(['grim','-l','1',str(out/'quicklook.png')],env=env,check=True,timeout=15)
    print('QUICKLOOK_REOPEN_AND_REVERSE_OK')
   finally:
    if p.poll() is None:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
   for error in ['ReferenceError','TypeError','Failed to load configuration']:self.assertNotIn(error,(root/'log').read_text())
if __name__=='__main__':unittest.main()
