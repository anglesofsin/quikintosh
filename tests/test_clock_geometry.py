"""Exercise the actual clock component with deterministic time input."""
from pathlib import Path
import os,re,tempfile,unittest
from unittest.mock import patch
import test_qml_interface as qml
ROOT=Path(__file__).resolve().parents[1]
SOURCE=os.environ.get('QUICKINTOSH_TEST_SOURCE','')
@unittest.skipUnless(SOURCE and qml.QS,'Set QUICKINTOSH_TEST_SOURCE and QUICKINTOSH_TEST_QS')
class ClockGeometry(unittest.TestCase):
 def test_digits_keep_font_size_in_all_layouts(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);source=Path(SOURCE)
   for p in source.iterdir():
    if p.name not in ['shell.qml','settings.qml','installer.qml']:(root/p.name).symlink_to(p,target_is_directory=p.is_dir())
   def writable(p):
    if p==root:return
    writable(p.parent)
    if p.is_symlink():
     src=p.resolve();p.unlink();p.mkdir()
     for child in src.iterdir():(p/child.name).symlink_to(child,target_is_directory=child.is_dir())
   clock=root/'ui/widgets/types/PersonalClock.qml';writable(clock.parent);clock.unlink()
   # Replace only the clock's time source; rendering/layout are production code.
   text=(source/'ui/widgets/types/PersonalClock.qml').read_text()
   text=text.replace(' id:root',' id:root\n property date simulatedDate:new Date(2000,10,28,0,0,0)\n property alias renderedDigits:digits',1).replace('clock.date','root.simulatedDate').replace('id:digits;','id:digits;objectName:"timeDigits";')
   clock.write_text(text)
   # Only font/style dependencies are needed; never start desktop services.
   services=root/'services';services.unlink();services.mkdir()
   import shutil
   shutil.copyfile(source/'services/LockClockStyle.qml',services/'LockClockStyle.qml')
   shutil.copyfile(source/'services/WidgetFonts.qml',services/'WidgetFonts.qml')
   stubs={'Theme':"property color textPrimary:'#fff';property color accent:'#08f';property bool plainSurfaces:false",'I18n':"function tr(text){return text}",'SettingsPreferences':"property var accessibility:({reduceMotion:false})",'WidgetState':"property var desktopBackdrop:null",'RenderingState':"property bool shadows:true;property bool ambientAnimations:true",'ShellMotion':"function duration(ms){return ms}"}
   for name,body in stubs.items():
    (services/(name+'.qml')).write_text('pragma Singleton\nimport QtQuick\nimport Quickshell\nSingleton{'+body+'}')
   (services/'qmldir').write_text('module qs.services\n'+''.join('singleton '+name+' '+name+'.qml\n' for name in ['LockClockStyle','WidgetFonts',*stubs]))
   env={'HOME':directory,'XDG_CONFIG_HOME':directory+'/.config','XDG_STATE_HOME':directory+'/.local/state','XDG_CACHE_HOME':directory+'/.cache','HYPRLAND_INSTANCE_SIGNATURE':'','DBUS_SESSION_BUS_ADDRESS':'','QSG_RHI_BACKEND':'software'}
   wrapper=Path('/run/current-system/sw/bin/lickintosh')
   if wrapper.exists():
    match=re.search(r'export FONTCONFIG_FILE=([^\n]+)',wrapper.read_text())
    if match:env['FONTCONFIG_FILE']=match[1].strip('"')
   with patch.dict(os.environ,env):
    result=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
import qs.ui.widgets.types as Widgets
Scope{
 Item{
  Widgets.PersonalClock{id:clock;width:320;height:320}
 }
 property int resizeStep:0
 property var envelope:null
 property int step:0
 property real expected:0
 property var configs:[{clockSize:280,clockAnimate:true},{clockSize:280,clock12Hour:true},{clockSize:280,clockSeconds:true},{clockSize:280,variant:'stacked',clockSeconds:true},{clockSize:280,clockFont:'Georgia'},{clockAutoSize:true}]
 property var times:[[0,0,0],[1,11,11],[8,8,8],[9,9,9],[11,11,11],[12,0,0],[22,22,22],[23,59,59]]
 Timer{interval:30;running:true;repeat:true;onTriggered:{
  const config=Math.floor(step/times.length),index=step%times.length
  if(config>=configs.length){
   if(resizeStep===0){clock.widgetData={clockAutoSize:true};envelope=clock.measuredTime}
   clock.width=160+resizeStep*7;clock.height=100+resizeStep*3
   if(clock.measuredTime!==envelope || !isFinite(clock.fittedSize)){Qt.exit(43);return}
   if(++resizeStep>60){clock.isSnapshot=true;if(clock.backdrop!==null){Qt.exit(44);return}console.log('CLOCK_GEOMETRY_48_TIMES_OK');console.log('RESIZE_METRICS_REUSED_OK');Qt.quit()}return
  }
  if(index===0)clock.widgetData=configs[config]
  const t=times[index];clock.simulatedDate=new Date(2000,10,28,t[0],t[1],t[2])
  if(index===0)expected=clock.fittedSize
  if(!isFinite(clock.fittedSize) || Math.abs(clock.fittedSize-expected)>.01){console.error('CLOCK_SIZE_CHANGED',config,index,expected,clock.fittedSize);Qt.exit(41);return}
  if(clock.renderedDigits.stretch || clock.renderedDigits.scaleIn!==1 || clock.renderedDigits.scaleOut!==1 || clock.renderedDigits.font.features.tnum!==1){Qt.exit(42);return}
  step++
 }}
}''')
   self.assertIn('CLOCK_GEOMETRY_48_TIMES_OK',result)
if __name__=='__main__':unittest.main()
