"""Probe real pixels once; preserve colored app icons and follow bar ink."""
from pathlib import Path
import tempfile,unittest
import test_qml_interface as qml
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(qml.QS,'Set QUICKINTOSH_TEST_QS')
class TrayColors(unittest.TestCase):
 def test_monochrome_and_colored_icons(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'components').mkdir();(root/'services').mkdir()
   (root/'components/TrayIcon.qml').write_text((ROOT/'modules/lickintosh/tray-colors/TrayIcon.qml').read_text())
   (root/'components/qmldir').write_text('module qs.components\nTrayIcon TrayIcon.qml\n')
   (root/'services/qmldir').write_text('module qs.services\nsingleton TopBarStyle TopBarStyle.qml\n')
   (root/'services/TopBarStyle.qml').write_text('pragma Singleton\nimport QtQuick\nimport Quickshell\nSingleton{property color ink:"#111111";function colorFor(screen,side){return ink}}')
   for name,color in [('white','white'),('black','black'),('color','#f1ae36')]:
    (root/(name+'.svg')).write_text('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><path fill="'+color+'" d="M4 4h24v24H4z"/></svg>')
   output=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
import qs.components
import qs.services
Scope{
 FloatingWindow{
  visible:true;width:120;height:40
  TrayIcon{id:white;width:32;height:32;source:'file://'+Quickshell.shellDir+'/white.svg'}
  TrayIcon{id:black;x:40;width:32;height:32;source:'file://'+Quickshell.shellDir+'/black.svg'}
  TrayIcon{id:colored;x:80;width:32;height:32;source:'file://'+Quickshell.shellDir+'/color.svg'}
 }
 Timer{interval:900;running:true;onTriggered:{
  if(!white.monochrome || !black.monochrome || colored.monochrome){Qt.exit(21);return}
  TopBarStyle.ink='#fafafa'
 }}
 Timer{interval:1200;running:true;onTriggered:{
  if(String(white.foreground)!=='#fafafa'){Qt.exit(22);return}
  console.log('TRAY_MONOCHROME_COLOR_AND_ADAPTIVE_INK_OK');Qt.quit()
 }}
}''')
   self.assertIn('TRAY_MONOCHROME_COLOR_AND_ADAPTIVE_INK_OK',output)
if __name__=='__main__':unittest.main()
