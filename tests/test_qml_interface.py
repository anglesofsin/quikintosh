"""Optional offscreen Qt tests; never lock or interact with the user's desktop."""
from pathlib import Path
import os
import shutil
import struct
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
QS=os.environ.get('QUICKINTOSH_TEST_QS') or shutil.which('quickshell') or shutil.which('qs')

@unittest.skipUnless(QS,'Set QUICKINTOSH_TEST_QS to run the optional offscreen checks')
class Interface(unittest.TestCase):
    def run_qml(self,directory,text,factor='1'):
        root=Path(directory)
        (root/'runtime').mkdir(mode=0o700,exist_ok=True)
        (root/'shell.qml').write_text(text)
        env=dict(os.environ,QT_QPA_PLATFORM='offscreen',QT_SCALE_FACTOR=factor,XDG_RUNTIME_DIR=str(root/'runtime'))
        for key in ('DISPLAY','WAYLAND_DISPLAY','QT_PLUGIN_PATH','QML_IMPORT_PATH','QML2_IMPORT_PATH'):env.pop(key,None)
        result=subprocess.run([QS,'-p',str(root)],env=env,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return result.stdout+result.stderr

    def test_lock_mirror_handles_early_native_notification(self):
        source=(ROOT/'modules/lickintosh/lock-state-sync.py').read_text()
        start=source.index('    function synchronizeLockState() {')
        function=source[start:source.index('    Timer {',start)]
        with tempfile.TemporaryDirectory() as directory:
            output=self.run_qml(directory,'''import QtQuick
import Quickshell
Scope {
 id:root
 property bool _sessionLocked:false
 property string capturePath:''
 property int stage:0
 signal lockRequested()
 signal unlockRequested()
 QtObject{id:lock;property bool locked:false;signal earlyNotify();function change(value){earlyNotify();locked=value}}
 QtObject{id:lockContext;function reset(){}}
 Timer{id:captureTimer;interval:10}
 Connections{target:lock;function onEarlyNotify(){Qt.callLater(root.synchronizeLockState)}}
'''+function+'''
 Timer{interval:50;running:true;repeat:true;onTriggered:{
  if(stage===0){lock.change(true);stage=1}
  else if(stage===1){if(!root._sessionLocked){Qt.exit(30);return}lock.change(false);stage=2}
  else{if(root._sessionLocked || lock.locked){Qt.exit(31);return}console.log('MIRROR_OK');Qt.quit()}
 }}
}''')
            self.assertIn('MIRROR_OK',output)

    def test_native_scale_and_capture_export_pixel_size(self):
        capture=(ROOT/'modules/lickintosh/capture/CaptureWindow.qml').read_text()
        self.assertIn('factor/(win.screen?.devicePixelRatio || 1)',capture)
        for factor in (.75,1,1.5,2):
            with self.subTest(factor=factor),tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'probe.png'
                output=self.run_qml(directory,'''import QtQuick
import Quickshell
Scope {
 FloatingWindow{visible:true;implicitWidth:240;implicitHeight:160
  Rectangle{id:probe;width:200;height:100;color:'red'}
  Timer{interval:200;running:true;onTriggered:{
   if(Math.abs(probe.Screen.devicePixelRatio-'''+str(factor)+''')>.01){Qt.exit(40);return}
   probe.grabToImage(result=>{result.saveToFile('''+repr(str(path))+''');Qt.quit()},Qt.size(200,100))
  }}
 }
}''',str(factor))
                header=path.read_bytes()
                self.assertEqual(header[:8],b'\x89PNG\r\n\x1a\n')
                self.assertEqual(struct.unpack('>II',header[16:24]),(round(200*factor),round(100*factor)))

if __name__=='__main__':unittest.main()
