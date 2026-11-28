"""Behavioral tests: input validation, restoration and rice isolation."""
import importlib.util
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('settings_backend',Path(__file__).with_name('backend.py'))
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class BackendTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.home=Path(self.temp.name)
  self.patches=[patch.object(b,'HOME',self.home),patch.object(b,'STATE',self.home/'state')]
  for p in self.patches:p.start()
 def tearDown(self):
  for p in reversed(self.patches):p.stop()
  self.temp.cleanup()
 def test_users_include_current_account_when_nss_enumeration_is_empty(self):
  current=b.pwd.getpwuid(os.getuid())
  with patch.object(b.pwd,'getpwall',return_value=[]),patch.object(b.pwd,'getpwuid',return_value=current):
   users=b.users_info()['users']
   self.assertEqual(len(users),1)
   self.assertTrue(users[0]['current'])
   self.assertEqual(users[0]['name'],current.pw_name)
 def test_empty_input_value_is_a_blank_field(self):
  with patch.object(b,'run',return_value='{"option":"input:kb_variant","str":"[[EMPTY]]"}'):
   self.assertEqual(b.input_values(['input:kb_variant'])['input:kb_variant'],'')
 def test_game_mode_is_idempotent_and_validates_boolean(self):
  with patch.object(b,'read',return_value='lickintosh'),patch.object(b,'run',return_value='{"gameMode":true}') as run:
   self.assertTrue(b.action('game-mode',{'enabled':True})['gameMode'])
   self.assertFalse(any(args[0][-1]=='gameMode' for args in run.call_args_list))
   with self.assertRaises(ValueError):b.action('game-mode',{'enabled':'yes'})
 def test_game_mode_changes_only_when_requested_state_differs(self):
  with patch.object(b,'read',return_value='lickintosh'),patch.object(b,'run',side_effect=['{"gameMode":false}','ok','{"gameMode":true}']) as run:
   self.assertTrue(b.action('game-mode',{'enabled':True})['gameMode'])
   self.assertEqual(run.call_args_list[1].args[0][-1],'gameMode')
 def test_escaped_network_names(self):
  self.assertEqual(b.split_nm(r'uuid:Office\: A\\B:vpn:eth0'),['uuid','Office: A\\B','vpn','eth0'])
 def test_permissions_merge_overrides_without_losing_unrelated_grants(self):
  app='org.example.Test'
  def output(args,**kwargs):
   return '[Context]\nshared=!network;\nfilesystems=!xdg-download;\n' if args[1]=='override' else '[Context]\nshared=network;ipc;\nfilesystems=home:ro;xdg-download;\n'
  with patch.object(b,'privacy_info',return_value={'flatpaks':[{'id':app}]}),patch.object(b,'run',side_effect=output):
   result=b.permissions(app)
   self.assertFalse(result['grants']['network']);self.assertTrue(result['grants']['home']);self.assertFalse(result['grants']['downloads'])
   self.assertIn('ipc',result['context']['shared'])
 def test_input_rejects_injection_and_invalid_types(self):
  for key,value in [('input:kb_layout','us");os.execute("oops")'),('input:repeat_rate',True),('input:repeat_delay',100.5),('input:sensitivity',float('nan')),('input:sensitivity',2),('exec','pwd'),('input:natural_scroll','false')]:
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):b.validate_input(key,value)
 def test_lua_typed_options(self):
  with patch.object(b,'run',return_value='ok') as run:
   b.apply_options({'input:touchpad:tap-to-click':True,'input:repeat_rate':30})
   command=run.call_args.args[0]
   self.assertEqual(command[:2],['hyprctl','eval'])
   self.assertIn('["tap_to_click"]=true',command[2]);self.assertIn('["repeat_rate"]=30',command[2])
 def test_input_roundtrip_and_removed_override(self):
  with patch.dict(os.environ,HYPRLAND_INSTANCE_SIGNATURE='test'),patch.object(b,'input_values',return_value={'input:repeat_delay':500}),patch.object(b,'apply_options') as apply:
   b.runtime({'input:repeat_delay':525});b.runtime({})
   self.assertEqual(apply.call_args.args[0],{'input:repeat_delay':500})
   b.runtime(restore=True)
   self.assertFalse((b.STATE/'runtime.json').exists())
 def test_new_compositor_does_not_restore_old_input(self):
  b.write_json(b.STATE/'runtime.json',{'instance':'old','original':{'input:repeat_delay':500},'applied':{'input:repeat_delay':525}})
  with patch.dict(os.environ,HYPRLAND_INSTANCE_SIGNATURE='new'),patch.object(b,'apply_options') as apply:
   b.runtime(restore=True);self.assertEqual(apply.call_args.args[0],{})
 def test_restore_files_bytes_mode_symlink_and_absent(self):
  regular=self.home/'regular';regular.write_bytes(b'original\x00');regular.chmod(0o640)
  link=self.home/'link';link.symlink_to(regular)
  missing=self.home/'missing'
  for path in [regular,link,missing]:b.remember_file(path)
  regular.write_text('changed');link.unlink();link.write_text('changed');missing.write_text('added')
  b.restore_files()
  self.assertEqual(regular.read_bytes(),b'original\x00');self.assertEqual(regular.stat().st_mode&0o777,0o640)
  self.assertTrue(link.is_symlink());self.assertFalse(missing.exists())
 def test_file_preferences_survive_rice_roundtrip(self):
  target=self.home/'setting';target.write_text('other rice')
  b.remember_file(target);target.write_text('lickintosh')
  b.restore_files();self.assertEqual(target.read_text(),'other rice')
  target.write_text('updated other rice')
  b.activate_files();self.assertEqual(target.read_text(),'lickintosh')
  b.restore_files();self.assertEqual(target.read_text(),'updated other rice')
 def test_actions_do_not_affect_other_rices(self):
  with patch.object(b,'read',return_value='noctalia-legacy'),patch.object(b,'runtime') as runtime:
   with self.assertRaises(RuntimeError):b.action('runtime',{'values':{}})
   runtime.assert_not_called()
 def test_usage_is_bounded_and_contains_no_titles(self):
  b.usage_tick('org.example.Editor',10)
  values=b.read_json(b.STATE/'usage.json');self.assertEqual(list(values.values())[0],{'org.example.Editor':10})
  for seconds in [-1,0,121]:
   with self.assertRaises(ValueError):b.usage_tick('org.example.Editor',seconds)
 def test_manual_audio_is_announced_before_changing_volume(self):
  with patch.object(b,'read',return_value='lickintosh'),patch.object(b,'audio_info',return_value={'outputs':[],'inputs':[]}),patch.object(b,'run') as run:
   b.action('audio-volume',{'target':'output','value':.5})
   commands=[call.args[0] for call in run.call_args_list]
   self.assertEqual(commands[0][-3:],['call','audioFeedback','manual'])
   self.assertEqual(commands[1],['wpctl','set-volume','@DEFAULT_AUDIO_SINK@','0.5'])
 def test_server_embedded_password_rejected(self):
  with patch.object(b,'read',return_value='lickintosh'),patch.object(b.subprocess,'Popen') as start:
   for url in ['https://example.org','sftp://user:secret@example.org']:
    with self.assertRaises(ValueError):b.action('open-server',{'url':url})
   start.assert_not_called()

if __name__=='__main__':unittest.main()
