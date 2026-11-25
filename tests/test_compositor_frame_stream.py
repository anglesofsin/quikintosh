"""Exercise native frame delivery with private UNIX sockets, no desktop access."""
import json,os,re,socket,subprocess,tempfile,threading,time,unittest
from pathlib import Path
QS=os.environ.get('QUICKINTOSH_TEST_QS','')
MODULE=os.environ.get('QUICKINTOSH_TEST_RENDER_MODULE','')
@unittest.skipUnless(QS and MODULE,'Built native rendering module required')
class CompositorFrameStream(unittest.TestCase):
 def test_compositor_events_drive_geometry_without_animation_timer(self):
  counts=[]
  for cap in [0,30]:
   with tempfile.TemporaryDirectory(prefix='qi-frames-') as folder:
    root=Path(folder);runtime=root/'run';runtime.mkdir(mode=0o700)
    server=runtime/'hypr/test';server.mkdir(parents=True)
    stream=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);stream.bind(str(server/'quickintosh-frames.sock'));stream.settimeout(.2)
    rpc=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);rpc.bind(str(server/'.socket.sock'));rpc.listen();rpc.settimeout(.2)
    stop=threading.Event();rpcCalls=[];errors=[]
    def packet(x,animating=True):return json.dumps({'supported':True,'animating':animating,'refreshHz':240,'windows':{'1':{'at':[x,0],'size':[100,100],'visible':True}}}).encode()
    def fallback():
     while not stop.is_set():
      try:c,_=rpc.accept()
      except socket.timeout:continue
      try:c.recv(1000);rpcCalls.append(1);c.sendall(packet(-100,False));c.close()
      except OSError:pass
    def frames():
     first=True
     while not stop.is_set():
      try:message,peer=stream.recvfrom(128)
      except socket.timeout:continue
      try:
       if first:
        first=False
        for n in range(60):stream.sendto(packet(n),peer);time.sleep(.005)
       stream.sendto(packet(999,False),peer)
      except OSError as e:
       if not stop.is_set():errors.append(str(e))
    workers=[threading.Thread(target=fn,daemon=True) for fn in [fallback,frames]]
    for thread in workers:thread.start()
    (root/'shell.qml').write_text('''import QtQuick
import Quickshell
import Quickintosh.Render
Scope{
 property int updates:0
 property real lastX:-1
 Connections{target:FramePacer;function onGeometryChanged(){updates++;lastX=FramePacer.geometry['1']?.at[0] ?? -1}}
 Component.onCompleted:FramePacer.setGeometryMotion(true,CAP)
 Timer{interval:1100;running:true;onTriggered:{
  if(!FramePacer.frameSynchronized || lastX!==999 || updates<3){console.error('STREAM_FAILED',updates,lastX,FramePacer.frameSynchronized);Qt.exit(2);return}
  console.log('FRAME_STREAM_OK',updates);Qt.quit()
 }}
}'''.replace('CAP',str(cap)))
    env=dict(os.environ,HOME=folder,XDG_CONFIG_HOME=folder+'/.config',XDG_STATE_HOME=folder+'/.state',XDG_CACHE_HOME=folder+'/.cache',XDG_RUNTIME_DIR=str(runtime),QT_QPA_PLATFORM='offscreen',HYPRLAND_INSTANCE_SIGNATURE='test',QML_IMPORT_PATH=MODULE)
    for key in ['DISPLAY','WAYLAND_DISPLAY','QML2_IMPORT_PATH','QT_PLUGIN_PATH']:env.pop(key,None)
    try:result=subprocess.run([QS,'-p',folder],env=env,capture_output=True,text=True,timeout=8)
    finally:
     stop.set()
     for thread in workers:thread.join(timeout=1)
     stream.close();rpc.close()
    output=result.stdout+result.stderr;self.assertEqual(result.returncode,0,output)
    match=re.search(r'FRAME_STREAM_OK (\d+)',output);self.assertIsNotNone(match,output)
    count=int(match[1]);counts.append(count)
    self.assertLessEqual(len(rpcCalls),3,'Frame stream must replace per-frame RPC')
    self.assertFalse(errors,errors)
    self.assertFalse(list(runtime.glob('qf-*')),'Subscriber sockets must be removed on exit')
  self.assertGreater(counts[0],25,counts)
  self.assertLess(counts[1],counts[0]/2,counts)
  print('Frame-driven geometry updates, native / cap30:',counts)
if __name__=='__main__':unittest.main()
