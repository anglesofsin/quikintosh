"""Corner updates must submit all native presets and layer registrations."""
from pathlib import Path
import importlib.util,json,unittest
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
corners=module('corners',ROOT/'modules/lickintosh/corners/menu-corners.py')
glass=module('glass',ROOT/'modules/lickintosh/compositor/native_glass.py')
class Api:
 @staticmethod
 def lua(v):
  if isinstance(v,dict):return '{'+','.join('['+json.dumps(k)+']='+Api.lua(x) for k,x in v.items())+'}'
  if isinstance(v,bool):return 'true' if v else 'false'
  return json.dumps(v)
class Registry(unittest.TestCase):
 def test_preserve_profiles_and_baseline(self):
  values={'native-glass:menubar:enabled':True,'native-glass:menubar:blur_strength':2,'native-glass:windows:refraction_strength':1.5}
  cmd=corners.command(Api,glass,5,True,values,['menubar','windows'])
  for name in ['quickintosh-dock','quickintosh-ui-menubar','quickintosh-ui-windows','quickshell','quickshell:dock']:self.assertIn(name,cmd)
  self.assertIn('rounding=5',cmd)
 def test_empty_profiles_still_keep_native_baseline(self):
  cmd=corners.command(Api,glass,0,False,{},[])
  self.assertIn('hl.plugin.hyprglass.preset',cmd);self.assertIn('hl.plugin.hyprglass.layer',cmd)
 def test_invalid_arguments(self):
  for radius in [-1,25,True,1.5,'5']:
   with self.assertRaises(ValueError):corners.command(Api,glass,radius,True,{},[])
if __name__=='__main__':unittest.main()
