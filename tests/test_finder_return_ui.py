"""Return in a real isolated Nautilus window; no host keyboard input."""
from pathlib import Path
import os,tempfile,json,subprocess,time,signal,unittest
@unittest.skipUnless(os.getenv('QUICKINTOSH_TEST_PRIVATE_RUNTIME'),'Private compositor required')
class FinderReturn(unittest.TestCase):
 def test_return_rename(self):
  with tempfile.TemporaryDirectory(prefix='qi-native-finder-') as tmp:
   root=Path(tmp);folder=root/'Files';folder.mkdir();(folder/'Selected document.txt').write_text('preview')
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_STATE_HOME=tmp+'/.state',XDG_CACHE_HOME=tmp+'/.cache',XDG_RUNTIME_DIR=os.environ['QUICKINTOSH_TEST_PRIVATE_RUNTIME'],WAYLAND_DISPLAY=os.environ['QUICKINTOSH_TEST_PRIVATE_WAYLAND'],HYPRLAND_INSTANCE_SIGNATURE=os.environ['QUICKINTOSH_TEST_PRIVATE_HYPRLAND'])
   env.pop('DISPLAY',None)
   bus=subprocess.Popen(['dbus-daemon','--session','--nofork','--print-address=1','--address=unix:path='+tmp+'/bus'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True);env['DBUS_SESSION_BUS_ADDRESS']=bus.stdout.readline().strip()
   env['LD_PRELOAD']=Path('/tmp/qi-finder-rename.path').read_text().strip()+'/lib/theme-live.so';env['GDK_BACKEND']='wayland';env['GSK_RENDERER']='cairo';env['RUNNING_TESTS']='TRUE';env['GIO_USE_VFS']='local';env['GSETTINGS_BACKEND']='memory'
   out=Path('/home/pg/.local/state/quickintosh/reviews/file-microinteractions');out.mkdir(parents=True,exist_ok=True)
   with (out/'finder.log').open('w') as log:p=subprocess.Popen(['/nix/store/10fvws3xcy23a68ciffc5f2kz1yq4prj-nautilus-50.2.2/bin/nautilus','--new-window','--select',str(folder/'Selected document.txt')],env=env,stdout=log,stderr=log,start_new_session=True)
   def ctl(*args):return subprocess.check_output(['hyprctl',*args],env=env,text=True,timeout=5)
   try:
    end=time.monotonic()+30
    while True:
     clients=json.loads(ctl('-j','clients'));w=next((w for w in clients if 'nautilus' in w['class'].lower()),None)
     if w:break
     self.assertLess(time.monotonic(),end,(out/'finder.log').read_text());time.sleep(.2)
    time.sleep(1);address=w['address']
    def key(k):ctl('eval','hl.dispatch(hl.dsp.send_shortcut({mods="",key="'+k+'",window="address:'+address+'"}))')
    key('Return');time.sleep(.4);subprocess.run(['grim','-l','1',str(out/'finder-return-rename.png')],env=env,check=True)
    key('Escape');time.sleep(.2)
    self.assertTrue((folder/'Selected document.txt').exists())
    print('FINDER_RETURN_CAPTURE_READY')
   finally:
    if p.poll() is None:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
    bus.terminate();bus.wait(timeout=5);bus.stdout.close()
if __name__=='__main__':unittest.main()
