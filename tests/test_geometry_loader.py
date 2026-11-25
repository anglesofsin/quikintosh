"""Upgrade only Quickintosh telemetry, using a fake hyprctl and private runtime."""
from pathlib import Path
import json,os,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class GeometryLoader(unittest.TestCase):
 def test_old_library_path_is_used_instead_of_plugin_handle(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);binary=root/'hyprctl';events=root/'events.jsonl';record=root/'quickintosh-geometry.path'
   old='/nix/store/old-quickintosh/lib/quickintosh-geometry.so';new='/nix/store/new-quickintosh/lib/quickintosh-geometry.so'
   record.write_text(old)
   binary.write_text('''#!/usr/bin/env python3
import json,os,sys
args=sys.argv[1:]
with open(os.environ['QI_TEST_EVENTS'],'a') as f:f.write(json.dumps(args)+'\\n')
if args==['plugins','list','-j']:print(json.dumps([{'name':'other','version':'0.1','handle':'OTHER'},{'name':'quickintosh-geometry','version':'1.0.0','handle':'NOT_A_PATH'}]))
elif args[:2]==['plugin','unload']:
 if args[2]!='/nix/store/old-quickintosh/lib/quickintosh-geometry.so':print('plugin not loaded');sys.exit(1)
 print('ok')
elif args[:2]==['plugin','load']:print('ok')
else:sys.exit(2)
''');binary.chmod(0o700)
   env=dict(os.environ,PATH=folder+':'+os.environ['PATH'],XDG_RUNTIME_DIR=folder,HYPRLAND_INSTANCE_SIGNATURE='private-test',QI_TEST_EVENTS=str(events))
   result=subprocess.run(['python3',str(ROOT/'modules/lickintosh/rendering/ensure-geometry.py'),new],env=env,capture_output=True,text=True,check=True)
   self.assertEqual(result.stderr,'')
   self.assertEqual(record.read_text(),new)
   calls=[json.loads(line) for line in events.read_text().splitlines()]
   self.assertEqual([c for c in calls if c[:2]==['plugin','unload']],[['plugin','unload',old]])
   self.assertIn(['plugin','load',new],calls)
if __name__=='__main__':unittest.main()
