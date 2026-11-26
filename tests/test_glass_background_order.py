"""Native glass cache and changing pixels; never runs against the host session."""
import json,os,signal,subprocess,tempfile,time,unittest
from pathlib import Path
try:
 from PIL import Image
except ImportError:
 Image=None
ROOT=Path(__file__).resolve().parents[1]
RUNTIME=os.environ.get('QUICKINTOSH_TEST_PRIVATE_RUNTIME','')
WAYLAND=os.environ.get('QUICKINTOSH_TEST_PRIVATE_WAYLAND','')
SIGNATURE=os.environ.get('QUICKINTOSH_TEST_PRIVATE_HYPRLAND','')
PLUGIN=os.environ.get('QUICKINTOSH_TEST_GLASS_PLUGIN','')
QS=os.environ.get('QUICKINTOSH_TEST_QS','')
@unittest.skipUnless(all((RUNTIME,WAYLAND,SIGNATURE,PLUGIN,QS,Image)),'Private compositor, glass plugin and Pillow required')
class BackgroundOrder(unittest.TestCase):
 def test_top_updates_reuse_cache_and_bottom_updates_change_pixels(self):
  self.assertNotEqual(Path(RUNTIME).resolve(),Path(os.environ.get('XDG_RUNTIME_DIR','/run/user/1000')).resolve())
  with tempfile.TemporaryDirectory(prefix='qi-glass-fixture-') as directory:
   root=Path(directory);(root/'shell.qml').write_text((ROOT/'tests/fixtures/glass-background-order.qml').read_text())
   env=dict(os.environ,HOME=directory,XDG_CONFIG_HOME=directory+'/.config',XDG_CACHE_HOME=directory+'/.cache',XDG_RUNTIME_DIR=RUNTIME,WAYLAND_DISPLAY=WAYLAND,HYPRLAND_INSTANCE_SIGNATURE=SIGNATURE)
   env.pop('DISPLAY',None);env.pop('DBUS_SESSION_BUS_ADDRESS',None)
   def ctl(*args):
    p=subprocess.run(['hyprctl',*args],env=env,capture_output=True,text=True,timeout=8)
    self.assertEqual(p.returncode,0,p.stdout+p.stderr);return p.stdout.strip()
   def stats():return json.loads(ctl('-j','hyprglass','stats'))['monitors'][0]
   loaded=False
   with (root/'runtime.log').open('w') as log:
    process=subprocess.Popen([QS,'-p',directory],env=env,stdout=log,stderr=log,start_new_session=True)
    try:
     time.sleep(2);self.assertEqual(ctl('plugin','load',PLUGIN),'ok');loaded=True
     ctl('eval','hl.plugin.hyprglass.config({enabled=true,default_preset="pomme",windows={background_cache=true,live_resample=true,live_resample_fps=0},layers={enabled=false}})')
     ctl('eval','hl.window_rule({name="qa-glass",match={title="^QI Glass Target$"},float=true,center=true,opacity="1.0 1.0",tag="+hyprglass_enabled"})')
     time.sleep(1);ctl('hyprglass','stats','reset');time.sleep(2);top=stats()
     self.assertGreater(top['windowGlassDraws'],0);self.assertGreater(top['windowCacheHits'],top['windowCacheMisses'])
     subprocess.run([QS,'-p',directory,'ipc','call','qa','animate','true'],env=env,capture_output=True,check=True,timeout=5)
     time.sleep(.4);ctl('hyprglass','stats','reset');colors=[]
     for _ in range(12):
      picture=root/'frame.png';subprocess.run(['grim',str(picture)],env=env,capture_output=True,check=True,timeout=5)
      with Image.open(picture) as image:colors.append(image.convert('RGB').getpixel((image.width//2,image.height//2)))
      time.sleep(.12)
     bottom=stats();self.assertGreater(bottom['windowCacheMisses'],0)
     self.assertGreater(max(c[0]-c[2] for c in colors)-min(c[0]-c[2] for c in colors),50)
     print('GLASS_ORDER_AND_LIVE_PIXELS',top['windowCacheHits'],top['windowCacheMisses'],bottom['windowCacheMisses'],colors)
    finally:
     if loaded:ctl('plugin','unload',PLUGIN)
     if process.poll() is None:
      os.killpg(process.pid,signal.SIGTERM)
      try:process.wait(timeout=3)
      except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
if __name__=='__main__':unittest.main()
