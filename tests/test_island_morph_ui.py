"""Exercise the real compact/dashboard handoff on a private Wayland display."""
from pathlib import Path
import os,json,tempfile,subprocess,time,signal,unittest
REQUIRED=['QUICKINTOSH_TEST_SOURCE','QUICKINTOSH_TEST_QS','QUICKINTOSH_TEST_PRIVATE_RUNTIME','QUICKINTOSH_TEST_PRIVATE_WAYLAND','QUICKINTOSH_TEST_PRIVATE_HYPRLAND']
@unittest.skipUnless(all(os.environ.get(k) for k in REQUIRED),'Built shell and private compositor required')
class IslandMorphUI(unittest.TestCase):
 def test_repeated_compact_expanded_handoff(self):
  runtime=Path(os.environ[REQUIRED[2]]).resolve();self.assertFalse(runtime.is_relative_to('/run/user'))
  with tempfile.TemporaryDirectory(prefix='qi-island-morph-') as tmp:
   root=Path(tmp);source=Path(os.environ[REQUIRED[0]])
   for e in source.iterdir():
    if e.name!='shell.qml':(root/e.name).symlink_to(e,target_is_directory=e.is_dir())
   for relative in ['rosa','rosa/overlays']:
    p=root/relative;original=p.resolve();p.unlink();p.mkdir()
    for e in original.iterdir():(p/e.name).symlink_to(e,target_is_directory=e.is_dir())
   p=root/'rosa/overlays/Island.qml';s=p.read_text();p.unlink();s=s.replace('    id: root','    id: root\n    property var qaWindow:null',1).replace('        IslandWindow {','        IslandWindow {\n            Component.onCompleted:root.qaWindow=this',1);p.write_text(s)
   p=root/'rosa/overlays/IslandWindow.qml';s=p.read_text();p.unlink();s=s.replace('    id: win','    id: win\n    property var qaDashboard:null\n    property int qaUncovered:0\n    FrameAnimation{running:win.visible;onTriggered:{if(win.presentationWanted && !win.blocked && !idleVisibility.fullyHidden && win.dashboardCover && stage.opacity<.01)win.qaUncovered++}}\n    readonly property var qaGeometry:({dashboard:qaDashboard ? qaDashboard.qaBody:null,uncovered:qaUncovered,kind:win.hub.kind,cover:dashboardCover,requested:dashboardRequested,compactOpacity:stage.opacity,morph:morph.value,visible:visible,opened:opened,stageCoverage:stage.opacity,pillOpacity:pill.opacity,bodyWidth:body.width,bodyHeight:body.height,mediaTargetWidth:wideSpan.target-24,mediaTargetHeight:wideTall.target-24,outerStroke:goo.stroke})',1);s=s.replace('        IslandDashboard {','        IslandDashboard {\n            Component.onCompleted:win.qaDashboard=this',1);p.write_text(s)
   p=root/'rosa/overlays/IslandDashboard.qml';s=p.read_text();p.unlink();p.write_text(s.replace('    id: panel','    id: panel\n    readonly property var qaBody:({page:page,collapsed:collapsed,geometryExpanded:geometryExpanded,expanded:expanded,bodyWidth:body.width,bodyHeight:body.height,targetWidth:capsuleWidth,targetHeight:capsuleHeight,windowWidth:width,parentWidth:body.parent.width})',1))
   (root/'shell.qml').write_text('''import QtQuick
import QtTest
import Quickshell
import Quickshell.Io
import qs.rosa.overlays
import qs.rosa.services
import qs.services as Native
ShellRoot{
 TestCase{id:pointer;name:'PrivatePointer';when:false}
 Island{id:hub;demoKind:'clock'}
 IpcHandler{target:'morphQA';function state():string{return JSON.stringify(hub.qaWindow?.qaGeometry || {})}function prepareEvent():void{IslandConfig.setStyle('autoWide',false);hub.showDemo('power');hub.demoWide=false;hub.qaWindow.collapseActivity()}function clearEvent():void{hub.qaWindow.forced=false;hub.endDemo();hub.dismiss();Native.ShelfState.activities=[];Native.ShelfState.items=[];hub.qaWindow.hushed=false}function liveActivity():void{Native.ShelfState.activities=[{id:'fixture-transfer',kind:'share',title:'KDE Connect',progress:.8,expires:Date.now()/1000+60}]}function trayReview():void{Native.ShelfState.items=[{name:'Review',path:'/tmp/qi-review-art.png'}]}function clickEvent():void{function named(item){if(item.objectName==='activity-compact')return item;for(const child of item.children || []){const found=named(child);if(found)return found}return null}const item=named(hub.qaWindow.contentItem);pointer.mouseClick(item,item.width/2,item.height/2,Qt.LeftButton)}function rightClick():void{const item=hub.qaWindow.contentItem;pointer.mouseClick(item,item.width/2,10,Qt.RightButton)}function expandIsland(on:bool):void{hub.qaWindow.dashboardRequested=on}function activity(kind:string,on:bool):void{hub.demoKind=kind;hub.demoWide=on;hub.qaWindow.forced=on}function reviewPage(index:int):void{hub.qaWindow.dashboardRequested=true;hub.qaWindow.qaDashboard.selectPage(index)}function reviewDetail(key:string):void{hub.qaWindow.dashboardRequested=true;hub.qaWindow.qaDashboard.detailWidget=key;hub.qaWindow.qaDashboard.selectPage(13)}function shotReview():void{IslandConfig.setStyle('autoWide',false);hub.demoKind='';hub.qaWindow.hushed=false;hub.shot('/tmp/qi-review-art.png')}function dashboardEnabled(on:bool):void{IslandConfig.setStyle("dashboardEnabled",on)}}
}''')
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_CACHE_HOME=tmp+'/.cache',XDG_STATE_HOME=tmp+'/.state',XDG_RUNTIME_DIR=str(runtime),WAYLAND_DISPLAY=os.environ[REQUIRED[3]],HYPRLAND_INSTANCE_SIGNATURE=os.environ[REQUIRED[4]],DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent');env.pop('DISPLAY',None)
   qs=os.environ[REQUIRED[1]]
   with (root/'log').open('w') as log:p=subprocess.Popen([qs,'-p',tmp],env=env,stdout=log,stderr=log,start_new_session=True)
   try:
    def ipc(*args):
     self.assertIsNone(p.poll(),(root/'log').read_text())
     r=subprocess.run([qs,'-p',tmp,'ipc','call','morphQA',*args],env=env,capture_output=True,text=True,timeout=5)
     self.assertEqual(r.returncode,0,r.stdout+r.stderr);return r.stdout
    def wait(predicate,timeout=5):
     end=time.monotonic()+timeout;last={}
     while time.monotonic()<end:
      try:
       last=json.loads(ipc('state'))
       if predicate(last):return last
      except (ValueError,KeyError,AssertionError,subprocess.TimeoutExpired):
       if p.poll() is not None:raise AssertionError((root/"log").read_text())
      time.sleep(.025)
     self.fail(str(last)+'\n'+(root/'log').read_text()[-3500:])
    wait(lambda s:s.get('visible') and s.get('compactOpacity',0)>.95,timeout=30)
    ipc('prepareEvent');wait(lambda s:not s.get('opened'));ipc('clickEvent');wait(lambda s:s.get('opened') and s.get('morph',0)>.9);ipc('clearEvent');wait(lambda s:not s.get('opened'))
    ipc('liveActivity');wait(lambda s:s.get('kind')=='share');ipc('clearEvent');wait(lambda s:s.get('kind')!='share')
    ipc('trayReview');wait(lambda s:s.get('kind')=='tray');ipc('clickEvent');wait(lambda s:s.get('cover') and s.get('requested'));ipc('expandIsland','false');ipc('clearEvent');wait(lambda s:not s.get('cover'))
    ipc('rightClick');wait(lambda s:s.get('cover') and s.get('requested'))
    time.sleep(.6);self.assertTrue(json.loads(ipc('state'))['requested'],'Right click shelf disappeared')
    ipc('rightClick');wait(lambda s:not s.get('cover') and not s.get('requested'))
    review=Path('/home/pg/.local/state/quickintosh/reviews/settings-tahoe-audit/transitions');review.mkdir(exist_ok=True)
    for index,(on,delay) in enumerate([(True,.06),(True,.3),(False,.03),(False,.16),(False,.4)]):
     ipc('expandIsland',str(on).lower());time.sleep(delay);subprocess.run(['grim','-l','1',str(review/f'frame-{index}.png')],env=env,check=True,timeout=15)
    for _ in range(20):
     ipc('expandIsland','true');wait(lambda s:s.get('cover') and s.get('compactOpacity',0)>.95)
     time.sleep(.08)
     ipc('expandIsland','false');wait(lambda s:not s.get('cover') and s.get('compactOpacity',0)>.95)
    # Reverse an unfinished morph repeatedly; the last request owns the surface.
    for _ in range(12):
     ipc('expandIsland','true');time.sleep(.03);ipc('expandIsland','false');time.sleep(.03)
    wait(lambda s:not s.get('cover') and s.get('compactOpacity',0)>.95)
    ipc('activity','media','true')
    for frame in range(6):
     state=json.loads(ipc('state'));self.assertAlmostEqual(state['bodyWidth'],state['mediaTargetWidth'],delta=1);self.assertAlmostEqual(state['bodyHeight'],state['mediaTargetHeight'],delta=1)
     self.assertEqual(state['outerStroke'],0)
     opening=Path('/home/pg/.local/state/quickintosh/reviews/player-final-polish');opening.mkdir(parents=True,exist_ok=True)
     subprocess.run(['grim','-l','1',str(opening/f'media-opening-{frame}.png')],env=env,check=True,timeout=15)
     time.sleep(.025)
    ipc('activity','media','false');wait(lambda s:not s.get('opened'))
    for kind in ['media','voice','timer']:
     ipc('activity',kind,'true');wait(lambda s:s.get('opened') and s.get('morph',0)>.9)
     ipc('expandIsland','true');wait(lambda s:s.get('cover') and s.get('compactOpacity',0)>.95)
     ipc('activity',kind,'false');ipc('expandIsland','false')
     wait(lambda s:not s.get('cover') and s.get('compactOpacity',0)>.95)
    ipc('dashboardEnabled','false');ipc('expandIsland','true')
    wait(lambda s:not s.get('cover') and not s.get('requested') and s.get('compactOpacity',0)>.95)
    ipc('dashboardEnabled','true')
    ipc('clearEvent');ipc('shotReview');wait(lambda s:s.get('kind')=='shot' and s.get('opened') and s.get('morph',0)>.9)
    shotReview=Path('/home/pg/.local/state/quickintosh/reviews/media-polish');shotReview.mkdir(exist_ok=True,parents=True)
    subprocess.run(['grim','-l','1',str(shotReview/'screenshot-expanded.png')],env=env,check=True,timeout=15)
    ipc('clearEvent');wait(lambda s:s.get('kind')!='shot' and not s.get('opened'))
    if os.environ.get('QI_MEDIA_GALLERY')=='1':
     for index in [0,1,2,3,4,5,6,7,8,9,10,11,12,14]:
      ipc('reviewPage',str(index));wait(lambda s:s.get('cover') and s.get('dashboard',{}).get('page')==index);time.sleep(.45)
      subprocess.run(['grim','-l','1',str(shotReview/f'tab-{index}.png')],env=env,check=True,timeout=15)
     for key in ['batteries','calendar','queue','notes','focus','performance','notifications','developer','teleprompter','vault','breather','terminal','transcribe','ring','selection','jobs','navigation','iconSettings']:
      ipc('reviewDetail',key);wait(lambda s:s.get('cover') and s.get('dashboard',{}).get('page')==13);time.sleep(.45)
      subprocess.run(['grim','-l','1',str(shotReview/f'widget-{key}.png')],env=env,check=True,timeout=15)
     ipc('expandIsland','false');wait(lambda s:not s.get('cover'))
    self.assertEqual(json.loads(ipc('state'))['uncovered'],0,'Both surfaces lost coverage during collapse')
    print('ISLAND_REAL_OWNER_20_MORPH_HANDOFFS_ZERO_UNCOVERED_CLOSE_FRAMES_OK')
   finally:
    if p.poll() is None:
     os.killpg(p.pid,signal.SIGTERM)
     try:p.wait(timeout=4)
     except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
if __name__=='__main__':unittest.main()
