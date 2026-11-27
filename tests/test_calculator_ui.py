"""Retained calculator window smoke/performance check on a private display only."""
from pathlib import Path
import os,json,shutil,subprocess,tempfile,time,signal,unittest
SOURCE=os.environ.get('QUICKINTOSH_TEST_SOURCE','');QS=os.environ.get('QUICKINTOSH_TEST_QS','')
RUNTIME=os.environ.get('QUICKINTOSH_TEST_PRIVATE_RUNTIME','');WAYLAND=os.environ.get('QUICKINTOSH_TEST_PRIVATE_WAYLAND','');SIGNATURE=os.environ.get('QUICKINTOSH_TEST_PRIVATE_HYPRLAND','')
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(all((SOURCE,QS,RUNTIME,WAYLAND,SIGNATURE)),'Built source and private compositor required')
class CalculatorUI(unittest.TestCase):
 def test_modes_arithmetic_and_repeated_mapping(self):
  self.assertNotEqual(Path(RUNTIME).resolve(),Path(os.environ.get('XDG_RUNTIME_DIR','/run/user/1000')).resolve())
  with tempfile.TemporaryDirectory(prefix='qi-calculator-test-') as directory:
   root=Path(directory);app=root/'app';app.mkdir();src=Path(SOURCE)
   for e in src.iterdir():
    if e.name!='shell.qml':(app/e.name).symlink_to(e,target_is_directory=e.is_dir())
   p=app/'components';original=p.resolve();p.unlink();p.mkdir()
   for e in original.iterdir():(p/e.name).symlink_to(e,target_is_directory=e.is_dir())
   p=app/'components/CalculatorApp.qml';text=p.read_text();p.unlink();p.write_text(text.replace(' id:app',' id:app\n readonly property var testWindow:window',1))
   (app/'shell.qml').write_text((ROOT/'tests/fixtures/calculator-ui.qml').read_text())
   env=dict(os.environ,HOME=directory,XDG_CONFIG_HOME=directory+'/.config',XDG_STATE_HOME=directory+'/.state',XDG_CACHE_HOME=directory+'/.cache',XDG_RUNTIME_DIR=RUNTIME,WAYLAND_DISPLAY=WAYLAND,HYPRLAND_INSTANCE_SIGNATURE=SIGNATURE)
   env.pop('DISPLAY',None);env.pop('DBUS_SESSION_BUS_ADDRESS',None)
   log=root/'app.log'
   with log.open('w') as output:p=subprocess.Popen([QS,'-p',str(app)],env=env,stdout=output,stderr=output,start_new_session=True)
   try:
    def ipc(*args):
     r=subprocess.run([QS,'-p',str(app),'ipc','call','calculatorTest',*args],env=env,capture_output=True,text=True,timeout=5)
     self.assertEqual(r.returncode,0,r.stderr+log.read_text());return r.stdout.strip()
    def status():return json.loads(ipc('status'))
    deadline=time.monotonic()+12
    while time.monotonic()<deadline:
     self.assertIsNone(p.poll(),log.read_text())
     try:
      if status()['ready']:break
     except (AssertionError,ValueError):pass
     time.sleep(.1)
    self.assertTrue(status()['ready']);ipc('begin');ipc('keys','239.5*0.4=')
    deadline=time.monotonic()+4
    while status()['value']!='95.8' and time.monotonic()<deadline:time.sleep(.02)
    self.assertEqual(status()['value'],'95.8');self.assertTrue(status()['visible'])
    for mode in range(6):
     ipc('page',str(mode));time.sleep(.2);s=status();self.assertFalse(s['error']);self.assertTrue(s['visible']);self.assertGreaterEqual(s['width'],330);self.assertGreaterEqual(s['height'],570)
    durations=[]
    for _ in range(12):
     start=time.perf_counter();ipc('closeCalc');self.assertFalse(status()['visible']);ipc('begin');self.assertTrue(status()['visible']);durations.append(time.perf_counter()-start)
    self.assertLess(max(durations),2,'Unexpected warm window mapping stall')
    print('CALCULATOR_UI_12_CYCLES_MAX_SECONDS',round(max(durations),4))
    text=log.read_text()
    for error in ['TypeError','ReferenceError','Failed to load configuration','has crashed']:self.assertNotIn(error,text)
   finally:
    if p.poll() is None:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=4)
if __name__=='__main__':unittest.main()
