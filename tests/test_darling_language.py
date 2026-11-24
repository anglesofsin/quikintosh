"""Opt-in native Objective-C integration with an isolated Darwin prefix."""
import binascii
import json
import os
from pathlib import Path
import shutil
import socket
import socketserver
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
DARLING=os.environ.get('QUICKINTOSH_TEST_DARLING')

class DarwinLanguage(unittest.TestCase):
    @unittest.skipUnless(DARLING,'Set QUICKINTOSH_TEST_DARLING to the experimental command')
    def test_language_and_real_image_thumbnail(self):
        root=Path(tempfile.mkdtemp(prefix='quickintosh-language-'))
        env=dict(os.environ,DPREFIX=str(root/'prefix'))
        try:
            def chunk(tag,data):
                return struct.pack('>I',len(data))+tag+data+struct.pack('>I',binascii.crc32(tag+data)&0xffffffff)
            image=root/'fixture.png'
            image.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',128,64,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\x33\x66\x99'*128)*64))+chunk(b'IEND',b''))
            for fixture,marker,args in [('naturallanguage-runtime.py','NATURALLANGUAGE_DARWIN_UTF16_RANGES_EMPTY_OVERFLOW_OK',[]),('thumbnail-runtime.py','THUMBNAIL_DARWIN_IMAGE_SIZE_ASYNC_ERROR_CALLBACK_OK',['/Volumes/SystemRoot'+str(image)])]:
                source=root/fixture;shutil.copyfile(ROOT/'tests/fixtures'/fixture,source)
                result=subprocess.run([DARLING,'shell','/usr/bin/python2.7','/Volumes/SystemRoot'+str(source),*args],env=env,capture_output=True,text=True,timeout=180)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertIn(marker,result.stdout,result.stdout+result.stderr)
            self.check_delayed_response(root,env)
        finally:
            subprocess.run([DARLING,'--stop'],env=env,capture_output=True,check=True,timeout=30)
            subprocess.run(['unshare','--user','--map-auto','--map-current-user','--setuid=0','--setgid=0',sys.executable,'-c','import shutil,sys;shutil.rmtree(sys.argv[1])',str(root)],capture_output=True,check=True,timeout=30)

    def check_delayed_response(self,root,env):
        backend=subprocess.check_output([DARLING,'shell','/usr/bin/printenv','QUICKINTOSH_NL_SOCKET'],env=env,text=True,timeout=15).strip()
        delayed=[]
        def receive(stream,count):
            result=bytearray()
            while len(result)<count:
                data=stream.recv(count-len(result))
                if not data:raise ConnectionError('Incomplete test frame')
                result.extend(data)
            return bytes(result)
        class Proxy(socketserver.BaseRequestHandler):
            def handle(self):
                self.request.settimeout(10)
                header=receive(self.request,4)
                length,=struct.unpack('>I',header)
                if length>4*1024*1024:raise ValueError('Oversize test frame')
                payload=receive(self.request,length)
                if json.loads(payload).get('operation')=='tokens' and not delayed:
                    delayed.append(True);time.sleep(3.5)
                with socket.socket(socket.AF_UNIX) as upstream:
                    upstream.settimeout(10);upstream.connect(backend)
                    upstream.sendall(header+payload)
                    header=receive(upstream,4);length,=struct.unpack('>I',header)
                    if length>4*1024*1024:raise ValueError('Oversize test response')
                    self.request.sendall(header+receive(upstream,length))
        with tempfile.TemporaryDirectory(prefix='test-',dir=Path(backend).parent) as directory:
            proxy=str(Path(directory)/'delay.sock')
            with socketserver.UnixStreamServer(proxy,Proxy) as server:
                os.chmod(proxy,0o600)
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                try:
                    result=subprocess.run([DARLING,'shell','/bin/sh','-c','export QUICKINTOSH_NL_SOCKET="$1"; shift; exec "$@"','test-delayed-provider',proxy,'/usr/bin/python2.7','/Volumes/SystemRoot'+str(root/'naturallanguage-runtime.py')],env=env,capture_output=True,text=True,timeout=30)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    self.assertEqual(delayed,[True])
                finally:
                    server.shutdown();thread.join(timeout=5)

if __name__=='__main__':unittest.main()
