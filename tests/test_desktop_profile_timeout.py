import ast,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
class ProfileTimeout(unittest.TestCase):
 def test_unavailable_theme_service_does_not_abort_login(self):
  tree=ast.parse((Path(__file__).resolve().parents[1]/'modules/lickintosh/desktop-profile.py').read_text())
  function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
  import sys
  scope={'subprocess':subprocess,'sys':sys}
  exec(compile(ast.Module(body=[function],type_ignores=[]),'profile-run','exec'),scope)
  for error in [subprocess.TimeoutExpired('gsettings',3),FileNotFoundError('gsettings')]:
   with patch.object(subprocess,'run',side_effect=error):
    result=scope['run']('gsettings','set','schema','key','value')
    self.assertEqual(result.returncode,124);self.assertEqual(result.stdout,'')
if __name__=='__main__':unittest.main()
