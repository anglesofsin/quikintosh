"""Regression test for stale special-workspace focus; isolated compositor only."""
import json,os,shutil,signal,subprocess,tempfile,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUNTIME=os.environ.get('QUICKINTOSH_TEST_PRIVATE_RUNTIME','')
WAYLAND=os.environ.get('QUICKINTOSH_TEST_PRIVATE_WAYLAND','')
SIGNATURE=os.environ.get('QUICKINTOSH_TEST_PRIVATE_HYPRLAND','')
PLUGIN=os.environ.get('QUICKINTOSH_TEST_FOCUS_PLUGIN','')
QS=os.environ.get('QUICKINTOSH_TEST_QS','')
@unittest.skipUnless(all((RUNTIME,WAYLAND,SIGNATURE,PLUGIN,QS)),'Private compositor and matching focus plugin required')
class LayerFocus(unittest.TestCase):
 def test_panel_close_never_reopens_hidden_special(self):
  self.assertNotEqual(Path(RUNTIME).resolve(),Path(os.environ.get('XDG_RUNTIME_DIR','/run/user/1000')).resolve())
  with tempfile.TemporaryDirectory(prefix='qi-focus-fixture-') as directory:
   root=Path(directory);(root/'shell.qml').write_text((ROOT/'tests/fixtures/layer-focus.qml').read_text())
   env=dict(os.environ,HOME=directory,XDG_CONFIG_HOME=directory+'/.config',XDG_CACHE_HOME=directory+'/.cache',XDG_RUNTIME_DIR=RUNTIME,WAYLAND_DISPLAY=WAYLAND,HYPRLAND_INSTANCE_SIGNATURE=SIGNATURE)
   env.pop('DISPLAY',None);env.pop('DBUS_SESSION_BUS_ADDRESS',None)
   def ctl(*args):
    p=subprocess.run(['hyprctl',*args],env=env,capture_output=True,text=True,timeout=8)
    self.assertEqual(p.returncode,0,p.stdout+p.stderr);return p.stdout.strip()
   def monitor():return json.loads(ctl('monitors','-j'))[0]
   def hide():
    if monitor()['specialWorkspace'].get('name'):ctl('eval','hl.dispatch(hl.dsp.workspace.toggle_special("qa"))');time.sleep(.3)
   def show(value):
    p=subprocess.run([QS,'-p',directory,'ipc','call','qa','setPanel',str(value).lower()],env=env,capture_output=True,text=True,timeout=5)
    self.assertEqual(p.returncode,0,p.stdout+p.stderr)
   loaded=False
   with (root/'runtime.log').open('w') as log:
    p=subprocess.Popen([QS,'-p',directory],env=env,stdout=log,stderr=log,start_new_session=True)
    try:
     window=None
     for _ in range(60):
      window=next((c for c in json.loads(ctl('clients','-j')) if c['title']=='QI Hidden Call'),None)
      if window:break
      time.sleep(.1)
     self.assertIsNotNone(window)
     ctl('eval','hl.dispatch(hl.dsp.window.move({workspace="special:qa",follow=false}))');time.sleep(.3);hide()
     def attempt():
      ctl('eval','hl.dispatch(hl.dsp.focus({window="address:'+window['address']+'"}))');time.sleep(.2);hide()
      show(True);time.sleep(.25);show(False);time.sleep(.35)
      return monitor()['specialWorkspace'].get('name','')
     before=[attempt() for _ in range(3)];hide()
     self.assertTrue(any(before),'Fixture did not reproduce the unguarded compositor regression')
     self.assertEqual(ctl('plugin','load',PLUGIN),'ok');loaded=True
     after=[attempt() for _ in range(8)];hide();self.assertFalse(any(after),after)
     ctl('eval','hl.dispatch(hl.dsp.focus({window="address:'+window['address']+'"}))');time.sleep(.3)
     self.assertEqual(monitor()['specialWorkspace'].get('name'),'special:qa');hide()
     print('LAYER_FOCUS_REGRESSION',before,after)
    finally:
     if loaded:ctl('plugin','unload',PLUGIN)
     if p.poll() is None:
      os.killpg(p.pid,signal.SIGTERM)
      try:p.wait(timeout=3)
      except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
if __name__=='__main__':unittest.main()
