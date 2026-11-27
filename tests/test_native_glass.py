from pathlib import Path
import importlib.util,json,unittest
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
if __name__=='__main__':unittest.main()
