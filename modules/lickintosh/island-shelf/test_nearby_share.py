import unittest
from pathlib import Path
from unittest.mock import patch,Mock
from app_ops import AppOperations

class SharingTests(unittest.TestCase):
 def setUp(self):
  self.ops=AppOperations()
  self.ops.managed=lambda paths:[Path('/tmp/fixture-file')]
 @patch('app_ops.subprocess.run')
 @patch('app_ops.shutil.which',return_value='/mock/tool')
 def test_single_reachable_device(self,which,run):
  run.return_value=Mock(stdout='paired-device\n',returncode=0)
  self.assertEqual(self.ops.sharing({'paths':['fixture']})['provider'],'kdeconnect')
  self.assertEqual(run.call_args.args[0],['kdeconnect-cli','--device','paired-device','--share','/tmp/fixture-file'])
 @patch('app_ops.subprocess.run')
 @patch('app_ops.shutil.which',return_value='/mock/tool')
 def test_ambiguous_and_stale_recipients(self,which,run):
  run.return_value=Mock(stdout='one\ntwo\n',returncode=0)
  with self.assertRaises(ValueError):self.ops.sharing({'paths':['fixture']})
  with self.assertRaises(ValueError):self.ops.sharing({'paths':['fixture'],'device':'stale'})
  self.assertEqual(run.call_count,2)
 def test_unknown_provider(self):
  with self.assertRaises(ValueError):self.ops.sharing({'paths':['fixture'],'provider':'unknown'})

if __name__=='__main__':unittest.main()
