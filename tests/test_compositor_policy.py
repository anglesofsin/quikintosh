import importlib.util,unittest,math
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'modules/lickintosh/compositor/options.py'
spec=importlib.util.spec_from_file_location('policy',p);policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
class CompositorPolicy(unittest.TestCase):
 def test_four_sided_spacing_restores_as_lua_table(self):
  self.assertEqual(policy.option_value('general:gaps_in','1 2 3 4'),dict(top=1,right=2,bottom=3,left=4))
  self.assertEqual(policy.option_value('general:gaps_out','5 9'),dict(top=5,right=9,bottom=5,left=9))
 def test_unicode_titles_are_valid_lua_strings(self):
  command=policy.rule_commands([{'app':'kitty','title':'Olá'}])
  self.assertIn('Olá',command)
  self.assertNotIn('\\u00',command)
  with self.assertRaises(ValueError):policy.rule_commands([{'app':'bad\nclass'}])
 def test_typed_bounds_and_no_nan(self):
  for value in [float('nan'),float('inf'),True,-1,2]:
   with self.assertRaises(ValueError):policy.typed(value,('number',0,1))
 def test_exact_class_and_title_are_lua_data(self):
  table=policy.rule_table({'app':'kitty[1]";os.exit()','title':'a.*','activeOpacity':.8,'noBlur':False},0)
  self.assertEqual(table['match']['title'],'^a\\.\\*$')
  command=policy.rule_commands([{'app':'kitty','noBlur':True}],3)
  self.assertIn('"enabled"]=false',command)
  self.assertIn('"no_blur"]=true',command)
  with self.assertRaises(ValueError):policy.rule_commands([{'app':''}])
if __name__=='__main__':unittest.main()
