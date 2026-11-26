import json,os,subprocess,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/'modules/infinite-desktop/toggle-stream-hide.sh'
class StreamShortcuts(unittest.TestCase):
 def test_typed_lua_and_state_updates_only_after_success(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);bin=root/'bin';bin.mkdir()
   mock=bin/'hyprctl';mock.write_text('''#!/usr/bin/env python3
import os,sys,json
from pathlib import Path
if sys.argv[1]=='monitors':print(json.dumps([{'focused':True,'specialWorkspace':{'name':'special:Olá'}}]))
else:
 Path(os.environ['HOME'],'lua').write_text(sys.argv[2])
 print('error: rejected' if os.environ.get('REJECT') else 'ok')
''');mock.chmod(0o755)
   env=dict(os.environ,HOME=directory,PATH=str(bin)+':'+os.environ['PATH'])
   subprocess.run(['bash',str(SCRIPT),'hide'],env=env,check=True)
   state=root/'.local/state/infinite-desktop/stream-hidden'
   self.assertEqual(state.read_text(),'special:Olá\n')
   self.assertIn('value="1"',(root/'lua').read_text())
   self.assertIn('\\195\\161',(root/'lua').read_text())
   failed=subprocess.run(['bash',str(SCRIPT),'show'],env=dict(env,REJECT='1'),capture_output=True)
   self.assertNotEqual(failed.returncode,0);self.assertEqual(state.read_text(),'special:Olá\n')
   subprocess.run(['bash',str(SCRIPT),'show'],env=env,check=True)
   self.assertEqual(state.read_text(),'');self.assertIn('value="0"',(root/'lua').read_text())
if __name__=='__main__':unittest.main()
