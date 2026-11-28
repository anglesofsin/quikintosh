"""Cold glass on two tiled windows entering from a hidden workspace, privately."""
from pathlib import Path
import json,os,signal,subprocess,time
from PIL import Image
runtime=Path(os.environ['XDG_RUNTIME_DIR']).resolve()
assert not runtime.is_relative_to('/run/user'),'Private compositor required'
root=Path(os.environ['HOME'])/'glass-reentry';root.mkdir()
out=Path('/home/pg/.local/state/quickintosh/reviews/glass-workspace-reentry');out.mkdir(parents=True,exist_ok=True)
qs='/nix/store/84llqjz63a7x3mb44hd5d289i42zayhc-quickshell-wrapped-0.3.1/bin/qs'
(root/'shell.qml').write_text('''import QtQuick
import Quickshell
import Quickshell.Wayland
ShellRoot{
 PanelWindow{anchors{top:true;bottom:true;left:true;right:true}exclusiveZone:-1;color:'#eeeeee';WlrLayershell.namespace:'qa-background';WlrLayershell.layer:WlrLayer.Background;WlrLayershell.keyboardFocus:WlrKeyboardFocus.None}
 FloatingWindow{visible:true;title:'QI Cold Left';implicitWidth:600;implicitHeight:800;color:'#08000000';Text{text:'Left';color:'white'}}
 FloatingWindow{visible:true;title:'QI Cold Right';implicitWidth:600;implicitHeight:800;color:'#08000000';Text{text:'Right';color:'white'}}
}''')
def ctl(*args):
 r=subprocess.run(['hyprctl',*args],capture_output=True,text=True,timeout=8)
 assert r.returncode==0,(args,r.stdout,r.stderr)
 return r.stdout.strip()
def lua(code):
 result=ctl('eval',code)
 assert 'error' not in result.lower(),result
 return result
def stats():return json.loads(ctl('-j','hyprglass','stats'))['monitors'][0]
log=(out/'qml.log').open('w');q=subprocess.Popen([qs,'-p',str(root)],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
try:
 for attempt in range(70):
  windows=[w for w in json.loads(ctl('-j','clients')) if w['title'].startswith('QI Cold')]
  if len(windows)==2:break
  time.sleep(.1)
 assert len(windows)==2,windows
 lua('hl.config({general={gaps_in=0,gaps_out=0,border_size=0}});hl.animation({leaf="workspaces",enabled=true,speed=6,bezier="default"})')
 for w in windows:
  sel=json.dumps('address:'+w['address'])
  lua('hl.dispatch(hl.dsp.window.move({workspace=2,follow=false,window='+sel+'}))')
 time.sleep(.8)
 ctl('dismissnotify','-1')
 results={}
 plugins=[('before','/nix/store/g2bn1n5qmkcssiwygdi1id5kaahnglh1-hyprglass-1.1.0/lib/hyprglass.so'),('after',os.environ['QI_GLASS_PLUGIN'])]
 for phase,plugin in plugins:
  lua('hl.dispatch(hl.dsp.focus({workspace=1}))');time.sleep(.7)
  assert ctl('plugin','load',plugin)=='ok'
  lua('hl.plugin.hyprglass.config({enabled=true,default_preset="pomme",windows={background_cache=false,live_resample=true,live_resample_fps=0},layers={enabled=false}})')
  time.sleep(.1);ctl('hyprglass','stats','reset')
  # No screenshot before/during this first transition: capture may widen damage.
  lua('hl.dispatch(hl.dsp.focus({workspace=2}))')
  time.sleep(.7)
  cold=stats()
  print(phase,'COLD_REENTRY',cold,flush=True)
  for direction in [1,2,1,2]:
   lua('hl.dispatch(hl.dsp.focus({workspace='+str(direction)+'}))')
   for frame in range(5):
    time.sleep(.035)
    path=out/(phase+'-'+str(direction)+'-'+str(frame)+'.png')
    subprocess.run(['grim','-l','1',str(path)],check=True,timeout=10,capture_output=True)
  time.sleep(.7)
  path=out/(phase+'-settled.png');subprocess.run(['grim','-l','1',str(path)],check=True,timeout=10,capture_output=True)
  im=Image.open(path).convert('RGB');points=[im.getpixel((int(im.width*x),im.height//2)) for x in [.1,.25,.45,.55,.75,.9]]
  ctl('dismissnotify','-1');time.sleep(1.2);idle0=stats();time.sleep(.3);idle1=stats()
  idleFrames=idle1['frames']-idle0['frames']
  results[phase]={'cold':cold,'settledPixels':points,'idleFrames':idleFrames}
  if phase=='after':
   assert idleFrames<=3,('Transition keeps redrawing after settling',idleFrames)
   assert cold['windowCacheMisses']>0,cold
   assert cold['windowDeferredResamples']==0,cold
   assert cold['windowGlassDraws']==cold['windowCacheMisses'],cold
   assert max(p[0] for p in points)-min(p[0] for p in points)<=3,points
  assert ctl('plugin','unload',plugin)=='ok'
 (out/'metrics.json').write_text(json.dumps(results,indent=2))
 print('COLD_WORKSPACE_GLASS_PASSED',flush=True)
finally:
 if q.poll() is None:os.killpg(q.pid,signal.SIGTERM);q.wait(timeout=5)
 log.close()
