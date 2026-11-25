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
 def test_native_workspace_overrides_keep_special_leaves_separate(self):
  from tempfile import TemporaryDirectory
  from types import SimpleNamespace
  import json,os
  with TemporaryDirectory() as state:
   commands=[]
   initial={"name":"workspaces","overridden":True,"bezier":"default","enabled":True,"speed":5,"style":"slide"}
   special=dict(initial,name="specialWorkspaceIn",style="slidevert")
   def run(args):
    if args[1]=="animations":
     return json.dumps([[initial,special],[{"name":"default"}]])
    commands.append(args[-1])
    return "ok"
   def read_json(path):
    return json.loads(path.read_text()) if path.exists() else {}
   api=SimpleNamespace(STATE=Path(state),os=os,run=run,read_json=read_json,
                       write_json=lambda path,data:path.write_text(json.dumps(data)))
   policy.apply_native_workspace(api,{"style":"slidefadevert","speed":2.5,"distance":75,"direction":"top"})
   self.assertIn("slidefadevert top 75%",commands[-1])
   self.assertIn("workspacesIn",commands[-1])
   self.assertIn("workspacesOut",commands[-1])
   self.assertNotIn("specialWorkspace",commands[-1])
   policy.apply_native_workspace(api,{},restore=True)
   self.assertIn('["style"]="slide"',commands[-1])
   self.assertNotIn("specialWorkspace",commands[-1])
 def test_native_open_and_close_are_independent_and_reversible(self):
  from tempfile import TemporaryDirectory
  from types import SimpleNamespace
  import json,os
  with TemporaryDirectory() as state:
   commands=[]
   opening=dict(name='windowsIn',overridden=True,bezier='default',enabled=True,speed=5,style='popin 80%')
   closing=dict(opening,name='windowsOut',style='slide')
   def run(args):
    if args[1]=='animations':return json.dumps([[opening,closing],[{'name':'default'}]])
    commands.append(args[-1]);return 'ok'
   def read_json(path):return json.loads(path.read_text()) if path.exists() else {}
   api=SimpleNamespace(STATE=Path(state),os=os,run=run,read_json=read_json,
    write_json=lambda path,data:path.write_text(json.dumps(data)))
   policy.apply_native_windows(api,{'window-animation:windowsOut:style':'popin','window-animation:windowsOut:amount':70})
   self.assertIn('windowsOut',commands[-1]);self.assertIn('popin 70%',commands[-1])
   self.assertNotIn('windowsIn',commands[-1]);self.assertNotIn('specialWorkspace',commands[-1])
   policy.apply_native_windows(api,{},restore=True)
   self.assertIn('["style"]="slide"',commands[-1])
   self.assertFalse((api.STATE/'window-animation-runtime.json').exists())
if __name__=='__main__':unittest.main()
