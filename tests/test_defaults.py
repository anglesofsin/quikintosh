import json,os,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Defaults(unittest.TestCase):
 def test_seed_preserves_existing_preferences(self):
  with tempfile.TemporaryDirectory() as directory:
   env=dict(os.environ,HOME=directory)
   command=['python3',str(ROOT/'scripts/setup-defaults.py'),str(ROOT/'defaults'),'/example.jpg']
   subprocess.run(command,env=env,check=True)
   path=Path(directory)/'.config/lickintosh/shell-config.json'
   value=json.loads(path.read_text());self.assertEqual(value['wallpaper']['path'],'/example.jpg')
   self.assertEqual(value['capture']['directory'],'~/Desktop')
   path.write_text('{"custom":true}');subprocess.run(command,env=env,check=True)
   self.assertEqual(json.loads(path.read_text()),{'custom':True})
if __name__=='__main__':unittest.main()
