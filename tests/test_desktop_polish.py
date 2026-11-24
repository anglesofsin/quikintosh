"""Offscreen regression checks; never connect to the user's compositor."""
import os
from pathlib import Path
import shutil
import tempfile
import unittest
import test_qml_interface as qml

SOURCE=os.environ.get('QUICKINTOSH_TEST_SOURCE','')
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(qml.QS and SOURCE,'Set QUICKINTOSH_TEST_SOURCE to a built shell and QUICKINTOSH_TEST_QS')
class DesktopPolish(unittest.TestCase):
    def test_widget_position_color_preservation_and_privacy_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);services=root/'services';services.mkdir()
            names=['WidgetState','PrivacyPresentation']
            for name in names:shutil.copyfile(Path(SOURCE)/'services'/f'{name}.qml',services/f'{name}.qml')
            stubs={
                'DesktopFiles':'property var layout:[];property bool desktopFocused:true',
                'AppearanceState':"property color iconColor:'#0088ff'",
                'ShellConfig':"property bool ready:false;property var options:({spotlight:{indexing:{wallpaperDir:''}}})",
                'WidgetRegistry':"function resolve(w){return w} function sizesOf(t,v){return ['s','m','l']} property var sizeLabels:({s:'Small'})",
            }
            for name,body in stubs.items():
                (services/f'{name}.qml').write_text('pragma Singleton\nimport QtQuick\nimport Quickshell\nSingleton{'+body+'}')
            (services/'qmldir').write_text('module qs.services\n'+''.join(f'singleton {n} {n}.qml\n' for n in [*names,*stubs]))
            # WidgetState's persistence belongs to this temporary directory.
            p=services/'WidgetState.qml';p.write_text(p.read_text().replace('Quickshell.env("HOME")',repr(directory)))
            (root/'.config/quickintosh/core').mkdir(parents=True)
            (root/'.config/lickintosh/core').mkdir(parents=True)
            result=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
import qs.services
Scope {
 Timer{interval:120;running:true;onTriggered:{
  WidgetState.areaWidth=1000;WidgetState.areaHeight=800
  DesktopFiles.layout=[{x:16,y:44,w:153,h:153}]
  WidgetState.desktop=[{id:'a',type:'image',size:'s',x:334,y:0,theme:'color',image:'/test.gif'}]
  WidgetState.moveWidget('a',17,23,false)
  let a=WidgetState.desktop[0]
  if(a.x===0 && a.y===0){Qt.exit(11);return}
  WidgetState.moveWidget('a',17,23,true);a=WidgetState.desktop[0]
  if(a.x!==17 || a.y!==23 || !a.freePosition || a.theme!=='color' || a.image!=='/test.gif'){Qt.exit(12);return}
  const drop=WidgetState.snap('s',17,23,true)
  if(drop.x!==17 || drop.y!==23){Qt.exit(18);return}
  WidgetState.allowCtrlFreePlacement=false;WidgetState.moveWidget('a',17,23,true);a=WidgetState.desktop[0]
  if(a.freePosition || a.x===17){Qt.exit(13);return}
  if(WidgetState.widgetMaterial!=='glass' || WidgetState.desktopMenuMaterial!=='glass'){Qt.exit(14);return}
  for(const size of ['s','m','l','portrait','banner','wide','tall','square']){
   const d=WidgetState.sizeOf(size);if(d.w<153 || d.h<153){Qt.exit(15);return}
  }
  WidgetState.allowCtrlFreePlacement=true
  if(!WidgetState.resizeWidgetTo('a',500,250,false)){Qt.exit(19);return}
  let dimensions=WidgetState.sizeOf(WidgetState.desktop[0])
  if(dimensions.w!==500 || dimensions.h!==250 || WidgetState.desktop[0].image!=='/test.gif'){Qt.exit(20);return}
  DesktopFiles.layout=[{x:WidgetState.desktop[0].x+216,y:WidgetState.desktop[0].y+44,w:50,h:50}]
  if(WidgetState.resizeWidgetTo('a',600,280,false)){Qt.exit(21);return}
  if(!WidgetState.resizeWidgetTo('a',600,280,true)){Qt.exit(22);return}
  WidgetState.resizeWidget('desktop','a','m');dimensions=WidgetState.sizeOf(WidgetState.desktop[0])
  if(dimensions.w!==320 || dimensions.h!==153){Qt.exit(23);return}
  PrivacyPresentation.setCorner('test',true)
  if(!PrivacyPresentation.corner.test){Qt.exit(16);return}
  PrivacyPresentation.setCorner('test',false)
  if(PrivacyPresentation.corner.test){Qt.exit(17);return}
  console.log('PLACEMENT_COLOR_MATERIAL_PRIVACY_OK');Qt.quit()
 }}
}''')
            self.assertIn('PLACEMENT_COLOR_MATERIAL_PRIVACY_OK',result)

if __name__=='__main__':unittest.main()
