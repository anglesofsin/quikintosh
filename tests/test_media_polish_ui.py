"""Capture actual media/calendar/battery surfaces in a private compositor."""
from pathlib import Path
import os,subprocess,tempfile,json,time,signal,unittest
from test_island_compact_ui import REQUIRED
@unittest.skipUnless(all(os.environ.get(k) for k in REQUIRED),'Private compositor required')
class MediaPolishUI(unittest.TestCase):
 def test_surfaces(self):
  assert not Path(os.environ[REQUIRED[2]]).is_relative_to('/run/user')
  out=Path('/home/pg/.local/state/quickintosh/reviews/media-polish');out.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(prefix='qi-review-media-polish-') as tmp:
   root=Path(tmp);source=Path(os.environ[REQUIRED[0]])
   for e in source.iterdir():
    if e.name!='shell.qml':(root/e.name).symlink_to(e,target_is_directory=e.is_dir())
   (root/'shell.qml').write_text('''import QtQuick
import QtQuick.Layouts
import QtTest
import Quickshell
import Quickshell.Io
import Quickshell.Widgets
import qs.island-shelf
import qs.services
import qs.rosa.services
ShellRoot{
 TestCase{id:pointer;name:'PrivateMediaPointer';when:false}
 FloatingMusic{id:floatingPlayer}
 FloatingWindow{id:win;title:'Media Polish Review';visible:true;implicitWidth:560;implicitHeight:360;color:'transparent'
  property string page:'media'
  ClippingRectangle{anchors.fill:parent;radius:40;color:'#050509';antialiasing:true;layer.enabled:true;layer.samples:4
   Rectangle{anchors.fill:parent;gradient:Gradient{GradientStop{position:0;color:'#00000000'}GradientStop{position:1;color:'#3d265e'}}}
   Loader{id:loader;anchors.fill:parent;anchors.margins:24;sourceComponent:({media:media,queue:queue,calendar:calendar,batteries:batteries,empty:empty,icons:icons})[win.page]}
  }
 }
 Component{id:media;ShelfMedia{}}
 Component{id:queue;QueueShelf{}}
 Component{id:calendar;ShelfCalendar{today:new Date(2026,10,27)}}
 Component{id:batteries;BatteriesShelf{reviewDevices:[{id:'pc',name:'Laptop',kind:'laptop',percent:81,charging:true},{id:'phone',name:'Phone',kind:'phone',percent:64},{id:'bad',name:'',percent:0},{id:'offline',name:'Disconnected',percent:40,connected:false}]}}
 Component{id:empty;BatteriesShelf{reviewDevices:[]}}
 Component{id:icons;RowLayout{spacing:24;Repeater{model:['laptop.png','notch/home.svg','notch/inbox.svg','notch/grid.svg'];delegate:ColumnLayout{required property string modelData;spacing:16;ShelfIcon{icon:modelData;size:16}ShelfIcon{icon:modelData;size:24}ShelfIcon{icon:modelData;size:32}}}}}
 IpcHandler{target:'mediaQA'
  function tap(name:string):void{function find(item){if(!item.visible)return null;if(item.objectName===name)return item;for(const child of item.children || []){const hit=find(child);if(hit)return hit}return null}const item=find(floatingPlayer.contentItem);if(!item)throw new Error('Missing control '+name);pointer.mouseClick(item,item.width/2,item.height/2,Qt.LeftButton)}
  function state():string{return JSON.stringify({floatingContent:floatingPlayer.content,page:win.page,playing:MprisState.isPlaying,has:MprisState.hasPlayer,loaded:loader.status===Loader.Ready,queue:ShelfState.queueData,playerOpen:ShelfState.playerOpen})}
  function page(name:string):void{win.page=name}
  function pause():void{MprisState.togglePlaying()}
  function floating(mode:string,content:string):void{IslandConfig.setStyle('floatingPlayerSize',mode);floatingPlayer.content=content;ShelfState.playerOpen=true;win.visible=false}
 }
}'''.replace("import qs.island-shelf","import 'island-shelf'"))
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_STATE_HOME=tmp+'/.state',XDG_CACHE_HOME=tmp+'/.cache',XDG_RUNTIME_DIR=os.environ[REQUIRED[2]],WAYLAND_DISPLAY=os.environ[REQUIRED[3]],HYPRLAND_INSTANCE_SIGNATURE=os.environ[REQUIRED[4]])
   bus=subprocess.Popen(['dbus-daemon','--session','--nofork','--print-address=1','--address=unix:path='+tmp+'/bus'],stdout=subprocess.PIPE,text=True)
   env['DBUS_SESSION_BUS_ADDRESS']=bus.stdout.readline().strip();env.pop('DISPLAY',None)
   python='/nix/store/5rziv4y1hvkimk8d1x20k7afh9p5z1qd-python3-3.14.7-env/bin/python3'
   service=subprocess.Popen([python,str(Path(__file__).parent/'fixtures/mpris_player.py'),tmp+'/actions'],env=env,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
   assert service.stdout.readline().strip()=='MPRIS_QA_READY'
   qs=os.environ[REQUIRED[1]]
   with (out/'qml.log').open('w') as log:p=subprocess.Popen([qs,'-p',tmp],env=env,stdout=log,stderr=log,start_new_session=True)
   def ipc(*args):
    assert p.poll() is None,(out/'qml.log').read_text()
    r=subprocess.run([qs,'-p',tmp,'ipc','call','mediaQA',*args],env=env,capture_output=True,text=True,timeout=20)
    if r.returncode:raise RuntimeError(r.stderr+r.stdout)
    return r.stdout
   def wait(predicate):
    for _ in range(150):
     try:
      s=json.loads(ipc('state'))
      if predicate(s):return s
     except (RuntimeError,ValueError,subprocess.TimeoutExpired):pass
     time.sleep(.1)
    raise AssertionError((out/'qml.log').read_text()[-5000:])
   def capture(name):
    time.sleep(.4);subprocess.run(['hyprctl','dismissnotify','-1'],env=env,capture_output=True)
    subprocess.run(['grim','-l','1',str(out/(name+'.png'))],env=env,check=True)
   def resize(w,h):
    command='for _,w in ipairs(hl.get_windows()) do if w.title=="Media Polish Review" then hl.dispatch(hl.dsp.window.float({action="enable",window="address:"..w.address}));hl.dispatch(hl.dsp.window.resize({x='+str(w)+',y='+str(h)+',window="address:"..w.address})) end end'
    subprocess.run(['hyprctl','eval',command],env=env,capture_output=True,check=True)
   try:
    wait(lambda s:s['has'] and s['loaded']);resize(560,290);capture('media-playing');ipc('pause');wait(lambda s:not s['playing']);capture('media-paused');ipc('pause')
    for name,size in [('calendar',(620,260)),('batteries',(560,300)),('empty',(560,250)),('icons',(400,220)),('queue',(380,570))]:
     ipc('page',name);wait(lambda s:s['loaded']);resize(*size)
     if name=='queue':wait(lambda s:s['queue'].get('supported') and len(s['queue'].get('items',[]))==2)
     capture(name)
    for mode,content in [('mini','player'),('player','player'),('expanded','player'),('player','queue'),('player','lyrics'),('player','outputs')]:
     ipc('floating',mode,content);wait(lambda s:s['playerOpen']);capture('floating-'+mode+'-'+content)
    ipc('floating','player','player');wait(lambda s:s['floatingContent']=='player');time.sleep(.2)
    ipc('tap','player-queue-button');wait(lambda s:s['floatingContent']=='queue');ipc('tap','player-queue-button');wait(lambda s:s['floatingContent']=='player')
    ipc('tap','floating-lyrics-button');wait(lambda s:s['floatingContent']=='lyrics');ipc('floating','player','player');wait(lambda s:s['floatingContent']=='player');ipc('tap','player-output-button');wait(lambda s:s['floatingContent']=='outputs')
    log=(out/'qml.log').read_text()
    for error in ['ReferenceError:','TypeError:','is not a type','Cannot assign','Binding loop']:self.assertNotIn(error,log,log[-6000:])
   finally:
    for stream in [service.stdout,bus.stdout]:stream.close()
    for proc in [p,service,bus]:
     if proc.poll() is None:proc.terminate();proc.wait(timeout=5)
if __name__=='__main__':unittest.main()
