"""Opt-in panel lifecycle check in an explicitly isolated Wayland compositor.

Requires a built source, private compositor/runtime and matching read-only
Hyprland fixture. Never falls back to the host Wayland socket or host HOME.
"""
from pathlib import Path
import os,shutil,subprocess,tempfile,unittest
SOURCE=os.environ.get('QUICKINTOSH_TEST_SOURCE','')
QS=os.environ.get('QUICKINTOSH_TEST_QS','')
RUNTIME=os.environ.get('QUICKINTOSH_TEST_PRIVATE_RUNTIME','')
WAYLAND=os.environ.get('QUICKINTOSH_TEST_PRIVATE_WAYLAND','')
SIGNATURE=os.environ.get('QUICKINTOSH_TEST_PRIVATE_HYPRLAND','')
@unittest.skipUnless(all([SOURCE,QS,RUNTIME,WAYLAND,SIGNATURE]),'An isolated compositor and built source are required')
class PanelResponsiveness(unittest.TestCase):
 def test_prepared_panels_reopen_without_discarding_glass_or_claiming_hidden_input(self):
  self.assertNotEqual(Path(RUNTIME).resolve(),Path(os.environ.get('XDG_RUNTIME_DIR','/run/user/'+str(os.getuid()))).resolve(),'Refusing the host runtime')
  self.assertTrue(SIGNATURE.startswith('quickintosh-'),'Use a read-only compositor fixture')
  with tempfile.TemporaryDirectory(prefix='quickintosh-panels-') as directory:
   root=Path(directory);app=root/'app';app.mkdir();home=root/'home';(home/'Desktop').mkdir(parents=True);(home/'.config').mkdir()
   (home/'.config/user-dirs.dirs').write_text('XDG_DESKTOP_DIR="'+str(home/'Desktop')+'"\n')
   (home/'.config/lickintosh').mkdir(parents=True)
   (home/'.config/lickintosh/shell-config.json').write_text('{"glass":{"captureWindows":false}}')
   src=Path(SOURCE)
   for entry in src.iterdir():
    if entry.name!='shell.qml':(app/entry.name).symlink_to(entry,target_is_directory=entry.is_dir())
   def detach(path):
    if path==app:return
    detach(path.parent)
    if path.is_symlink():
     original=path.resolve();path.unlink()
     if original.is_dir():
      path.mkdir()
      for entry in original.iterdir():(path/entry.name).symlink_to(entry,target_is_directory=entry.is_dir())
     else:shutil.copyfile(original,path)
   env=dict(os.environ,HOME=str(home),XDG_CONFIG_HOME=str(home/'.config'),XDG_CACHE_HOME=str(home/'.cache'),XDG_STATE_HOME=str(home/'.local/state'),XDG_RUNTIME_DIR=RUNTIME,WAYLAND_DISPLAY=WAYLAND,QT_QPA_PLATFORM='wayland',HYPRLAND_INSTANCE_SIGNATURE=SIGNATURE)
   for key in ('DISPLAY','DBUS_SESSION_BUS_ADDRESS'):env.pop(key,None)
   for name,rootid,winid,backdrop in [
    ('ui/topbar/statusarea/controlcenter/ControlCenter.qml','root','ccWindow','ccBackdrop'),
    ('ui/topbar/statusarea/notifcenter/NotifCenter.qml','root','ncWin','testGlass'),
    ('ui/topbar/menubar/applemenu/AppleMenuWindow.qml','root','panel','testGlass'),
    ('ui/topbar/statusarea/StatusSubMenuWindow.qml','root','panel','testGlass'),
    ('ui/topbar/menubar/globalmenu/PopupMenu.qml','root','panel','menuBackdrop'),
    ('ui/topbar/statusarea/spotlight/SpotlightWindow.qml','root','win','testGlass')]:
    p=app/name;detach(p);s=p.read_text();s=s.replace('    id: root','    id: root\n    property var testWindow:null',1)
    if backdrop=='testGlass':
     import re
     s=re.sub(r'GlassBackdrop\s*\{', 'GlassBackdrop { id:testGlass;',s,count=1)
    s=s.replace('id: '+winid+'\n','id: '+winid+'\n                property var testBackdrop:'+backdrop+'\n                Component.onCompleted:root.testWindow=this\n',1)
    # Existing onCompleted on menu panels must be merged, not duplicated.
    s=s.replace('Component.onCompleted: panel.entered = true','Component.onCompleted:{panel.entered=true;root.testWindow=panel}').replace('                Component.onCompleted:root.testWindow=this\n                mask:', '                Component.onCompleted:root.testWindow=this\n                mask:')
    if winid=='panel':s=s.replace('                Component.onCompleted:root.testWindow=this\n','')
    if 'ccWindow'==winid:s=s.replace('property var testBackdrop:ccBackdrop','readonly property real testProgress:ccContent.showProgress\n                property var testBackdrop:ccBackdrop')
    # Other completed handlers in Spotlight already exist at window scope.
    if winid=='win':
     s=s.replace('                Component.onCompleted:root.testWindow=this\n','')
     s=s.replace('property var testBackdrop:testGlass','property var testBackdrop:testGlass\n                Timer{interval:20;running:true;onTriggered:root.testWindow=win}',1)
    p.write_text(s)
   (app/'shell.qml').write_text('''import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.components.glass
import qs.services
import qs.ui.topbar.statusarea.controlcenter
import qs.ui.topbar.statusarea.notifcenter
import qs.ui.topbar.statusarea
import qs.ui.topbar.statusarea.spotlight
import qs.ui.topbar.menubar.applemenu
import qs.ui.topbar.menubar.globalmenu
Scope{
 ControlCenter{id:cc}
 NotifCenter{id:nc}
 AppleMenuWindow{id:apple}
 StatusSubMenuWindow{id:status;contentComponent:Component{Item{implicitHeight:100;signal closeRequested()}}}
 PopupMenu{id:global;items:[{label:'Test',title:'Test'}]}
 SpotlightWindow{id:spot}
 property var panels:[cc,nc,apple,status,global,spot,spot]
 property int index:0
 property int phase:0
 property real started:Date.now()
 property real openedAt:0
 property real first:0
 property int opens:0
 property real maxFrame:0
 property real lastFrame:Date.now()
 function fail(message){console.error('READINESS_FAILED',message,index,phase);Qt.exit(2)}
 FrameAnimation{running:true;onTriggered:{
  const now=Date.now();if(phase>0)maxFrame=Math.max(maxFrame,now-lastFrame);lastFrame=now
  if(now-started>65000){fail('timeout '+GlassPrewarm.queue.length);return}
  if(phase===0){
   if(now-started<5000)return
   if(now-started<16000 && (GlassPrewarm.current!==null || GlassPrewarm.queue.length>0 || panels.some(p=>!p.testWindow || !p.testWindow.testBackdrop?.captureSettled)))return
   for(let p of panels){const w=p.testWindow;if(!w || !w.testBackdrop){fail('window not prepared');return}
    const b=w.testBackdrop;if(!b.retained || !b.captureSettled){fail('backdrop not ready '+b.retained+' '+b.captureSettled);return}
    if(b.prewarming){fail('preparation not finished');return}
    if(!b.materialPrepared){fail('material not prepared');return}
    if(w.visible){fail('closed prepared surface remains mapped');return}
    if(!w.mask || (w.mask.width>0 && w.mask.height>0)){fail('hidden surface has input area');return}
    if(w.WlrLayershell.keyboardFocus!==WlrKeyboardFocus.None){fail('hidden surface holds keyboard');return}
   }
   console.log('ALL_PANELS_PREPARED_BEFORE_INPUT');phase=1
  }
  const p=panels[index],w=p.testWindow,b=w.testBackdrop
  if(phase===1){openedAt=now;first=0;if(index===6)LauncherState.pendingAction="applications";p.opened=true;phase=2;return}
  if(phase===2){
   if(index===6 && w.preparedGrid!=="applications"){fail('Launchpad grid not prepared');return}
   if(!b.captureSettled){fail('lost prepared backdrop on reopen');return}
   if(!first && w.visible && w.contentItem.opacity>.99 && (p!==cc || w.testProgress>0)){first=now-openedAt;console.log('PANEL_FIRST_FRAME',index,first)}
   if(first && now-openedAt>first+700){if(b.warmItem && (!b.warmItem.visible || b.warmItem.opacity<.9)){if(now-openedAt>first+4500)fail('opened content invisible '+b.warmItem.visible+' '+b.warmItem.opacity);return}p.opened=false;openedAt=now;phase=3}
  }else if(phase===3 && now-openedAt>500){
   if(!b.retained || !b.captureSettled){fail('scene discarded on close');return}
   if(b.prewarming){fail('completed material prepared again on close');return}
   if(w.visible){fail('closed surface still mapped after animation '+JSON.stringify({active:b.presentationActive,warming:b.prewarming,retained:b.retained,opened:p.opened,win:b.win===w}));return}
   if(++opens<2){phase=1;return}opens=0;index++;if(index===panels.length){console.log('PANELS_REOPEN_READY_OK','MAX_FRAME',maxFrame);Qt.quit()}else phase=1
  }
 }}
}''')
   log=root/'panels.log'
   with log.open('w') as output:
    process=subprocess.Popen([QS,'-p',str(app)],env=env,stdout=output,stderr=output,start_new_session=True)
    try:code=process.wait(timeout=75)
    except subprocess.TimeoutExpired:process.kill();process.wait();self.fail(log.read_text())
   text=log.read_text();self.assertEqual(code,0,text)
   self.assertIn('ALL_PANELS_PREPARED_BEFORE_INPUT',text)
   self.assertIn('PANELS_REOPEN_READY_OK',text)
   for error in ['TypeError','ReferenceError','Failed to load configuration']:self.assertNotIn(error,text)
   print('\n'.join(line for line in text.splitlines() if 'PANEL_FIRST_FRAME' in line or 'PANELS_REOPEN_READY_OK' in line))
if __name__=='__main__':unittest.main()
