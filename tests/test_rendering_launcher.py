from pathlib import Path
import json,os,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class RendererLauncher(unittest.TestCase):
 def test_only_known_renderer_values_leave_the_launcher(self):
  with tempfile.TemporaryDirectory() as directory:
   config=Path(directory)/'.config/lickintosh/shell-config.json';config.parent.mkdir(parents=True)
   for value,expected in [(None,'auto'),({},'auto'),({'performance':{'renderer':'threaded'}},'threaded'),({'performance':{'renderer':'basic'}},'basic'),({'performance':{'renderer':'$(touch BAD)'}},'auto'),({'performance':[]},'auto'),([],'auto')]:
    config.write_text(json.dumps(value))
    result=subprocess.run(['python3',str(ROOT/'modules/lickintosh/rendering/launcher-env.py')],env=dict(os.environ,HOME=directory),capture_output=True,text=True,check=True)
    self.assertEqual(result.stdout.strip(),expected)
if __name__=='__main__':unittest.main()
