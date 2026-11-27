"""Corners must not enqueue material declarations outside a real reload."""
from pathlib import Path
import importlib.util,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('corners',ROOT/'modules/lickintosh/corners/menu-corners.py')
corners=importlib.util.module_from_spec(spec);spec.loader.exec_module(corners)
class Registry(unittest.TestCase):
 def test_corner_update_does_not_enqueue_materials(self):
  cmd=corners.command(5,True)
  self.assertNotIn('hyprglass',cmd);self.assertIn('rounding=5',cmd);self.assertIn('enabled=true',cmd)
 def test_disabling_corner_policy(self):
  cmd=corners.command(0,False);self.assertIn('enabled=false',cmd)
 def test_invalid_arguments(self):
  for radius in [-1,25,True,1.5,'5']:
   with self.assertRaises(ValueError):corners.command(radius,True)
if __name__=='__main__':unittest.main()
