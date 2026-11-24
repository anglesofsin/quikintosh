"""Activation tests use a throwaway home and bundle, never the current session."""
import importlib.util,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('arch_install',ROOT/'arch/install.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
spec=importlib.util.spec_from_file_location('arch_launcher',ROOT/'arch/launcher.py');launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(launcher)
class Install(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.base=Path(self.temp.name);self.home=self.base/'home';self.home.mkdir();self.bundle=self.base/'bundle'
  for name in ['runtime/bin','runtime/share/applications','hypr','scripts','config']:(self.bundle/name).mkdir(parents=True)
  for name in ['lickintosh','Hyprland']:(self.bundle/'runtime/bin'/name).write_text('#!/bin/sh\n')
  (self.bundle/'hypr/hyprland.lua').write_text('local rice="/run/current-system/sw/bin/rice-shell"\nlocal f=dofile(os.getenv("HOME") .. "/.config/hypr/remember-floating.lua")\nlocal s="/home/demo/scripts/test.sh"\nlocal state="/home/demo/.local/state/nixos-rice/active-shell"\n')
  (self.bundle/'scripts/test.sh').write_text('#!/bin/sh\necho /home/demo\n/home/demo/scripts/other.sh\n/run/current-system/sw/bin/hyprctl version\n')
  (self.bundle/'config/shells.json').write_text('{"default":"noctalia","shells":{}}')
  (self.bundle/'config/rices.json').write_text('{}')
 def test_private_config_and_roundtrip_backup(self):
  old=self.home/'.local/bin/quickintosh';old.parent.mkdir(parents=True);old.write_text('existing\n')
  hypr=self.home/'.config/hypr/hyprland.conf';hypr.parent.mkdir(parents=True);hypr.write_text('do not change')
  a=mod.Activation(self.home);a.activate(self.bundle)
  config=(self.home/'.config/quickintosh/hypr/hyprland.lua').read_text()
  self.assertNotIn('/run/current-system',config);self.assertNotIn('/home/demo',config)
  self.assertIn('dofile("'+str(self.home)+'/.config/quickintosh/hypr/remember-floating.lua")',config)
  self.assertEqual(hypr.read_text(),'do not change');self.assertTrue((a.root/'bin/quickintosh').exists())
  self.assertIn(str(a.root/'scripts/other.sh'),(a.root/'scripts/test.sh').read_text())
  self.assertNotIn('/run/current-system',(a.root/'scripts/test.sh').read_text())
  a.uninstall();self.assertEqual(old.read_text(),'existing\n');self.assertEqual(hypr.read_text(),'do not change')
 def test_modified_file_not_deleted(self):
  a=mod.Activation(self.home);a.activate(self.bundle)
  file=self.home/'.local/bin/quickintosh';file.write_text('my edit')
  a.uninstall();self.assertEqual(file.read_text(),'my edit')
 def test_reinstall_preserves_original_backup(self):
  old=self.home/'.local/bin/quickintosh';old.parent.mkdir(parents=True);old.write_text('original')
  mod.Activation(self.home).activate(self.bundle);mod.Activation(self.home).activate(self.bundle)
  mod.Activation(self.home).uninstall();self.assertEqual(old.read_text(),'original')
 def test_failed_activation_rolls_back(self):
  a=mod.Activation(self.home);original=a.put
  def fail(path,*args,**kwargs):
   if path.name=='launcher.py':raise ValueError('simulated failure')
   return original(path,*args,**kwargs)
  with patch.object(a,'put',side_effect=fail),self.assertRaises(ValueError):a.activate(self.bundle)
  self.assertFalse((self.home/'.config/quickintosh/hypr/hyprland.lua').exists())
  self.assertEqual(json.loads(a.record.read_text())['files'],{})
 def test_runtime_cleans_foreign_qt_and_keeps_host_apps(self):
  with patch.dict(os.environ,{'QT_PLUGIN_PATH':'/host/qt','PATH':'/usr/bin:/bin'}):env=launcher.environment(self.bundle)
  self.assertNotIn('QT_PLUGIN_PATH',env);self.assertIn('/usr/bin:/bin',env['PATH'])
  self.assertEqual(env['QUICKINTOSH_PLATFORM'],'arch')
 def test_gui_cannot_start_inside_another_session(self):
  a=mod.Activation(self.home);a.activate(self.bundle)
  with patch.object(launcher,'STATE',a.state),patch.dict(os.environ,{'QUICKINTOSH_SESSION':'','XDG_CURRENT_DESKTOP':'OtherDesktop'}):
   with self.assertRaises(RuntimeError):launcher.main(['lickintosh'])
   with self.assertRaises(RuntimeError):launcher.main(['rice-shell','switch','quickintosh'])
 def test_graphics_missing_fails_explicitly(self):
  with self.assertRaises(RuntimeError):launcher.graphics_command(['test'],{'graphics':str(self.bundle)})
class Pam(unittest.TestCase):
 def test_host_modules_absolute_and_includes_preserved(self):
  spec=importlib.util.spec_from_file_location('pam_setup',ROOT/'arch/pam_setup.py');pam=importlib.util.module_from_spec(spec);spec.loader.exec_module(pam)
  with tempfile.TemporaryDirectory() as d:
   base=Path(d);modules=base/'modules';modules.mkdir()
   (modules/'pam_unix.so').touch();(modules/'pam_deny.so').touch()
   (base/'system-auth').write_text('auth [success=1 default=bad] pam_unix.so try_first_pass\naccount include child\n')
   (base/'child').write_text('account required pam_deny.so\n')
   result=pam.build_policies(base,modules)
   self.assertIn(str(modules/'pam_unix.so'),result['quickintosh-system-auth'])
   self.assertIn('account include quickintosh-child',result['quickintosh-system-auth'])
   self.assertIn('[success=1 default=bad]',result['quickintosh-system-auth'])
if __name__=='__main__':unittest.main()

