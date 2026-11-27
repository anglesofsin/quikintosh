"""Opaque bar and inverse corners in a private compositor, with pixel checks."""
from pathlib import Path
import os,json,subprocess,tempfile,shutil,time,signal,unittest
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
REQUIRED=['QUICKINTOSH_TEST_SOURCE','QUICKINTOSH_TEST_QS','QUICKINTOSH_TEST_PRIVATE_RUNTIME','QUICKINTOSH_TEST_PRIVATE_WAYLAND','QUICKINTOSH_TEST_PRIVATE_HYPRLAND']
@unittest.skipUnless(all(os.environ.get(k) for k in REQUIRED),'Private compositor required')
class MenuBarBackground(unittest.TestCase):
 def test_opaque_outside_corners(self):
  runtime=os.environ['QUICKINTOSH_TEST_PRIVATE_RUNTIME']
  self.assertFalse(Path(runtime).resolve().is_relative_to(Path('/run/user')/str(os.getuid())))
  with tempfile.TemporaryDirectory(prefix='qi-bar-qa-') as tmp:
   root=Path(tmp);source=Path(os.environ['QUICKINTOSH_TEST_SOURCE'])
   for entry in source.iterdir():
    if entry.name not in ['shell.qml','qmldir']:(root/entry.name).symlink_to(entry,target_is_directory=entry.is_dir())
   (root/'qmldir').write_text((source/'qmldir').read_text()+'\nMenuBarBackground MenuBarBackground.qml\n')
   shutil.copyfile(ROOT/'modules/lickintosh/corners/MenuBarBackground.qml',root/'MenuBarBackground.qml')
   (root/'shell.qml').write_text('''import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
import "ui/settings/pages" as Pages
ShellRoot{
 Component.onCompleted:{ShellConfig.options.topbar.backgroundEnabled=true;ShellConfig.options.topbar.backgroundColor='#000000';ShellConfig.options.topbar.backgroundOpacity=1;ShellConfig.options.edges.roundMenuBackground=true;ShellConfig.options.edges.menuCornerRadius=20;ShellConfig.options.edges.hideCornersFullscreen=true}
 FloatingWindow{id:win;Pages.TopBarPage{id:page;visible:false;width:600;height:500}visible:true;title:'Menubar material QA';implicitWidth:180;implicitHeight:100;color:'#ff0000'
 Item{id:canvas;width:180;height:100;Rectangle{anchors.fill:parent;color:'#ff0000'}MenuBarBackground{id:bar;width:180;height:32}}
 }
 IpcHandler{target:'barQA';function capture():void{canvas.grabToImage(result=>result.saveToFile(Quickshell.env('QI_BAR_CAPTURE')))}function fullscreen():void{bar.fullscreen=true}
 function clearTint():void{ShellConfig.options.topbar.backgroundOpacity=0;ShellConfig.options.topbar.blurEnabled=true}
 function clearMaterial():void{ShellConfig.options.topbar.blurEnabled=false}
 function precision():string{let queue=[page];while(queue.length){let c=queue.shift();if(c.text==='Color opacity' && typeof c.decimals==='number'){const control=c.children[0];const values=[];for(let value of [.13,.37,.82]){control.committed(value);values.push(ShellConfig.options.topbar.backgroundOpacity)}return JSON.stringify({decimals:c.decimals,step:control.step,values:values})}for(let child of (c.children || []))queue.push(child)}return '{}'}}
}''')
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_CACHE_HOME=tmp+'/.cache',XDG_STATE_HOME=tmp+'/.state',XDG_RUNTIME_DIR=runtime,WAYLAND_DISPLAY=os.environ['QUICKINTOSH_TEST_PRIVATE_WAYLAND'],HYPRLAND_INSTANCE_SIGNATURE=os.environ['QUICKINTOSH_TEST_PRIVATE_HYPRLAND'],QI_BAR_CAPTURE=tmp+'/capture.png',QT_QUICK_BACKEND='software',QSG_RENDER_LOOP='basic',DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
   qs=os.environ['QUICKINTOSH_TEST_QS'];log=root/'qa.log'
   def ipc(action):
    result=subprocess.run([qs,'-p',tmp,'ipc','call','barQA',action],env=env,capture_output=True,text=True,timeout=5)
    self.assertEqual(result.returncode,0,result.stdout+result.stderr+log.read_text())
    return result.stdout
   with log.open('w') as output:p=subprocess.Popen([qs,'-p',tmp],env=env,stdout=output,stderr=output,start_new_session=True)
   try:
    time.sleep(5);self.assertIsNone(p.poll(),log.read_text());ipc('capture')
    capture=root/'capture.png'
    for _ in range(100):
     try:
      with Image.open(capture) as image:image.verify()
      break
     except (OSError,SyntaxError):time.sleep(.05)
    self.assertTrue(capture.exists(),log.read_text())
    with Image.open(capture) as im:
     rgb=im.convert('RGB')
     for point in [(0,0),(179,0),(90,31),(0,33),(179,33)]:self.assertEqual(rgb.getpixel(point),(0,0,0),str(point))
     for point in [(90,40),(19,51),(160,51)]:self.assertEqual(rgb.getpixel(point),(255,0,0),str(point))
    shutil.copyfile(capture,'/tmp/qi-menubar-opaque-corners.png')
    capture.unlink();ipc('fullscreen');time.sleep(.1);ipc('capture')
    for _ in range(100):
     try:
      with Image.open(capture) as image:image.verify()
      break
     except (OSError,SyntaxError):time.sleep(.05)
    self.assertTrue(capture.exists(),log.read_text())
    with Image.open(capture) as im:self.assertEqual(im.convert('RGB').getpixel((0,33)),(255,0,0))
    errors=subprocess.check_output(['hyprctl','configerrors'],env=env,text=True,timeout=5);self.assertFalse(errors.strip(),errors)
    self.assertNotIn('ReferenceError',log.read_text());self.assertNotIn('TypeError',log.read_text())
    precision=json.loads(ipc('precision'));self.assertEqual(precision['decimals'],2);self.assertAlmostEqual(precision['step'],.01);self.assertEqual(precision['values'],[.13,.37,.82])
    for action,expected in [('clearTint',250),('clearMaterial',255)]:
     capture.unlink();ipc(action);time.sleep(.1);ipc('capture')
     for _ in range(100):
      try:
       with Image.open(capture) as image:image.verify()
       break
      except (OSError,SyntaxError):time.sleep(.05)
     with Image.open(capture) as image:self.assertAlmostEqual(image.convert('RGB').getpixel((90,10))[0],expected,delta=1)
    print('MENUBAR_OPAQUE_AND_EXTERNAL_CORNERS_PIXELS_OK')
   finally:
    if log.exists():shutil.copyfile(log,'/tmp/qi-menubar-qa-last.log')
    if p.poll() is None:
     os.killpg(p.pid,signal.SIGTERM)
     try:p.wait(timeout=4)
     except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
if __name__=='__main__':unittest.main()
