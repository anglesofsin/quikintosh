"""Check native dock exit pixels in a private compositor, never the host."""
from test_glass_background_order import *
@unittest.skipUnless(all((RUNTIME,WAYLAND,SIGNATURE,PLUGIN,QS,Image)),'Private compositor, native plugin and Pillow required')
class DockMotion(unittest.TestCase):
 def test_hidden_dock_leaves_no_glass_pixels(self):
  self.assertNotEqual(Path(RUNTIME).resolve(),Path(os.environ.get('XDG_RUNTIME_DIR','/run/user/1000')).resolve())
  with tempfile.TemporaryDirectory(prefix='qi-dock-motion-') as directory:
   root=Path(directory);(root/'shell.qml').write_text((ROOT/'tests/fixtures/dock-glass-motion.qml').read_text())
   env=dict(os.environ,HOME=directory,XDG_CONFIG_HOME=directory+'/.config',XDG_CACHE_HOME=directory+'/.cache',XDG_RUNTIME_DIR=RUNTIME,WAYLAND_DISPLAY=WAYLAND,HYPRLAND_INSTANCE_SIGNATURE=SIGNATURE)
   env.pop('DISPLAY',None);env.pop('DBUS_SESSION_BUS_ADDRESS',None)
   def ctl(*args):return subprocess.run(['hyprctl',*args],env=env,capture_output=True,text=True,check=True,timeout=8).stdout
   def show(value):
    result=subprocess.run([QS,'-p',directory,'ipc','call','qa','setShown',str(value).lower()],env=env,capture_output=True,text=True,timeout=5)
    self.assertEqual(result.returncode,0,result.stdout+result.stderr+(root/'runtime.log').read_text())
   def pixels():
    p=root/'frame.png';subprocess.run(['grim',str(p)],env=env,capture_output=True,check=True,timeout=5)
    with Image.open(p) as im:
     im=im.convert('RGB');return [im.getpixel((im.width//2+dx,im.height-60)) for dx in (-240,0,240)]
   with (root/'runtime.log').open('w') as log:
    proc=subprocess.Popen([QS,'-p',directory],env=env,stdout=log,stderr=log,start_new_session=True)
    loaded=False
    try:
     time.sleep(1);self.assertIsNone(proc.poll(),(root/'runtime.log').read_text());ctl('plugin','load',PLUGIN);loaded=True
     ctl('eval','hl.plugin.hyprglass.config({enabled=true,default_preset="pomme",layers={enabled=true,live_resample_fps=0}});hl.plugin.hyprglass.layer("quickshell:dock",{mask_mode="contour",mask_threshold=0.015,live_resample=true})')
     time.sleep(.3)
     for _ in range(6):
      show(True);time.sleep(.22);visible=pixels()
      self.assertTrue(any(sum(abs(a-b) for a,b in zip(c,(96,128,160)))>15 for c in visible))
      show(False);time.sleep(.22)
      for c in pixels():self.assertLessEqual(max(abs(a-b) for a,b in zip(c,(96,128,160))),3,'Stale glass behind hidden dock')
     print('DOCK_GLASS_SIX_OPEN_CLOSE_CYCLES_OK')
    finally:
     if loaded:ctl('plugin','unload',PLUGIN)
     os.killpg(proc.pid,signal.SIGTERM);proc.wait(timeout=4)
if __name__=='__main__':unittest.main()
