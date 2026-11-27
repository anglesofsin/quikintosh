"""Native island material resamples on rendered frames in a private compositor."""
import os,subprocess,json,tempfile,time,signal,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQUIRED=['QUICKINTOSH_TEST_PRIVATE_RUNTIME','QUICKINTOSH_TEST_PRIVATE_WAYLAND','QUICKINTOSH_TEST_PRIVATE_HYPRLAND','QUICKINTOSH_TEST_QS','QUICKINTOSH_TEST_GLASS_PLUGIN']
@unittest.skipUnless(all(os.environ.get(k) for k in REQUIRED),'Private compositor and built plugin required')
class LiveGlass(unittest.TestCase):
 def test_visible_island_resamples_and_survives_reload(self):
  runtime=os.environ['QUICKINTOSH_TEST_PRIVATE_RUNTIME'];self.assertFalse(Path(runtime).resolve().is_relative_to(Path('/run/user')/str(os.getuid())))
  env=dict(os.environ,XDG_RUNTIME_DIR=runtime,WAYLAND_DISPLAY=os.environ['QUICKINTOSH_TEST_PRIVATE_WAYLAND'],HYPRLAND_INSTANCE_SIGNATURE=os.environ['QUICKINTOSH_TEST_PRIVATE_HYPRLAND'])
  def ctl(*args):
   r=subprocess.run(['hyprctl',*args],env=env,text=True,capture_output=True,timeout=10)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr);return r.stdout
  plugin=os.environ['QUICKINTOSH_TEST_GLASS_PLUGIN']
  self.assertNotIn('error',ctl('plugin','load',plugin).lower())
  config=Path(env['QUICKINTOSH_TEST_CONFIG'])
  config.write_text(config.read_text()+"\nif hl.plugin.hyprglass then hl.plugin.hyprglass.config({enabled=true,layers={enabled=true,force_live_resample=false}});hl.plugin.hyprglass.layer('quickintosh-island-dashboard',{mask_mode='alpha',mask_threshold=0.001,live_resample=true}) end\n")
  ctl('reload');self.assertFalse(ctl('configerrors').strip())
  with tempfile.TemporaryDirectory(prefix='qi-island-glass-') as tmp:
   root=Path(tmp);(root/'shell.qml').write_text('''import QtQuick
import Quickshell
import Quickshell.Wayland
ShellRoot{
 PanelWindow{anchors{top:true;bottom:true;left:true;right:true}exclusionMode:ExclusionMode.Ignore;WlrLayershell.layer:WlrLayer.Background;WlrLayershell.namespace:'qa-background';color:'red'}
 PanelWindow{anchors.top:true;implicitWidth:500;implicitHeight:200;exclusiveZone:-1;WlrLayershell.layer:WlrLayer.Overlay;WlrLayershell.namespace:'quickintosh-island-dashboard';color:'#33000000'
 Rectangle{width:2;height:2;color:'white';NumberAnimation on x{from:0;to:400;duration:2000;loops:Animation.Infinite}}
 }
}''')
   env.update(HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_CACHE_HOME=tmp+'/.cache',XDG_STATE_HOME=tmp+'/.state',DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
   with (root/'qs.log').open('w') as log:p=subprocess.Popen([os.environ['QUICKINTOSH_TEST_QS'],'-p',tmp],env=env,stdout=log,stderr=log,start_new_session=True)
   try:
    time.sleep(3)
    for iteration in range(2):
     self.assertIsNone(p.poll(),(root/'qs.log').read_text())
     ctl('hyprglass','stats','reset');time.sleep(1)
     stats=json.loads(ctl('-j','hyprglass','stats'));draws=sum(m['layerGlassDraws'] for m in stats['monitors']);misses=sum(m['layerCacheMisses'] for m in stats['monitors'])
     self.assertGreater(draws,0,stats);self.assertGreater(misses,0,stats);self.assertEqual(sum(m['layerCacheHits'] for m in stats['monitors']),0,stats);self.assertGreaterEqual(misses+sum(m['layerDeferredResamples'] for m in stats['monitors']),draws,stats)
     ctl('reload')
    ctl('plugin','unload',plugin);ctl('plugin','load',plugin);ctl('reload');time.sleep(.4)
    self.assertEqual(json.loads(ctl('-j','hyprglass','status'))['versionCheck'],'match')
    self.assertFalse(ctl('configerrors').strip());print('NATIVE_ISLAND_LIVE_SAMPLE_AND_PLUGIN_RELOAD_OK')
   finally:
    if p.poll() is None:
     os.killpg(p.pid,signal.SIGTERM)
     try:p.wait(timeout=4)
     except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
if __name__=='__main__':unittest.main()
