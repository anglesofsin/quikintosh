"""Offline toolkit correctness and persistence, without a desktop clipboard."""
import sys,json,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'modules/lickintosh/island-shelf'))
from developer_tools import transform
from backend import Shelf

class DeveloperToolsTests(unittest.TestCase):
 def test_unicode_roundtrip(self):
  text='Olá 👋\nSão Paulo'
  self.assertEqual(transform(transform(text,'base64'),'unbase64'),text)
  self.assertEqual(transform(transform(text,'url'),'unurl'),text)
 def test_json_and_hash(self):
  self.assertEqual(transform('{ "a": 1 }','minify'),'{"a":1}')
  self.assertEqual(json.loads(transform('{"a":1}','json')),{'a':1})
  self.assertEqual(transform('hello','sha256'),'2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824')
 def test_invalid_input_returns_error(self):
  with tempfile.TemporaryDirectory() as root:
   event=Shelf(root).handle({'action':'developerTool','operation':'jwt','text':'nope'})
   self.assertTrue(event['error']);self.assertEqual(event['text'],'')
 def test_jwt_never_claims_verification(self):
  token='eyJhbGciOiJub25lIn0.eyJzdWIiOiIxIn0.'
  result=json.loads(transform(token,'jwt'))
  self.assertEqual(result['payload'],{'sub':'1'});self.assertIs(result['signatureVerified'],False)
 def test_limits(self):
  with self.assertRaises(ValueError):transform('x'*1048577,'json')
  with self.assertRaises(ValueError):transform('', 'exec')
 def test_widget_recency_is_unique_and_persistent(self):
  with tempfile.TemporaryDirectory() as root:
   Shelf(root).handle({'action':'utilityPreferences','values':{'widgetRecent':['notes','media','notes','weather']}})
   self.assertEqual(Shelf(root).handle({'action':'utilityPreferences'})['values']['widgetRecent'],['notes','media','weather'])
 def test_command_preferences(self):
  with tempfile.TemporaryDirectory() as root:
   result=Shelf(root).handle({'action':'utilityPreferences','values':{'commandColumns':5,'commandFavorites':['calculator','notes']}})
   self.assertEqual(result['values']['commandColumns'],5);self.assertEqual(result['values']['commandFavorites'],['calculator','notes'])
 def test_break_settings_are_bounded(self):
  with tempfile.TemporaryDirectory() as root:
   result=Shelf(root).handle({'action':'utilityPreferences','values':{'breaksEnabled':True,'eyesMinutes':999,'waterMinutes':-4}})
   self.assertEqual(result['values'],{'breaksEnabled':True,'eyesMinutes':240,'waterMinutes':5})
 def test_script_persists(self):
  with tempfile.TemporaryDirectory() as root:
   shelf=Shelf(root);shelf.handle({'action':'utilityPreferences','values':{'teleprompterText':'script ☀'}})
   self.assertEqual(Shelf(root).handle({'action':'utilityPreferences'})['values'],{'teleprompterText':'script ☀'})

class ApplicationCleanupTests(unittest.TestCase):
 def test_personal_data_is_opt_in_and_scoped(self):
  from unittest.mock import patch
  from types import SimpleNamespace
  with tempfile.TemporaryDirectory() as home,tempfile.TemporaryDirectory() as state:
   folder=Path(home)/'.var/app/org.example.Test';folder.mkdir(parents=True);(folder/'note.txt').write_text('keep me')
   shelf=Shelf(state);row=dict(id='org.example.Test',kind='flatpak',removable=True)
   shelf.applications=lambda event=None:dict(type='applications',items=[row])
   calls=[]
   def runner(args,**kwargs):calls.append(args);return SimpleNamespace(returncode=0,stdout='')
   with patch('app_ops.Path.home',return_value=Path(home)),patch('app_ops.subprocess.run',side_effect=runner):
    review=shelf.application_data({'id':row['id']})
    self.assertEqual(review['items'][0]['path'],str(folder));self.assertEqual(review['items'][0]['size'],7)
    shelf.uninstall({'id':row['id'],'confirmed':True})
    self.assertFalse(any(call[0]=='gio' for call in calls))
    shelf.uninstall({'id':row['id'],'confirmed':True,'removeData':True})
    self.assertEqual(calls[-1],['gio','trash','--',str(folder)])
 def test_cleanup_rejects_symlink_and_unknown_app(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as home,tempfile.TemporaryDirectory() as state,tempfile.TemporaryDirectory() as outside:
   folder=Path(home)/'.var/app';folder.mkdir(parents=True);(folder/'org.example.Test').symlink_to(outside,target_is_directory=True)
   shelf=Shelf(state);shelf.applications=lambda event=None:dict(items=[dict(id='org.example.Test',kind='flatpak',removable=True)])
   with patch('app_ops.Path.home',return_value=Path(home)):
    self.assertEqual(shelf.application_data({'id':'org.example.Test'})['items'],[])
    with self.assertRaises(ValueError):shelf.application_data({'id':'unknown'})

class SelectionBridgeTests(unittest.TestCase):
 def test_transient_text_and_sensitive_clear(self):
  import os,subprocess
  script=Path(__file__).resolve().parents[1]/'modules/lickintosh/island-shelf/selection_bridge.py'
  env=dict(os.environ,CLIPBOARD_STATE='data')
  result=subprocess.run([sys.executable,str(script)],input='Olá selection',text=True,capture_output=True,env=env,check=True)
  self.assertEqual(json.loads(result.stdout),{'text':'Olá selection'})
  env['CLIPBOARD_STATE']='sensitive'
  result=subprocess.run([sys.executable,str(script)],input='not retained',text=True,capture_output=True,env=env,check=True)
  self.assertEqual(json.loads(result.stdout),{'text':''})
 def test_oversized_selection_is_ignored(self):
  import os,subprocess
  script=Path(__file__).resolve().parents[1]/'modules/lickintosh/island-shelf/selection_bridge.py'
  result=subprocess.run([sys.executable,str(script)],input='x'*65537,text=True,capture_output=True,env=dict(os.environ,CLIPBOARD_STATE='data'),check=True)
  self.assertEqual(json.loads(result.stdout),{'text':''})

class RingShortcutTests(unittest.TestCase):
 def test_no_override(self):
  from unittest.mock import patch
  from types import SimpleNamespace
  from ensure_ring_shortcut import ensure
  calls=[]
  def runner(args,**kwargs):calls.append(args);return SimpleNamespace(returncode=0,stdout='[{"modmask":72,"key":"R","description":"Personal"}]')
  with patch.dict('os.environ',{'HYPRLAND_INSTANCE_SIGNATURE':'private-test'}):self.assertFalse(ensure(runner))
  self.assertEqual(len(calls),1)
 def test_paired_default(self):
  from unittest.mock import patch
  from types import SimpleNamespace
  from ensure_ring_shortcut import ensure
  calls=[]
  def runner(args,**kwargs):calls.append(args);return SimpleNamespace(returncode=0,stdout='[]' if args[-1]=='binds' else 'ok')
  with patch.dict('os.environ',{'HYPRLAND_INSTANCE_SIGNATURE':'private-test'}):self.assertTrue(ensure(runner))
  self.assertIn('release=true',calls[-1][-1]);self.assertIn('actionRing show',calls[-1][-1])

class TerminalTests(unittest.TestCase):
 def test_explicit_command_and_exit(self):
  from terminal_backend import run
  events=[];code=run({'command':'printf QUICK_TERMINAL_OK; exit 7'},events.append)
  self.assertEqual(code,7);self.assertIn('QUICK_TERMINAL_OK',''.join(e.get('text','') for e in events))
 def test_reject_empty(self):
  from terminal_backend import run
  with self.assertRaises(ValueError):run({'command':''},lambda _:None)

class FinderBridgeTests(unittest.TestCase):
 def test_local_selection_and_unicode(self):
  from finder_service import selection
  self.assertEqual(selection({},['/tmp/São Paulo.png']),['file:///tmp/S%C3%A3o%20Paulo.png'])
  self.assertEqual(selection({'NAUTILUS_SCRIPT_SELECTED_URIS':'file:///tmp/a%0Ab\nhttps://example.com\nfile://remote/private'},[]),['file:///tmp/a%0Ab'])
 def test_installer_preserves_user_script(self):
  from install_finder_services import install
  with tempfile.TemporaryDirectory() as home:
   folder=Path(home)/'.local/share/nautilus/scripts';folder.mkdir(parents=True)
   target=folder/'Send to Dynamic Island';target.write_text('personal script')
   install('/usr/bin/python3','/tmp/bridge.py',home)
   self.assertEqual(target.read_text(),'personal script')
   floating=folder/'Send to Floating File Tray'
   self.assertIn('--floating',floating.read_text());self.assertTrue(floating.stat().st_mode&0o100)

class VaultTests(unittest.TestCase):
 def test_select_read_save_and_collision(self):
  with tempfile.TemporaryDirectory() as root,tempfile.TemporaryDirectory() as vault:
   note=Path(vault)/'hello.md';note.write_text('original')
   shelf=Shelf(root);result=shelf.handle({'action':'vaultSelect','path':vault})
   self.assertEqual(result['notes'][0]['name'],'hello.md')
   initial=shelf.handle({'action':'vaultRead','name':'hello.md'})
   shelf.handle({'action':'vaultSave','name':'hello.md','modified':initial['modified'],'text':'edited'})
   self.assertEqual(note.read_text(),'edited')
   with self.assertRaises(ValueError):shelf.handle({'action':'vaultSave','name':'hello.md','modified':initial['modified'],'text':'stale'})
 def test_vault_cannot_escape(self):
  with tempfile.TemporaryDirectory() as root,tempfile.TemporaryDirectory() as vault:
   shelf=Shelf(root);shelf.handle({'action':'vaultSelect','path':vault})
   for name in ['../secret.md','/etc/passwd','note.txt']:
    with self.assertRaises(ValueError):shelf.handle({'action':'vaultRead','name':name})
   (Path(vault)/'escape.md').symlink_to('/etc/passwd')
   with self.assertRaises(ValueError):shelf.handle({'action':'vaultRead','name':'escape.md'})

if __name__=='__main__':unittest.main()
