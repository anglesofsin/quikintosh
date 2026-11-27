"""Desktop menu ownership uses the actual visible special workspace."""
from pathlib import Path
import subprocess,shutil,unittest
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(shutil.which('node'),'Node required for policy test')
class Focus(unittest.TestCase):
 def test_special_open_close_and_stale_active_window(self):
  source=(ROOT/'modules/lickintosh/finder-menus/DesktopFocus.js').read_text()
  cases='''
const m={activeWorkspace:{id:2},activeSpecialWorkspace:{id:0}};
const special={workspace:{id:-98},mapped:true};
if(windowVisible(special,m,0))throw Error('closed special retained app');
m.activeSpecialWorkspace.id=-98;
if(!windowVisible(special,m,0))throw Error('visible special lost app');
m.activeSpecialWorkspace.id=0;
if(windowVisible(special,m,0))throw Error('closing special retained app');
if(!windowVisible({workspace:{id:2}},m,0))throw Error('regular app lost');
if(windowVisible({workspace:{id:1}},m,0))throw Error('foreign regular app retained');
if(windowVisible({workspace:{id:2},hidden:true},m,0))throw Error('hidden app retained');
'''
  subprocess.run(['node','-e',source+cases],check=True)
if __name__=='__main__':unittest.main()
