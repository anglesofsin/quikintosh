import json,shutil,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(shutil.which('node'),'Node.js required for JS policy checks')
class FocusPolicy(unittest.TestCase):
 def test_profile_rules_and_overnight_schedule(self):
  source=(ROOT/'modules/lickintosh/focus/FocusPolicy.js').read_text()
  case=r'''
const assert=require('assert');
let p={appMode:'allow',apps:'Discord, Spotify',peopleMode:'allow',people:'Alice',allowCritical:true,timeSensitive:false};
assert(permits(p,'discord','',false,false));assert(!permits(p,'Other','',false,false));
assert(permits(p,'Other','Alice',false,false));assert(permits(p,'Other','',true,false));
p.appMode='silence';assert(!permits(p,'Spotify','',false,false));assert(permits(p,'Other','',false,false));
p.peopleMode='silence';assert(!permits(p,'Other','Alice',false,false));
p.timeSensitive=true;assert(permits(p,'Spotify','',false,true));
p={schedule:true,start:'22:00',end:'07:00',days:[1]};
assert(scheduled(p,new Date(2026,10,23,23,0)));assert(scheduled(p,new Date(2026,10,24,6,0)));
assert(!scheduled(p,new Date(2026,10,24,8,0)));assert(!scheduled(p,new Date(2026,10,24,23,0)));
p.start='junk';assert(!scheduled(p,new Date()));p.start='25:00';assert(!scheduled(p,new Date()));
'''
  subprocess.run(['node','-e',source+'\n'+case],check=True,capture_output=True,text=True)
if __name__=='__main__':unittest.main()
