from pathlib import Path
import importlib.util,json,unittest,tempfile,types
spec=importlib.util.spec_from_file_location('glass',Path(__file__).resolve().parents[1]/'modules/lickintosh/compositor/native_glass.py')
glass=importlib.util.module_from_spec(spec);spec.loader.exec_module(glass)
class Api:
 @staticmethod
 def lua(v):
  if isinstance(v,dict):return '{'+','.join('['+json.dumps(k)+']='+Api.lua(x) for k,x in v.items())+'}'
  if isinstance(v,bool):return 'true' if v else 'false'
  return json.dumps(v)
class GlassTests(unittest.TestCase):
 def test_strict_profiles(self):
  for values in [{'native-glass:anything:enabled':True},{'native-glass:windows:blur_strength':float('nan')},{'native-glass:windows:tint_color':-1},{'native-glass:windows:enabled':1}]:
   with self.assertRaises(ValueError):glass.validate(values)
 def test_customization_keeps_other_native_surfaces(self):
  cmd=glass.commands(Api,{'native-glass:menus:blur_strength':.7})
  for ns in ['quickshell:dock','quickintosh-island-dashboard','quickintosh-quickshot-controls','quickintosh-sharing-panel','quickshell:applemenu']:self.assertIn(json.dumps(ns),cmd)
  self.assertNotIn('quickshell:desktop',cmd)
 def test_removing_windows_profile_restores_live_default(self):
  cmd=glass.commands(Api,{},['windows','menus'])
  self.assertIn('background_cache=false',cmd)
  self.assertIn('"quickshell:dock"',cmd)
  self.assertNotIn('quickintosh-ui-menus',cmd)
 def test_color_preserves_full_rgba(self):
  self.assertEqual(glass.validate({'native-glass:dock:tint_color':0xffffff80})['dock']['tint_color'],0xffffff80)
 def test_menubar_is_blur_only_and_island_live(self):
  cmd=glass.commands(Api,{'native-glass:menubar:enabled':True,'native-glass:menubar:refraction_strength':2})
  self.assertIn('"refraction_strength"]=0',cmd)
  self.assertIn('"lens_distortion"]=0',cmd)
  self.assertIn('"live_resample"]=true',cmd)
 def test_profiles_are_committed_by_real_reload_only_when_changed(self):
  with tempfile.TemporaryDirectory() as tmp:
   calls=[]
   api=types.SimpleNamespace(STATE=Path(tmp),os=types.SimpleNamespace(environ={'HYPRLAND_INSTANCE_SIGNATURE':'qa'}),lua=Api.lua,write_json=lambda path,value:path.write_text(json.dumps(value)))
   def run(args):calls.append(args);return 'ok' if args[1]=='reload' else ''
   api.run=run
   values={'native-glass:menubar:blur_strength':2}
   glass.apply(api,values)
   include=Path(tmp)/'native-glass-config.lua'
   self.assertIn('quickintosh-ui-menubar',include.read_text())
   self.assertEqual(calls.count(['hyprctl','reload']),1)
   self.assertFalse(any('eval' in call for call in calls))
   glass.apply(api,dict(values));self.assertEqual(calls.count(['hyprctl','reload']),1)
   glass.apply(api,{'native-glass:menubar:blur_strength':3});self.assertEqual(calls.count(['hyprctl','reload']),2)
   glass.apply(api,{},restore=True);self.assertFalse(include.exists());self.assertEqual(calls.count(['hyprctl','reload']),3)
 def test_failed_reload_restores_previous_profile_file(self):
  with tempfile.TemporaryDirectory() as tmp:
   include=Path(tmp)/'native-glass-config.lua';include.write_text('-- previous valid include')
   calls=[]
   def run(args):
    calls.append(args)
    if args==['hyprctl','reload'] and calls.count(args)==1:raise RuntimeError('reload failed')
    return ''
   api=types.SimpleNamespace(STATE=Path(tmp),os=types.SimpleNamespace(environ={}),lua=Api.lua,run=run,write_json=lambda *_:None)
   with self.assertRaises(RuntimeError):glass.apply(api,{'native-glass:menubar:enabled':True})
   self.assertEqual(include.read_text(),'-- previous valid include')
   self.assertEqual(calls.count(['hyprctl','reload']),2)
if __name__=='__main__':unittest.main()
