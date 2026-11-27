import unittest,subprocess
from unittest.mock import patch,Mock
from translate_backend import translate
class TranslationTests(unittest.TestCase):
 @patch('translate_backend.shutil.which',return_value='/mock/trans')
 @patch('translate_backend.subprocess.Popen')
 def test_stdin_and_success(self,run,which):
  run.return_value=Mock(returncode=0);run.return_value.communicate.return_value=('Bom dia\n','');run.return_value.poll.return_value=0
  self.assertEqual(translate({'text':'Good morning','source':'en','target':'pt'})['text'],'Bom dia')
  self.assertNotIn('Good morning',run.call_args.args[0]);run.return_value.communicate.assert_called_once_with('Good morning',timeout=25)
 def test_validation(self):
  for event in [{'text':''},{'text':'x'*10001},{'text':'hello','target':'pt;touch /tmp/no'},{'text':'hello','target':'auto'}]:
   with self.assertRaises(ValueError):translate(event)
 @patch('translate_backend.shutil.which',return_value='/mock/trans')
 @patch('translate_backend.subprocess.Popen')
 def test_provider_failure(self,run,which):
  run.return_value=Mock(returncode=1);run.return_value.communicate.return_value=('','');run.return_value.poll.return_value=1
  with self.assertRaises(ValueError):translate({'text':'hello'})
if __name__=='__main__':unittest.main()
