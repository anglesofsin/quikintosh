"""Native island review in an explicitly private compositor; no host input."""
from pathlib import Path
import os,subprocess,tempfile,time,json,signal,shutil,re
import unittest
REQUIRED=['QUICKINTOSH_TEST_SOURCE','QUICKINTOSH_TEST_QS','QUICKINTOSH_TEST_PRIVATE_RUNTIME','QUICKINTOSH_TEST_PRIVATE_WAYLAND','QUICKINTOSH_TEST_PRIVATE_HYPRLAND','QUICKINTOSH_TEST_CONFIG','QUICKINTOSH_TEST_GLASS_PLUGIN']
@unittest.skipUnless(all(os.environ.get(k) for k in REQUIRED),'Built shell and private compositor required')
class IslandSurfaceUI(unittest.TestCase):
 def test_native_surface_navigation_edit_hold_and_collapse(self):
  source=Path(os.environ['QUICKINTOSH_TEST_SOURCE']);qs=os.environ['QUICKINTOSH_TEST_QS']
  runtime=os.environ['QUICKINTOSH_TEST_PRIVATE_RUNTIME'];assert not Path(runtime).resolve().is_relative_to('/run/user')
  out=Path(os.environ.get('QUICKINTOSH_REVIEW_DIR',tempfile.mkdtemp(prefix='qi-review-artifacts-')));out.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(prefix='qi-review-a-') as tmp:
   root=Path(tmp)
   for entry in source.iterdir():
    if entry.name!='shell.qml':(root/entry.name).symlink_to(entry,target_is_directory=entry.is_dir())
   def writable_dir(path):
    p=root/path;target=p.resolve();p.unlink();p.mkdir()
    for e in target.iterdir():(p/e.name).symlink_to(e,target_is_directory=e.is_dir())
   writable_dir('rosa');writable_dir('rosa/overlays')
   p=root/'rosa/overlays/IslandDashboard.qml';s=p.read_text();p.unlink();s=s.replace('    id: panel','    id: panel\n    readonly property var qaGeometry:({bodyWidth:body.width,bodyHeight:body.height,navY:navigation.y,navHeight:navigation.height,contentWidth:pageContent.width,contentHeight:pageContent.height,contentScale:pageContent.scale})',1);p.write_text(s)
   (root/'shell.qml').write_text('''import QtQuick
  import Quickshell
  import Quickshell.Io
  import Quickshell.Wayland
  import qs.services
  import qs.rosa.services
  import qs.rosa.overlays
  ShellRoot{
   PanelWindow{anchors{left:true;right:true;top:true;bottom:true}exclusionMode:ExclusionMode.Ignore;WlrLayershell.layer:WlrLayer.Background;color:'#292b36';Image{anchors.fill:parent;fillMode:Image.PreserveAspectCrop;source:Quickshell.shellPath('assets/wallpapers/daniel-leone.jpg')}}
   IslandDashboard{id:island;output:Quickshell.screens[0];expanded:false;onDismissed:expanded=false}
   IpcHandler{target:'reviewA';function expandIsland():string{island.expanded=true;return 'expanded='+island.expanded}function close():void{island.expanded=false}function page(n:int):void{island.selectPage(n)}function state():string{return JSON.stringify({expanded:island.expanded,page:island.page,hold:ShelfState.holdOpen,geometry:island.qaGeometry})}}
  }''')
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_CACHE_HOME=tmp+'/.cache',XDG_STATE_HOME=tmp+'/.state',XDG_RUNTIME_DIR=runtime,WAYLAND_DISPLAY=os.environ['QUICKINTOSH_TEST_PRIVATE_WAYLAND'],HYPRLAND_INSTANCE_SIGNATURE=os.environ['QUICKINTOSH_TEST_PRIVATE_HYPRLAND'],DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
   env.pop('DISPLAY',None)
   def ctl(*args):return subprocess.check_output(['hyprctl',*args],env=env,text=True,timeout=5)
   ctl('dismissnotify','-1')
   ctl('plugin','load',os.environ['QUICKINTOSH_TEST_GLASS_PLUGIN'])
   config=Path(os.environ['QUICKINTOSH_TEST_CONFIG']);config.write_text(config.read_text()+"\nif hl.plugin.hyprglass then hl.plugin.hyprglass.config({enabled=true,layers={enabled=true,force_live_resample=false}});hl.plugin.hyprglass.layer('quickintosh-island-dashboard',{preset='pomme',mask_mode='alpha',mask_threshold=0.001,live_resample=true}) end\n")
   ctl('reload');ctl('dismissnotify','-1')
   def ipc(*args):
    r=subprocess.run([qs,'-p',tmp,'ipc','call','reviewA',*args],env=env,capture_output=True,text=True,timeout=5)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr+(root/'log').read_text()[-4000:])
    return r.stdout
   def wait_state(predicate):
    deadline=time.monotonic()+5;last={}
    while time.monotonic()<deadline:
     last=json.loads(ipc('state'))
     if predicate(last):return last
     time.sleep(.04)
    raise AssertionError('UI did not settle: '+str(last))
   with (root/'log').open('w') as log:p=subprocess.Popen([qs,'-p',tmp],env=env,stdout=log,stderr=log,start_new_session=True)
   try:
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
     assert p.poll() is None,(root/'log').read_text()
     try:state=json.loads(ipc('state'));break
     except (RuntimeError,ValueError,subprocess.TimeoutExpired):time.sleep(.1)
    else:raise RuntimeError('No UI IPC')
    ctl('eval','hl.dispatch(hl.dsp.cursor.move({x=640,y=65}))')
    ipc('expandIsland')
    state=wait_state(lambda s:s['expanded'] and abs(s['geometry']['bodyHeight']-216)<.01)
    assert state['geometry']['contentScale']==1,state
    assert abs(state['geometry']['bodyHeight']-216)<.01,state
    recordingLog=(out/'recording.log').open('w')
    recorder=subprocess.Popen(['wf-recorder','-D','--no-dmabuf','-r','60','-c','libx264','-p','preset=ultrafast','-g','350,0 1220x650','-f',str(out/'transitions.mp4')],env=env,stdout=recordingLog,stderr=recordingLog)
    for page,name in [(0,'home'),(6,'tray'),(8,'widgets')]:
     ctl('eval','hl.dispatch(hl.dsp.cursor.move({x=640,y=65}))');ipc('page',str(page));wait_state(lambda s:s['page']==page and abs(s['geometry']['bodyHeight']-(560 if page==8 else 216))<.01);assert json.loads(ipc('state'))['expanded'],'Page change collapsed the island'
     subprocess.run(['grim',str(out/(name+'.png'))],env=env,check=True,timeout=5)
     (out/(name+'.json')).write_text(ipc('state'))
    ctl('eval','hl.dispatch(hl.dsp.cursor.move({x=960,y=850}))');time.sleep(.7)
    assert json.loads(ipc('state'))['expanded'],'Editor collapsed while being configured'
    ipc('page','0');wait_state(lambda s:not s['expanded'])
    ipc('expandIsland');time.sleep(.2);ipc('close')
    state=wait_state(lambda s:abs(s['geometry']['bodyWidth']-92)<.01 and abs(s['geometry']['bodyHeight']-26)<.01);assert abs(state['geometry']['bodyWidth']-92)<1 and abs(state['geometry']['bodyHeight']-26)<1,state
    recorder.send_signal(signal.SIGINT);recorder.wait(timeout=10);recordingLog.close()
    assert recorder.returncode==0,(out/'recording.log').read_text()
    stats=json.loads(ctl('-j','hyprglass','stats'))['monitors']
    draws=sum(m['layerGlassDraws'] for m in stats);misses=sum(m['layerCacheMisses'] for m in stats);deferred=sum(m['layerDeferredResamples'] for m in stats)
    assert draws>0 and sum(m['layerCacheHits'] for m in stats)==0 and misses+deferred>=draws,stats
    print('ISLAND_HOME_TRAY_WIDGETS_AND_EDITOR_HOLD_OK',state,'nativeDraws',draws,'cacheMisses',misses,'deferred',deferred)
   finally:
    if 'recorder' in locals() and recorder.poll() is None:
     recorder.send_signal(signal.SIGINT)
     try:recorder.wait(timeout=5)
     except subprocess.TimeoutExpired:
      recorder.terminate()
      try:recorder.wait(timeout=3)
      except subprocess.TimeoutExpired:recorder.kill();recorder.wait()
     recordingLog.close()
    if p.poll() is None:
     os.killpg(p.pid,signal.SIGTERM)
     try:p.wait(timeout=4)
     except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    shutil.copyfile(root/'log',out/'qml.log')

if __name__=='__main__':unittest.main()
