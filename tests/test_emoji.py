import json,runpy,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'modules/lickintosh/emoji'
class Emoji(unittest.TestCase):
 def test_catalog_search_sequences_and_skin_tones(self):
  data=json.loads((SOURCE/'catalog.json').read_text());items=data['items']
  self.assertGreater(len(items),1800)
  self.assertEqual(len({e['emoji'] for e in items}),len(items))
  thumbs=next(e for e in items if e['emoji']=='👍');self.assertEqual(thumbs['tones']['3'],'👍🏽')
  heart=next(e for e in items if e['emoji']=='❤️');self.assertIn('coracao',heart['search'])
  self.assertEqual(next(e for e in items if e['emoji']=='❤️‍🔥')['group'],0)
 def test_paste_validates_original_target_and_uses_terminal_shortcut(self):
  for app,target,expected in [('kitty','0x1234','CTRL SHIFT'),('firefox','0x1234','CTRL'),('firefox','0x5678',None)]:
   calls=[]
   def run(command,**kwargs):calls.append((command,kwargs));return type('Result',(),{'returncode':0,'stdout':'ok'})()
   with patch.object(sys,'argv',['paste.py','👍🏽',target]),patch('subprocess.run',side_effect=run),patch('subprocess.check_output',return_value=json.dumps({'address':'0x1234','class':app})),patch('time.sleep'):
    try:runpy.run_path(str(SOURCE/'paste.py'),run_name='__main__')
    except SystemExit as e:self.assertEqual(e.code,0)
   self.assertEqual(calls[0][0][0],'wl-copy');self.assertEqual(calls[0][1]['input'],'👍🏽'.encode())
   if expected:
    self.assertEqual(len(calls),2);self.assertIn('mods="'+expected+'"',calls[1][0][-1]);self.assertIn('state="up"',calls[1][0][-1])
   else:self.assertEqual(len(calls),1)
 def test_invalid_target_copies_without_sending_keys(self):
  with patch.object(sys,'argv',['paste.py','❤️','0x1";os.exit()']),patch('subprocess.run') as run:
   with self.assertRaises(SystemExit):runpy.run_path(str(SOURCE/'paste.py'),run_name='__main__')
   self.assertEqual(run.call_count,1)
if __name__=='__main__':unittest.main()
