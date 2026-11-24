from pathlib import Path
import json
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class SpecialWorkspaces(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.scripts=self.root/'scripts with spaces'
        self.scripts.mkdir()
        for name in ['special-toggle.sh','toggle-special-left.sh','toggle-special-right.sh','toggle-special-public.sh','toggle-special-scratchpad.sh']:
            shutil.copy(ROOT/'modules/infinite-desktop'/name,self.scripts/name)
        binary=self.root/'bin';binary.mkdir()
        (binary/'hyprctl').write_text('''#!/usr/bin/env python3
import json,os,sys
with open(os.environ['FIXTURE_LOG'],'a') as f:f.write(json.dumps(sys.argv[1:])+'\\n')
if sys.argv[1:]==['monitors','-j']:
 print(json.dumps([{'focused':True,'specialWorkspace':{'name':os.environ.get('FIXTURE_OUTGOING','')}}]))
''')
        (binary/'hyprctl').chmod(0o755)
        self.log=self.root/'calls.jsonl'
        self.env=dict(os.environ,PATH=str(binary)+':'+os.environ['PATH'],FIXTURE_LOG=str(self.log))

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_all_four_shortcuts_dispatch_from_a_portable_path(self):
        for suffix,workspace in [('left','left'),('right','right'),('public','public'),('scratchpad','special')]:
            self.log.unlink(missing_ok=True)
            subprocess.run(['bash',str(self.scripts/('toggle-special-'+suffix+'.sh'))],env=self.env,check=True)
            commands=[row[1] for row in self.calls() if row[0]=='dispatch']
            self.assertEqual(commands,['hl.dsp.workspace.toggle_special("'+workspace+'")'])

    def test_switch_closes_outgoing_before_opening_target(self):
        self.env['FIXTURE_OUTGOING']='special:left'
        subprocess.run(['bash',str(self.scripts/'toggle-special-right.sh')],env=self.env,check=True)
        commands=[row[1] for row in self.calls() if row[0]=='dispatch']
        self.assertEqual(commands,['hl.dsp.workspace.toggle_special("left")','hl.dsp.workspace.toggle_special("right")'])

    def test_unknown_target_fails_before_any_dispatch(self):
        p=subprocess.run(['bash',str(self.scripts/'special-toggle.sh'),'unknown'],env=self.env,capture_output=True)
        self.assertNotEqual(p.returncode,0)
        self.assertFalse(self.log.exists())

if __name__=='__main__':unittest.main()
