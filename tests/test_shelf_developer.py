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
