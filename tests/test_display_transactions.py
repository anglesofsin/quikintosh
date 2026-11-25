"""Display mutations use a fake compositor; never alter the test machine's outputs."""
import importlib.util,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('displays',Path(__file__).resolve().parents[1]/'modules/lickintosh/display-wallpaper/displays.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
class Displays(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.old=d.ROOT;d.ROOT=Path(self.tmp.name);self.addCleanup(setattr,d,'ROOT',self.old)
  self.raw=[dict(name='DP-1',width=1920,height=1080,refreshRate=60,x=0,y=0,scale=1),dict(name='HDMI-A-1',width=2560,height=1440,refreshRate=144,x=1920,y=0,scale=1.25)]
  self.specs=[d.spec(m) for m in self.raw]
 def test_validation_rejects_black_screen_mirror_cycle_and_bad_values(self):
  for change in [lambda s:[x.update(disabled=True) for x in s],lambda s:[x.update(mirror=s[1-i]['output']) for i,x in enumerate(s)],lambda s:s[0].update(scale=float('nan')),lambda s:s[0].update(mode='1920x1080");os.execute("bad")'),lambda s:s.pop()]:
   s=[x.copy() for x in self.specs];change(s)
   with self.assertRaises(ValueError):d.validate(s,self.raw)
 def test_confirmation_is_required_before_persisting(self):
  with patch.object(d,'monitors',return_value=self.raw),patch.object(d,'apply') as apply,patch.object(d.subprocess,'Popen'):
   result=d.command({'action':'preview','specs':self.specs});token=result['pending']['token']
   self.assertFalse((d.ROOT/'saved.json').exists());self.assertTrue((d.ROOT/'pending.json').exists());apply.assert_called_once()
   d.command({'action':'confirm','token':token});self.assertFalse((d.ROOT/'pending.json').exists());self.assertEqual(d.read(d.ROOT/'saved.json')['specs'],self.specs)
 def test_watchdog_restores_original_configuration(self):
  with patch.object(d,'monitors',return_value=self.raw),patch.object(d,'apply') as apply,patch.object(d.subprocess,'Popen'),patch.object(d.time,'sleep'):
   result=d.command({'action':'preview','specs':self.specs});d.watchdog(result['pending']['token'])
   self.assertEqual(apply.call_count,2);self.assertEqual(apply.call_args.args[0],self.specs);self.assertFalse((d.ROOT/'pending.json').exists())
 def test_failed_apply_rolls_back(self):
  with patch.object(d,'monitors',return_value=self.raw),patch.object(d,'apply',side_effect=[ValueError('rejected'),None]) as apply,patch.object(d.subprocess,'Popen'):
   with self.assertRaises(ValueError):d.command({'action':'preview','specs':self.specs})
   self.assertEqual(apply.call_count,2);self.assertFalse((d.ROOT/'pending.json').exists())
 def test_restore_ignores_unmatched_connectors(self):
  d.atomic(d.ROOT/'saved.json',{'specs':[self.specs[0]]})
  with patch.object(d,'monitors',return_value=self.raw),patch.object(d,'apply') as apply:d.command({'action':'restore'});apply.assert_not_called()
 def test_profiles_are_persistent_and_deletable(self):
  with patch.object(d,'monitors',return_value=self.raw):
   result=d.command({'action':'save-profile','name':'Desk','specs':self.specs});self.assertEqual(result['profiles']['Desk'],self.specs)
   self.assertEqual(d.command({'action':'delete-profile','name':'Desk'})['profiles'],{})
if __name__=='__main__':unittest.main()
