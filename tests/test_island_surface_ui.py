"""Native island review in an explicitly private compositor; no host input."""
from pathlib import Path
import os,subprocess,tempfile,time,json,signal,shutil,re
import unittest,sys
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
   p=root/'rosa/overlays/IslandDashboard.qml';s=p.read_text();p.unlink();s=s.replace('    readonly property var notices: {','    property var reviewNotices:[]\n    readonly property var notices: {\n        if(panel.reviewNotices.length)return panel.reviewNotices',1);s=s.replace('    id: panel','    id: panel\n    readonly property var qaGeometry:({bodyWidth:body.width,bodyHeight:body.height,navY:navigation.y,navHeight:navigation.height,contentWidth:pageContent.width,contentHeight:pageContent.height,contentScale:pageContent.scale})',1);p.write_text(s)
   (root/'shell.qml').write_text('''import QtQuick
  import QtTest
  import Quickshell
  import Quickshell.Io
  import Quickshell.Wayland
  import qs.services
  import qs.rosa.services
  import qs.rosa.overlays
  import qs.ui.topbar.statusarea.notifcenter
  import "island-shelf"
  ShellRoot{
   TestCase{id:pointer;name:"PrivateMenuPointer";when:false}
   function named(item,name){if(item.objectName===name)return item;for(const child of item.children || []){const found=named(child,name);if(found)return found}return null}
   function visualNames(item){if(!item)return [];let names=item.objectName ? [item.objectName]:[];for(const child of item.children || [])names=names.concat(visualNames(child));return names}
   property bool reviewInitialised:false
   function populateReview(){
    ShellConfig.options.wallpaper.path=Quickshell.env("QUICKINTOSH_REVIEW_BACKGROUND").replace("file://","");ShellConfig.options.wallpaper.pathLight="";ShellConfig.options.wallpaper.pathDark="";
    if(!reviewInitialised){reviewInitialised=true;ShelfState.add(JSON.parse(Quickshell.env('QA_TRAY_FILES')))}
    NotesState.notes=[{id:'review1',text:'Launch day\\nFinish the release notes.'},{id:'review2',text:'Podcast ideas\\nA conversation about creativity.'}];

    CalendarState.available=true;CalendarState.events=[{time:'10:00–10:45',title:'Design sync'},{time:'13:30–14:30',title:'Lunch with Sam'},{time:'15:00–16:00',title:'Launch review'}];
    WeatherState.available=true;WeatherState.city='Cupertino';WeatherState.tempC=21;WeatherState.description='Mostly sunny';WeatherState.weatherCode=0;WeatherState.forecast=[0,1,2,3,4,5,6].map(i=>({date:new Date(Date.UTC(2026,10,27+i)).toISOString().slice(0,10),code:[0,1,2,61,63,95,0][i],tempMax:25-i,tempMin:14-i}));WeatherState.hourly=[{time:'2026-11-27T10:00',temp:21,code:0},{time:'2026-11-27T11:00',temp:22,code:0},{time:'2026-11-27T12:00',temp:24,code:2},{time:'2026-11-27T13:00',temp:25,code:0}];IslandConfig.setStyle('dashboardWeatherLocation',true);
   }
   PanelWindow{anchors{left:true;right:true;top:true;bottom:true}exclusionMode:ExclusionMode.Ignore;WlrLayershell.layer:WlrLayer.Background;color:'#292b36';Image{anchors.fill:parent;fillMode:Image.PreserveAspectCrop;source:Quickshell.env('QUICKINTOSH_REVIEW_BACKGROUND') || Quickshell.shellPath('assets/wallpapers/daniel-leone.jpg')}}
   QtObject{id:replyNotice;property string appName:'Messages';property string summary:'Alex Morgan';property string body:'Look at this sunset! Dinner at seven?';property string appIcon:'mail-message';property string image:Quickshell.env('QA_MEDIA_ART');property bool hasInlineReply:true;property string inlineReplyPlaceholder:'Reply';property var actions:[];property string received:'';function sendInlineReply(text){received=text}}
   QtObject{id:bannerNotice;property string appName:'Quickintosh';property string summary:'Notification material';property string body:'A translucent banner over the desktop, using the same glass material as the shell.';property string appIcon:'preferences-system';property var actions:[];function dismiss(){}}
   NotifPopup{}
   DragBasket{id:basketPanel}
   FloatingTray{}
   TransformWindow{}
   FloatingMusic{id:floatingReview}
   PanelWindow{id:playerReview;visible:false;implicitWidth:760;implicitHeight:540;anchors{top:true;left:true}exclusionMode:ExclusionMode.Ignore;color:'#171719';WlrLayershell.namespace:'qi-player-review'
    property bool portrait:false
    ShelfMedia{id:reviewPlayer;anchors.fill:parent;anchors.margins:22;portrait:playerReview.portrait;showPopout:false}
   }
   IslandDashboard{id:island;reviewNotices:[replyNotice];output:Quickshell.screens[0];expanded:false;onDismissed:expanded=false}
   IpcHandler{target:'reviewA';function banner(on:bool):void{ShellConfig.options.wallpaper.path=Quickshell.env('QUICKINTOSH_REVIEW_BACKGROUND').replace('file://','');ShellConfig.options.wallpaper.pathDark='';ShellConfig.options.wallpaper.pathLight='';SettingsPreferences.notifications.duration=60000;if(on)NotifService.popupModel.insert(0,{notifObj:bannerNotice});else NotifService.removePopup(bannerNotice,true)}function tabBench():string{const samples=[];for(let pass=0;pass<4;pass++)for(let n=0;n<14;n++){const start=Date.now();island.selectPage(n);samples.push({page:n,ms:Date.now()-start,immediate:island.page===n})}return JSON.stringify(samples)}function expandIsland():string{island.expanded=true;return 'expanded='+island.expanded}function replyReview():string{function find(item){if(item.objectName==='notification-reply')return item;for(const child of item.children || []){const match=find(child);if(match)return match}return null}const field=find(island.contentItem);if(!field)return 'missing';field.text='Count me in! See you at 7.';field.accepted();return replyNotice.received}function basketDragState():string{const target=named(basketPanel.contentItem,'basket-target-transform');return JSON.stringify({contains:target?.containsDrag,x:target?.x,y:target?.y,hasUrls:target?.drag?.hasUrls,keys:target?.drag?.keys})}function nativeDragState():string{const item=named(island.contentItem,'tray-item-0');return JSON.stringify({pressed:item?.pressed,dragging:item?.drag.active,enabled:item?.enabled,visible:item?.visible})}function nativeTrayPoint():string{const item=named(island.contentItem,'tray-item-0');if(!item)return '[]';const p=item.mapToItem(island.contentItem,item.width/2,item.height/2);return JSON.stringify([Math.round((island.output.width-island.width)/2+p.x),Math.round(island.margins.top+p.y)])}function menuOpen():void{const button=named(island.contentItem,'home-options');pointer.mouseClick(button,button.width/2,button.height/2,Qt.LeftButton)}function reorderReview():string{const before=[1,2,3,4].map(i=>IslandConfig.s('shelfSlot'+i));const from=named(island.contentItem,'reorder-0');const to=named(island.contentItem,'home-slot-1');const point=to.mapToItem(from,to.width/2,20);pointer.mousePress(from,from.width/2,from.height/2,Qt.LeftButton);pointer.mouseMove(from,from.width/2+20,from.height/2,60);pointer.mouseMove(from,point.x,point.y,100);pointer.mouseRelease(from,point.x,point.y,Qt.LeftButton);return JSON.stringify({before:before,after:[1,2,3,4].map(i=>IslandConfig.s('shelfSlot'+i))})}function menuHover():void{const menu=named(island.contentItem,'shelf-home-editor').contextMenu;const item=menu.itemAt(0);pointer.mouseMove(item,item.width/2,item.height/2)}function menuSelect():void{const menu=named(island.contentItem,'shelf-home-editor').contextMenu;const item=menu.itemAt(0);pointer.mouseClick(item,item.width/2,item.height/2,Qt.LeftButton)}function menuState():string{const menu=named(island.contentItem,'shelf-home-editor')?.contextMenu;const button=named(island.contentItem,'home-options');return JSON.stringify({visible:menu?.visible,width:menu?.width,height:menu?.height,glassReady:menu?.glassReady,material:menu?.materialState,x:menu?.x,y:menu?.y,parentName:menu?.parent?.objectName,editing:ShelfState.editing,right:menu?.contentItem.mapToGlobal(menu.contentItem.width,0).x,buttonRight:button?.mapToGlobal(button.width,0).x})}function close():void{island.expanded=false}function holdReview(on:bool):void{ShelfState.interaction(on)}function editHome(on:bool):void{ShelfState.editing=on}function page(n:int):void{playerReview.visible=false;island.selectPage(n)}function playerMode(name:string):void{playerReview.portrait=name==='player';playerReview.implicitWidth=name==='activity' ? 440:name==='mini' ? 340:360;playerReview.implicitHeight=name==='activity' ? 178:name==='mini' ? 254:540;playerReview.visible=true}function floatingMode(name:string):void{playerReview.visible=false;IslandConfig.setStyle("floatingPlayerSize",name);ShelfState.playerOpen=true}function basketReview(on:bool):void{ShelfState.basketPosition=Qt.point(960,540);ShelfState.basketOpen=on}function notchReview(on:bool):void{IslandConfig.setStyle('surfaceMode',on ? 'notch':'island')}function transformReview(on:bool):void{island.expanded=!on;ShelfState.transformPaths=ShelfState.items.filter(i=>i.name.endsWith('.png')).map(i=>i.path);ShelfState.transformOpen=on}function closePlayer():void{ShelfState.playerOpen=false}function volume(value:real):void{MprisState.activePlayer.volume=value}function populate():void{populateReview()}function developerReview():void{const widget=named(island.contentItem,'shelf-developer-tools');const field=named(island.contentItem,'developer-input');field.text='{\"hello\":true}';widget.run()}function developerState():string{const widget=named(island.contentItem,'shelf-developer-tools');return JSON.stringify({result:widget?.result,error:widget?.error})}function detail(key:string):void{island.detailWidget=key;island.selectPage(13)}function playback():void{MprisState.togglePlaying()}function state():string{return JSON.stringify({transformOpen:ShelfState.transformOpen,transformPaths:ShelfState.transformPaths,basketVisible:basketPanel.visible,basketWidth:basketPanel.width,basketHeight:basketPanel.height,basketX:basketPanel.margins.left,basketY:basketPanel.margins.top,basketScreen:basketPanel.screen?.name,banners:NotifService.popupModel.count,reserveClockSpace:IslandConfig.s("reserveClockSpace"),playerVolume:MprisState.activePlayer ? MprisState.activePlayer.volume:0,playerLayout:reviewPlayer.qaLayout,playing:MprisState.isPlaying,hasPlayer:MprisState.hasPlayer,expanded:island.expanded,page:island.page,hold:ShelfState.holdOpen,clipCount:ShelfState.clips.length,fileIcon:IconResolver.forFile('thought.txt'),names:visualNames(island.contentItem),geometry:island.qaGeometry})}}
  }''')
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_CACHE_HOME=tmp+'/.cache',XDG_STATE_HOME=tmp+'/.state',XDG_RUNTIME_DIR=runtime,WAYLAND_DISPLAY=os.environ['QUICKINTOSH_TEST_PRIVATE_WAYLAND'],HYPRLAND_INSTANCE_SIGNATURE=os.environ['QUICKINTOSH_TEST_PRIVATE_HYPRLAND'],DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
   env.pop('DISPLAY',None);env['QT_NO_XDG_DESKTOP_PORTAL']='1'
   icons=root/'.local/share/icons';icons.parent.mkdir(parents=True);icons.symlink_to(source/'assets/icons_desktop',target_is_directory=True)
   env['XDG_DATA_HOME']=str(root/'.local/share')
   qt6ct=root/'.config/qt6ct';qt6ct.mkdir(parents=True)
   (qt6ct/'qt6ct.conf').write_text('[Appearance]\nicon_theme=MacTahoe-dark\n')
   clips=root/'.cache/quickshell/spotlight_clip';clips.mkdir(parents=True)
   (clips/'thought.txt').write_text('A quick thought to keep nearby.')
   (clips/'color.txt').write_text('#6F7BF2')
   cover=Path(os.environ['QA_MEDIA_ART'].removeprefix('file://'));shutil.copyfile(cover,clips/'cover.png')
   env['QA_TRAY_FILES']=json.dumps([str(clips/'thought.txt'),str(clips/'cover.png')])
   bus=subprocess.Popen(['dbus-daemon','--session','--nofork','--print-address=1','--address=unix:path='+tmp+'/bus'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   address=bus.stdout.readline().strip();assert address.startswith('unix:path='+tmp+'/bus'),address
   env['DBUS_SESSION_BUS_ADDRESS']=address
   mediaLog=(out/'mpris.log').open('w')
   media=subprocess.Popen([os.environ.get('QUICKINTOSH_TEST_PYTHON',sys.executable),str(Path(__file__).parent/'fixtures/mpris_player.py'),str(out/'mpris-actions.jsonl')],env=env,stdout=mediaLog,stderr=mediaLog)

   def ctl(*args):return subprocess.check_output(['hyprctl',*args],env=env,text=True,timeout=30)
   ctl('dismissnotify','-1')
   ctl('plugin','load',os.environ['QUICKINTOSH_TEST_GLASS_PLUGIN'])
   config=Path(os.environ['QUICKINTOSH_TEST_CONFIG']);config.write_text(config.read_text()+"\nif hl.plugin.hyprglass then hl.plugin.hyprglass.config({enabled=true,layers={enabled=true,force_live_resample=false}});hl.plugin.hyprglass.preset('quickintosh-island',{inherits='pomme',blur_strength=0.65,bevel_strength=0.18,specular_strength=0.22,dark={brightness=1,contrast=1,tint_color=0},light={brightness=1,contrast=1,tint_color=0}});hl.plugin.hyprglass.layer('quickintosh-island-dashboard',{preset='quickintosh-island',mask_mode='contour',mask_threshold=0.004,live_resample=true}) end\n")
   ctl('reload');ctl('dismissnotify','-1')
   def ipc(*args):
    r=subprocess.run([qs,'-p',tmp,'ipc','call','reviewA',*args],env=env,capture_output=True,text=True,timeout=30)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr+(root/'log').read_text()[-4000:])
    return r.stdout
   def wait_state(predicate):
    deadline=time.monotonic()+30;last={}
    while time.monotonic()<deadline:
     last=json.loads(ipc('state'))
     if predicate(last):return last
     time.sleep(.04)
    raise AssertionError('UI did not settle: '+str(last))
   with (root/'log').open('w') as log:p=subprocess.Popen([qs,'-p',tmp],env=env,stdout=log,stderr=log,start_new_session=True)
   try:
    deadline=time.monotonic()+90;startup_error=None
    while time.monotonic()<deadline:
     assert p.poll() is None,(root/'log').read_text()
     try:state=json.loads(ipc('state'));break
     except (RuntimeError,ValueError,subprocess.TimeoutExpired) as error:startup_error=error;time.sleep(.1)
    else:raise RuntimeError('No UI IPC: '+str(startup_error))
    wait_state(lambda s:s.get('hasPlayer') and s.get('playing') and s.get('fileIcon'));assert json.loads(ipc('state'))['reserveClockSpace'] is True;ipc('playback');wait_state(lambda s:not s['playing']);ipc('playback');wait_state(lambda s:s['playing'])
    ctl('eval','hl.dispatch(hl.dsp.cursor.move({x=640,y=65}))')
    ipc('holdReview','true');ipc('expandIsland')
    state=wait_state(lambda s:s['expanded'] and abs(s['geometry']['bodyHeight']-216)<.01)
    assert state['geometry']['contentScale']==1,state
    assert abs(state['geometry']['bodyHeight']-216)<.01,state
    ipc('populate');ipc('expandIsland')
    if os.environ.get('QUICKINTOSH_REVIEW_NATIVE_DRAG')=='1':
     plugin=Path('/tmp/qi-geometry-shelf-path').read_text().strip()+'/lib/quickintosh-geometry.so';ctl('plugin','load',plugin)
     ipc('page','6');wait_state(lambda s:s['page']==6 and 'tray-item-0' in s['names'] and abs(s['geometry']['bodyWidth']-720)<.01)
     time.sleep(.5);point=json.loads(ipc('nativeTrayPoint'));assert len(point)==2,point
     executable=Path('/tmp/qi-private-pointer-path').read_text().strip()+'/bin/qi-private-pointer'
     native=subprocess.Popen([executable],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
     def pointer_command(command):native.stdin.write(command+'\n');native.stdin.flush();assert native.stdout.readline().strip()=='ok';time.sleep(.07)
     def pointer_to(x,y):
      for _ in range(6):
       current=json.loads(ctl('-j','cursorpos'))
       if abs(current['x']-x)<3 and abs(current['y']-y)<3:return
       pointer_command('move '+str(x-current['x'])+' '+str(y-current['y']))
      current=json.loads(ctl('-j','cursorpos'));assert abs(current['x']-x)<5 and abs(current['y']-y)<5,current
     try:
      pointer_to(*point);pointer_command('down');time.sleep(.2);before={'source':point,'cursor':json.loads(ctl('-j','cursorpos')),'mouse':json.loads(ipc('nativeDragState'))};pointer_command('move 35 0');time.sleep(.2);before['afterMove']=json.loads(ipc('nativeDragState'));(out/'native-mouse-state.json').write_text(json.dumps(before,indent=2))
      for direction in [1,-1,1,-1,1,-1,1,-1,1,-1]:pointer_command('move '+str(direction*90)+' 0')
      state=wait_state(lambda s:s['basketVisible']);(out/'native-drag-before-drop.json').write_text(json.dumps({'state':state,'cursor':json.loads(ctl('-j','cursorpos')),'sourcePoint':point},indent=2))
      subprocess.run(['grim','-l','1',str(out/'native-drag-shake.png')],env=env,check=True,timeout=30)
      pointer_to(state['basketX']+195,state['basketY']+60);time.sleep(.2);(out/'native-target-state.json').write_text(ipc('basketDragState'));pointer_command('up')
      state=wait_state(lambda s:s['transformOpen'] and not s['basketVisible']);assert state['transformPaths'],state
      (out/'native-drag-state.json').write_text(json.dumps(state,indent=2))
      print('NATIVE_URI_DRAG_GLOBAL_SHAKE_AND_BASKET_TRANSFORM_DROP_OK');return
     finally:
      if native.poll() is None:
       pointer_command('up');native.stdin.write('quit\n');native.stdin.flush();native.wait(timeout=5)
      native.stdin.close();native.stdout.close()
    ipc('menuOpen');time.sleep(1.5);menu=json.loads(ipc('menuState'));assert menu['visible'] and menu['width']>=220 and menu['height']>=100,menu
    (out/'context-material.json').write_text(json.dumps(menu,indent=2))
    subprocess.run(['grim','-l','1',str(out/'home-context-menu.png')],env=env,check=True,timeout=30)
    ipc('menuHover');time.sleep(.1)
    subprocess.run(['grim','-l','1',str(out/'home-context-menu-highlight.png')],env=env,check=True,timeout=30)
    ipc('menuSelect');wait_state(lambda s:s['hold']);assert json.loads(ipc('menuState'))['editing'],'Menu click did not activate customization'
    swapped=json.loads(ipc('reorderReview'));(out/'widget-reorder.json').write_text(json.dumps(swapped));assert swapped['after'][0]==swapped['before'][1] and swapped['after'][1]==swapped['before'][0],swapped
    ipc('editHome','false')
    if os.environ.get('QUICKINTOSH_REVIEW_MENU_ONLY')=='1':
     print('NATIVE_CONTEXT_MENU_WIDTH_ANCHOR_AND_CLICK_OK',menu);return
    if os.environ.get('QUICKINTOSH_REVIEW_UTILITIES')=='1':
     for key in ['developer','teleprompter','vault','breather']:
      ipc('detail',key);wait_state(lambda s:abs(s['geometry']['bodyWidth']-620)<.01);time.sleep(.5)
      subprocess.run(['grim','-l','1',str(out/('widget-'+key+'.png'))],env=env,check=True,timeout=30)
      if key=='developer':
       ipc('developerReview')
       for attempt in range(100):
        tool=json.loads(ipc('developerState'))
        if tool.get('result'):break
        time.sleep(.1)
       assert not tool.get('error') and json.loads(tool['result'])=={'hello':True},tool
     ipc('notchReview','true');ipc('page','3');time.sleep(.8)
     subprocess.run(['grim','-l','1',str(out/'notch-media.png')],env=env,check=True,timeout=30)
     diagnostics=(root/'log').read_text()
     for issue in ['ReferenceError:','TypeError:','Cannot assign','Cannot open file','Failed to load configuration']:
      assert issue not in diagnostics,diagnostics[-8000:]
     print('NATIVE_UTILITIES_TOOLKIT_VAULT_TELEPROMPTER_BREATHER_AND_NOTCH_OK');return
    recordingLog=(out/'recording.log').open('w')
    recorder=subprocess.Popen(['wf-recorder','-D','--no-dmabuf','-r','60','-c','libx264','-p','preset=ultrafast','-p','threads=2','-g','350,0 1220x650','-f',str(out/'transitions.mp4')],env=env,stdout=recordingLog,stderr=recordingLog)
    for page,name in [(0,'home'),(6,'tray'),(8,'widgets')]:
     ipc('populate');ctl('eval','hl.dispatch(hl.dsp.cursor.move({x=640,y=65}))');ipc('page',str(page));wait_state(lambda s:s['page']==page and abs(s['geometry']['bodyHeight']-(310 if page==8 else 250 if page==6 else 216))<.01);assert json.loads(ipc('state'))['expanded'],'Page change collapsed the island'
     subprocess.run(['grim','-l','1',str(out/(name+'.png'))],env=env,check=True,timeout=30)
     (out/(name+'.json')).write_text(ipc('state'))
    if os.environ.get('QUICKINTOSH_REVIEW_ALL_PAGES')=='1':
     page_names={1:'weather',2:'system',3:'media',4:'notifications',5:'camera',6:'tray',7:'clipboard',8:'widgets',9:'lyrics',10:'audio',11:'activities',12:'awake',13:'calendar',14:'storage'}
     if os.environ.get('QUICKINTOSH_REVIEW_FOCUSED')=='1':page_names={key:value for key,value in page_names.items() if key in (4,6,7,14)}
     (out/'pages.json').write_text(json.dumps(page_names,indent=2))
     for page,name in page_names.items():
      ipc('page',str(page));expected_width={1:560,2:540,3:460,4:480,5:480,6:720,7:1000,8:1000,9:620,10:440,11:580,12:500,13:620,14:540}[page];wait_state(lambda s:s['page']==page and abs(s['geometry']['bodyWidth']-expected_width)<.01);time.sleep(.3);ipc('populate');time.sleep(.2)
      if page==7:wait_state(lambda s:s['clipCount']==3)
      subprocess.run(['grim','-l','1',str(out/('page-'+name+'.png'))],env=env,check=True,timeout=30)
      (out/('page-'+name+'.json')).write_text(ipc('state'))
     ipc('page','4');assert ipc('replyReview').strip()=='Count me in! See you at 7.';time.sleep(.1)
     subprocess.run(['grim','-l','1',str(out/'notification-sent.png')],env=env,check=True,timeout=30)
     ipc('page','0');ipc('editHome','true');time.sleep(.4)
     subprocess.run(['grim','-l','1',str(out/'inline-editor.png')],env=env,check=True,timeout=30)
     ipc('editHome','false');ipc('transformReview','true');time.sleep(2.5)
     window=None;deadline=time.monotonic()+30
     while time.monotonic()<deadline:
      window=next((w for w in json.loads(ctl('-j','clients')) if w.get('title')=='Quickintosh Transform'),None)
      if window and window['floating'] and all(abs(a-b)<3 for a,b in zip(window['size'],[414,680])):break
      time.sleep(.1)
     assert window and window['floating'] and all(abs(a-b)<3 for a,b in zip(window['size'],[414,680])),window
     subprocess.run(['grim','-l','1',str(out/'transform.png')],env=env,check=True,timeout=30)
     ipc('transformReview','false');ipc('basketReview','true');wait_state(lambda s:s['basketVisible'] and s['basketWidth']==260);time.sleep(1.0)
     (out/'basket-state.json').write_text(ipc('state'));(out/'basket-layers.json').write_text(ctl('-j','layers'))
     subprocess.run(['grim','-l','1',str(out/'drag-basket.png')],env=env,check=True,timeout=30)
     ipc('basketReview','false');ipc('notchReview','true');ipc('page','3');time.sleep(.4)
     subprocess.run(['grim','-l','1',str(out/'notch-media.png')],env=env,check=True,timeout=30)
     ipc('notchReview','false')
     for key in ([] if os.environ.get('QUICKINTOSH_REVIEW_FOCUSED')=='1' else ['focus','notes','performance','files','clipboard','audio','awake','storage','camera','notifications','developer','teleprompter','vault','breather']):
      ipc('detail',key);wait_state(lambda s:(key not in ['focus','notes','performance'] or 'shelf-'+('stats' if key=='performance' else key) in s['names']) and abs(s['geometry']['bodyWidth']-(620 if key in ('developer','teleprompter','vault','breather') else 380))<.01);ipc('populate');time.sleep(.3)
      if key=='developer':
       ipc('developerReview')
       for attempt in range(100):
        tool=json.loads(ipc('developerState'))
        if tool.get('result'):break
        time.sleep(.1)
       assert not tool.get('error') and json.loads(tool['result'])=={'hello':True},tool
      subprocess.run(['grim','-l','1',str(out/('widget-'+key+'.png'))],env=env,check=True,timeout=30)
     ipc('page','8');wait_state(lambda s:s['page']==8)
    if os.environ.get('QUICKINTOSH_REVIEW_EXPANDED')=='1':
     for mode in ['activity','mini','player']:
      ipc('playerMode',mode);time.sleep(.6)
      state=wait_state(lambda s:s['playerLayout']['portrait']==(mode=='player') and s['playerLayout']['seekWidth']>100)
      assert state['playerLayout']['titleWidth']>100,state
      subprocess.run(['grim','-l','1',str(out/('expanded-'+mode+'.png'))],env=env,check=True,timeout=30)
      (out/('expanded-'+mode+'.json')).write_text(json.dumps(state))
     ipc('close');time.sleep(.5)
     for mode in ['mini','player','expanded']:
      ipc('floatingMode',mode)
      deadline=time.monotonic()+10
      while time.monotonic()<deadline:
       clients=json.loads(ctl('-j','clients'));window=next((w for w in clients if w.get('title')=='Quickintosh Floating Player'),None)
       expected=[340,254] if mode=='mini' else [360,540] if mode=='player' else [760,540]
       if window and window['floating'] and all(abs(a-b)<3 for a,b in zip(window['size'],expected)):break
       time.sleep(.1)
      else:raise AssertionError('Floating player geometry: '+str(window))
      (out/('floating-'+mode+'.json')).write_text(json.dumps(window))
      time.sleep(.3)
      subprocess.run(['grim','-l','1',str(out/('floating-'+mode+'.png'))],env=env,check=True,timeout=30)
     ipc('closePlayer')
     ipc('volume','0.35');wait_state(lambda s:abs(s['playerVolume']-.35)<.01)
     ipc('page','8');ipc('expandIsland')
    if os.environ.get('QUICKINTOSH_REVIEW_BANNERS')=='1':
     ipc('close');ipc('banner','true');wait_state(lambda s:s['banners']==1);time.sleep(.6)
     subprocess.run(['grim','-l','1',str(out/'notification-banner.png')],env=env,check=True,timeout=30)
     ipc('banner','false');wait_state(lambda s:s['banners']==0);ipc('expandIsland')
    if os.environ.get('QUICKINTOSH_REVIEW_TAB_LAYOUT')=='1':
     for page in [8,3,8,1,8,7,8,0,8]:
      ipc('page',str(page));time.sleep(.035)
      state=json.loads(ipc('state'));assert state['page']==page,state
     time.sleep(.3)
     subprocess.run(['grim','-l','1',str(out/'widgets-after-rapid-switch.png')],env=env,check=True,timeout=30)
    if os.environ.get('QUICKINTOSH_REVIEW_TAB_RESPONSE')=='1':
     samples=json.loads(ipc('tabBench'));assert all(s['immediate'] for s in samples),samples
     (out/'tab-response.json').write_text(json.dumps(samples,indent=2));ipc('page','8')
    ipc('editHome','true');wait_state(lambda s:s['hold'] and abs(s['geometry']['bodyHeight']-440)<.01)
    subprocess.run(['grim','-l','1',str(out/'editor.png')],env=env,check=True,timeout=30)
    (out/'editor.json').write_text(ipc('state'))
    ipc('holdReview','false')
    ctl('eval','hl.dispatch(hl.dsp.cursor.move({x=960,y=850}))');time.sleep(.7)
    assert json.loads(ipc('state'))['expanded'],'Editor collapsed while being configured'
    ipc('editHome','false');ipc('page','0');time.sleep(.4);ctl('eval','hl.dispatch(hl.dsp.cursor.move({x=960,y=850}))');time.sleep(.7);assert json.loads(ipc('state'))['expanded'],'Right-click shelf must remain open after pointer exit';ipc('close');wait_state(lambda s:not s['expanded'])
    ipc('expandIsland');time.sleep(.2);ipc('close')
    state=wait_state(lambda s:abs(s['geometry']['bodyWidth']-92)<.01 and abs(s['geometry']['bodyHeight']-26)<.01);assert abs(state['geometry']['bodyWidth']-92)<1 and abs(state['geometry']['bodyHeight']-26)<1,state
    recorder.send_signal(signal.SIGINT);recorder.wait(timeout=45);recordingLog.close()
    assert recorder.returncode==0,(out/'recording.log').read_text()
    stats=json.loads(ctl('-j','hyprglass','stats'))['monitors']
    draws=sum(m['layerGlassDraws'] for m in stats);misses=sum(m['layerCacheMisses'] for m in stats);deferred=sum(m['layerDeferredResamples'] for m in stats)
    hits=sum(m['layerCacheHits'] for m in stats)
    assert draws>0 and misses+deferred+hits>=draws,stats
    if os.environ.get('QUICKINTOSH_REVIEW_BANNERS')!='1':assert hits==0,stats
    qml_log=(root/'log').read_text()
    for issue in ['ReferenceError:','TypeError:','Cannot assign','Cannot open file','Failed to load configuration']:
     assert issue not in qml_log,issue+'\n'+qml_log[-6000:]
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
    # Stop the UI before its providers so teardown cannot mask a test failure.
    if p.poll() is None:
     os.killpg(p.pid,signal.SIGTERM)
     try:p.wait(timeout=4)
     except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    for provider in (media,bus):
     if provider.poll() is None:
      provider.terminate()
      try:provider.wait(timeout=4)
      except subprocess.TimeoutExpired:provider.kill();provider.wait()
    mediaLog.close();bus.stdout.close();bus.stderr.close()
    shutil.copyfile(root/'log',out/'qml.log')

if __name__=='__main__':unittest.main()
