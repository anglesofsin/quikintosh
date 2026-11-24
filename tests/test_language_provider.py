"""Real CLD2/ICU model and private IPC checks; run with darling-language's Python."""
import importlib.util
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'modules/lickintosh/mac-apps/language-provider.py'
spec=importlib.util.spec_from_file_location('language_provider',SOURCE)
provider=importlib.util.module_from_spec(spec);spec.loader.exec_module(provider)

try:
    import icu
    import pycld2
    MODEL_AVAILABLE=True
except ImportError:
    MODEL_AVAILABLE=False

@unittest.skipUnless(MODEL_AVAILABLE, 'Use the CLD2/ICU Python environment from darling-language')
class LanguageProvider(unittest.TestCase):
    def test_real_languages_and_empty(self):
        for language,text in [('en','This paragraph describes the everyday lives of people around the world. Science and technology help society find solutions while teachers share knowledge with students.'),('pt','Este texto está escrito em português e descreve a vida das pessoas no Brasil. A ciência e a tecnologia ajudam a sociedade a encontrar soluções para seus desafios.')]:
            self.assertEqual(provider.analyze({'operation':'detect','text':text})['languages'][0][0],language)
        for text in ['', '123!!!']:
            self.assertEqual(provider.analyze({'operation':'detect','text':text})['languages'],[])
    def test_utf16_flags_and_units(self):
        request={'operation':'tokens','unit':0,'text':'Olá 😀 mundo 123!','language':'pt'}
        self.assertEqual(provider.analyze(request)['tokens'],[[0,3,0],[4,2,4],[7,5,0],[13,3,1]])
        self.assertEqual(provider.analyze(dict(request,unit=3))['tokens'],[[0,17,0]])
        self.assertEqual(provider.analyze(dict(request,unit=2,text='a\r\nb\n😀'))['tokens'],[[0,3,0],[3,2,0],[5,2,0]])
        self.assertEqual(provider.analyze(dict(request,text=''))['tokens'],[])
    def test_validation(self):
        for request in [{'operation':'bad','text':''},{'operation':'tokens','text':'x','unit':True},{'operation':'tokens','text':'x','unit':0,'language':'../x'},{'operation':'detect','text':None}]:
            with self.assertRaises(ValueError):provider.analyze(request)
    def test_private_framing_and_redacted_errors(self):
        with tempfile.TemporaryDirectory(prefix='qi-language-') as directory:
            path=Path(directory)/'bridge.sock'
            process=subprocess.Popen([sys.executable,str(SOURCE),'--serve',str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                for _ in range(500):
                    if path.exists():break
                    if process.poll() is not None:self.fail('provider exited')
                    time.sleep(.02)
                self.assertEqual(path.stat().st_mode & 0o777,0o600)
                self.assertEqual(provider.exchange(path,{'operation':'ping'})['result']['version'],1)
                self.assertEqual(provider.exchange(path,{'operation':'secret-TEST-TEXT','text':'secret-TEST-TEXT'}),{'error':'ValueError'})
                with socket.socket(socket.AF_UNIX) as client:
                    client.settimeout(3);client.connect(str(path));client.sendall(struct.pack('>I',provider.LIMIT+1))
                    size,=struct.unpack('>I',provider.read_exact(client,4))
                    self.assertEqual(provider.read_exact(client,size),b'{"error": "ValueError"}')
            finally:
                process.terminate();out,err=process.communicate(timeout=5)
            self.assertEqual(out,b'');self.assertNotIn(b'secret-TEST-TEXT',err)

if __name__=='__main__':unittest.main()
