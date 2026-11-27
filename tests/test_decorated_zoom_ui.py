"""Private-compositor regression for cross-process diagnostics and maximize mode."""
from pathlib import Path
import os,tempfile,shutil,json,subprocess,time,signal,unittest
ROOT=Path(__file__).resolve().parents[1]
REQUIRED=['QUICKINTOSH_TEST_SOURCE','QUICKINTOSH_TEST_QS','QUICKINTOSH_TEST_PRIVATE_RUNTIME','QUICKINTOSH_TEST_PRIVATE_WAYLAND','QUICKINTOSH_TEST_PRIVATE_HYPRLAND']
@unittest.skipUnless(all(os.environ.get(k) for k in REQUIRED),'Built source and private compositor required')
class WallpaperControls(unittest.TestCase):
 def test_diagnostics_bridge_and_maximize(self):
  runtime=os.environ['QUICKINTOSH_TEST_PRIVATE_RUNTIME'];self.assertNotEqual(Path(runtime).resolve(),Path('/run/user')/str(os.getuid()))
  with tempfile.TemporaryDirectory(prefix='qi-wallpaper-ui-') as tmp:
   root=Path(tmp);app=root/'app';app.mkdir();source=Path(os.environ['QUICKINTOSH_TEST_SOURCE'])
   for entry in source.iterdir():
    if entry.name not in ['shell.qml','settings.qml']:(app/entry.name).symlink_to(entry,target_is_directory=entry.is_dir())
   (app/'shell.qml').write_text('''import QtQuick
import Quickshell
import qs.services
ShellRoot{
 QtObject{id:fixture;function statistics(){return {width:1920,height:1080,fps:60,p95GapMs:17,stallsOver100ms:0,frameStorage:'gpu-texture',pixelFormat:'NV12'}}}
 Component.onCompleted:WallpaperVideo.addProbe('QA-fixture.mp4',fixture)
}''')
   (app/'settings.qml').write_text('''import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import qs.services
import "ui/topbar/statusarea/spotlight"
ShellRoot{
 FloatingWindow{visible:true;title:'Wallpaper Controls QA';implicitWidth:600;implicitHeight:500;color:'#202022';WallpaperDiagnostics{id:diagnostics;ipcPrefix:[Quickshell.env('QUICKINTOSH_TEST_QS'),'-p',Quickshell.shellDir,'ipc','call','wallpaperVideo'];anchors{left:parent.left;right:parent.right;top:parent.top;margins:20}enabledByUser:true}SpotlightCategoryGrid{id:appGrid;anchors.fill:parent;visible:false;items:Array.from({length:400},(_,index)=>({name:"Scroll fixture "+index,icon:"folder"}));categoryOrder:[];fontFamily:'SF Pro';fontFamilyMedium:'SF Pro';mode:'apps'}}
 IpcHandler{target:'wallpaperControls';function state():string{return JSON.stringify({rows:diagnostics.snapshot.length,received:diagnostics.received})}function stop():void{diagnostics.enabledByUser=false}
 function scroll():string{appGrid.visible=true;diagnostics.visible=false;let queue=[appGrid];while(queue.length){let c=queue.shift();if(typeof c.contentY==='number' && c.contentHeight>c.height && c.height>100){c.contentY=Math.min(c.contentHeight-c.height,c.contentY+120);return JSON.stringify({position:c.contentY,total:c.contentHeight,height:c.height})}for(let child of (c.children || []))queue.push(child)}return '{}'}}
 PanelWindow{anchors{left:true;right:true;top:true}implicitHeight:28;color:'#303033';exclusiveZone:28;WlrLayershell.keyboardFocus:WlrKeyboardFocus.None}
}''')
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_CACHE_HOME=tmp+'/.cache',XDG_STATE_HOME=tmp+'/.state',XDG_RUNTIME_DIR=runtime,WAYLAND_DISPLAY=os.environ['QUICKINTOSH_TEST_PRIVATE_WAYLAND'],HYPRLAND_INSTANCE_SIGNATURE=os.environ['QUICKINTOSH_TEST_PRIVATE_HYPRLAND'],QSG_RENDER_LOOP='basic',DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
   qs=os.environ['QUICKINTOSH_TEST_QS'];players=[];logs=[]
   def launch(config):
    log=root/(config+'.log');logs.append(log)
    with log.open('w') as f:players.append(subprocess.Popen([qs,'-p',str(app if config=='shell.qml' else app/config)],env=env,stdout=f,stderr=f,start_new_session=True))
   def ipc(config,target,action):return subprocess.check_output([qs,'-p',str(app if config=='shell.qml' else app/config),'ipc','call',target,action],env=env,text=True,stderr=subprocess.DEVNULL,timeout=5)
   def ctl(*args):return subprocess.check_output(['hyprctl',*args],env=env,text=True,timeout=5)
   def window():return next((w for w in json.loads(ctl('-j','clients')) if w.get('title')=='Wallpaper Controls QA'),None)
   try:
    launch('shell.qml');launch('settings.qml');deadline=time.monotonic()+25
    while True:
     self.assertTrue(all(p.poll() is None for p in players),'\n'.join(p.read_text() for p in logs))
     try:
      result=json.loads(ipc('settings.qml','wallpaperControls','state'))
      if result['rows']==1 and result['received'] and window():break
     except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
     self.assertLess(time.monotonic(),deadline,'\n'.join(p.read_text() for p in logs));time.sleep(.15)
    config=(ROOT/'modules/hyprland-lua/hyprland.lua').read_text()
    helper=config[config.index('local zoomedWindows = {}'):config.index('configurableBind("ALT + F", toggleDecoratedZoom')]
    self.assertNotIn('error',ctl('eval',helper+'\nqiZoomTest=toggleDecoratedZoom'))
    for floating in [True,False]:
     ctl('eval','hl.dispatch(hl.dsp.window.float({action="'+('enable' if floating else 'disable')+'"}))');time.sleep(.2)
     before=window()
     self.assertNotIn('error',ctl('eval','qiZoomTest()'));time.sleep(.3);w=window()
     self.assertEqual(w['fullscreen'],0);self.assertTrue(w['floating'])
     mon=next(m for m in json.loads(ctl('-j','monitors')) if m['id']==w['monitor']);reserved=mon['reserved']
     self.assertEqual(w['at'],[mon['x']+reserved[0],mon['y']+reserved[1]])
     self.assertEqual(w['size'],[round(mon['width']/mon['scale'])-reserved[0]-reserved[2],round(mon['height']/mon['scale'])-reserved[1]-reserved[3]])
     self.assertNotIn('error',ctl('eval','qiZoomTest()'));time.sleep(.3);after=window()
     self.assertEqual(after['floating'],floating);self.assertEqual(after['fullscreen'],0)
     if floating:self.assertEqual(after['at'],before['at']);self.assertEqual(after['size'],before['size'])
    ipc('settings.qml','wallpaperControls','stop');time.sleep(.4)
    self.assertFalse(json.loads(ipc('shell.qml','wallpaperVideo','state'))['measuring'])
    positions=[]
    for _ in range(15):
     row=json.loads(ipc('settings.qml','wallpaperControls','scroll'))
     if 'position' in row:positions.append(row['position'])
     time.sleep(.03)
    self.assertTrue(positions,'Launchpad scroll view was not created: '+str(row)+'\n'+'\n'.join(p.read_text() for p in logs))
    self.assertGreater(positions[-1],0)
    print('LAUNCHPAD_SCROLL_VIEW_OK',positions[-1])
    print('DECORATED_ZOOM_RESTORE_AND_DIAGNOSTICS_OK')
   finally:
    for p in reversed(players):
     if p.poll() is None:
      os.killpg(p.pid,signal.SIGTERM)
      try:p.wait(timeout=4)
      except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   text='\n'.join(p.read_text() for p in logs)
   for error in ['ReferenceError','TypeError','Failed to load configuration']:self.assertNotIn(error,text)
if __name__=='__main__':unittest.main()
