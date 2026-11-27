"""Desktop menu ownership uses the actual visible special workspace."""
from pathlib import Path
import subprocess,shutil,unittest
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(shutil.which('node'),'Node required for policy test')
class Focus(unittest.TestCase):
 def test_special_open_close_and_stale_active_window(self):
  source=(ROOT/'modules/lickintosh/finder-menus/DesktopFocus.js').read_text()
  cases='''
const named={activeWorkspace:{address:'2',id:2,name:'2'},specialWorkspace:{address:'special:right',type:'special',name:'special:right'}};
const namedApp={workspace:{address:'special:right',name:'special:right'},mapped:true};
if(!windowVisible(namedApp,named))throw Error('0.57 named special lost focus');
if(windowVisible({workspace:{id:2,name:'2'}},named))throw Error('named special covered regular focus');
const close=specialEvent('activespecialv2',',,HDMI-A-1','HDMI-A-1');
if(close!==0 || windowVisible(namedApp,named,null,close))throw Error('named special close retained focus');
if(!windowVisible({workspace:{id:2}},named,null,close))throw Error('close lost regular app');
if(specialEvent('activespecialv2','-98,special:left,DP-2','HDMI-A-1')!==null)throw Error('foreign monitor changed focus');
const open=specialEvent('activespecialv2','-98,special:right,HDMI-A-1','HDMI-A-1');
if(!windowVisible(namedApp,named,null,open))throw Error('open event lost named workspace');
const m={activeWorkspace:{id:2},activeSpecialWorkspace:{id:0}};
const special={workspace:{id:-98},mapped:true};
if(windowVisible(special,m,0))throw Error('closed special retained app');
m.activeSpecialWorkspace.id=-98;
if(windowVisible({workspace:{id:2}},m,0))throw Error('covered regular workspace claimed focus');
if(!windowVisible(special,m,0))throw Error('visible special lost app');
if(windowVisible(special,m,0,0))throw Error('special close event ignored');
m.activeSpecialWorkspace.id=0;
if(windowVisible(special,m,0))throw Error('closing special retained app');
if(!windowVisible({workspace:{id:2}},m,0))throw Error('regular app lost');
if(windowVisible({workspace:{id:1}},m,0))throw Error('foreign regular app retained');
if(windowVisible({workspace:{id:2},hidden:true},m,0))throw Error('hidden app retained');
'''
  subprocess.run(['node','-e',source+cases],check=True)
if __name__=='__main__':unittest.main()
