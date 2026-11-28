"""Native pixel regression for monitor-edge padding; private compositor only.

QI_GLASS_PLUGIN points at the candidate library; the baseline is the current
validated 1.1 library. Does not operate on the user's compositor.
"""
from pathlib import Path
import os,subprocess,time,json,signal
from PIL import Image
runtime=Path(os.environ['XDG_RUNTIME_DIR']).resolve()
assert not runtime.is_relative_to('/run/user'), 'Private compositor required'
root=Path(os.environ['HOME'])/'edge-glass-fixture';root.mkdir()
(root/'shell.qml').write_text('''import QtQuick
import Quickshell
import Quickshell.Wayland
ShellRoot{
 PanelWindow{anchors{top:true;bottom:true;left:true;right:true};exclusiveZone:-1;color:'#eeeeee';WlrLayershell.namespace:'qa-background';WlrLayershell.layer:WlrLayer.Background;WlrLayershell.keyboardFocus:WlrKeyboardFocus.None}
 FloatingWindow{visible:true;title:'QI Glass Edge Target';implicitWidth:850;implicitHeight:650;color:'#08000000'}
}'''.replace('right:true};','right:true}'))
env=dict(os.environ);qs='/nix/store/84llqjz63a7x3mb44hd5d289i42zayhc-quickshell-wrapped-0.3.1/bin/qs'
out=Path('/home/pg/.local/state/quickintosh/reviews/glass-screen-edge');out.mkdir(parents=True,exist_ok=True)
def ctl(*args):
 r=subprocess.run(['hyprctl',*args],env=env,capture_output=True,text=True,timeout=8)
 assert r.returncode==0,(args,r.stdout,r.stderr)
 return r.stdout.strip()
with (out/'qml.log').open('w') as log:q=subprocess.Popen([qs,'-p',str(root)],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
try:
 time.sleep(1)
 ctl('eval','hl.window_rule({name="qa-glass",match={title="^QI Glass Edge Target$"},float=true,no_anim=true,opacity="1.0 1.0",tag="+hyprglass_enabled"})')
 results={}
 for phase,plugin in [('before','/nix/store/asc3mjvxb0krljv3dcgzi1shymr01w98-hyprglass-1.1.0/lib/hyprglass.so'),('after',os.environ['QI_GLASS_PLUGIN'])]:
  print('LOAD',phase,ctl('plugin','load',plugin),flush=True)
  ctl('eval','hl.plugin.hyprglass.config({enabled=true,default_preset="pomme",windows={background_cache=false,live_resample=true,live_resample_fps=0},layers={enabled=false}})')
  time.sleep(.5)
  for attempt in range(50):
   windows=json.loads(ctl('-j','clients'));w=next((w for w in windows if w['title']=='QI Glass Edge Target'),None)
   if w:break
   time.sleep(.1)
  assert w,windows
  selector='address:'+w['address']
  ctl('eval','hl.dispatch(hl.dsp.window.float({action="enable",window='+json.dumps(selector)+'}));hl.dispatch(hl.dsp.window.resize({x=850,y=650,window='+json.dumps(selector)+'}))')
  def position(x,y):ctl('eval','hl.dispatch(hl.dsp.window.move({x='+str(x)+',y='+str(y)+',window='+json.dumps(selector)+'}))')
  pixels=[]
  for label,x,y in [('center',200,100),('left',-400,100),('right',900,100),('top',200,-350),('bottom',200,650),('corner',-400,-350)]:
   position(x,y);time.sleep(.15)
   geometry=next(w for w in json.loads(ctl('-j','clients')) if w['title']=='QI Glass Edge Target');print('GEOMETRY',label,geometry['at'],geometry['size'],geometry['floating'],flush=True)
   path=out/(phase+'-'+label+'.png');subprocess.run(['grim','-l','1',str(path)],env=env,check=True,timeout=10)
   im=Image.open(path).convert('RGB');px=min(im.width-60,max(60,x+425));py=min(im.height-60,max(60,y+325))
   pixels.append({'position':label,'sample':im.getpixel((px,py)),'horizontal':[im.getpixel((xx,im.height//2)) for xx in [1,5,15,30,60,100,im.width-101,im.width-61,im.width-31,im.width-16,im.width-6,im.width-2]],'vertical':[im.getpixel((im.width//2,yy)) for yy in [1,5,15,30,60,100,im.height-101,im.height-61,im.height-31,im.height-16,im.height-6,im.height-2]]})
  results[phase]=pixels
  print(phase,pixels,flush=True)
  if phase=='after':
   position(0,100)
   ctl('eval','hl.animation({leaf="workspaces",enabled=true,speed=5,bezier="default"});hl.dispatch(hl.dsp.window.move({workspace=1,follow=true,window='+json.dumps(selector)+'}))')
   time.sleep(.6)
   for workspace in [2,1]:
    ctl('eval','hl.dispatch(hl.dsp.focus({workspace='+str(workspace)+'}))')
    for frame in range(4):
     time.sleep(.04)
     subprocess.run(['grim','-l','1',str(out/('slide-'+str(workspace)+'-'+str(frame)+'.png'))],env=env,check=True,timeout=10)
  ctl('plugin','unload',plugin)
 (out/'metrics.json').write_text(json.dumps(results,indent=2))
 if os.environ['QI_GLASS_PLUGIN']!='/nix/store/asc3mjvxb0krljv3dcgzi1shymr01w98-hyprglass-1.1.0/lib/hyprglass.so':
  for kind,axis,index in [('left','horizontal',0),('right','horizontal',-1),('top','vertical',0),('bottom','vertical',-1)]:
   old=next(x for x in results['before'] if x['position']==kind)[axis][index][0]
   new=next(x for x in results['after'] if x['position']==kind)[axis][index][0]
   assert new>old+25,(kind,old,new)
  old=results['before'][0]['sample'];new=results['after'][0]['sample']
  assert max(abs(a-b) for a,b in zip(old,new))<=2,('In-bounds appearance changed',old,new)
 print('EDGE_GLASS_CAPTURE_COMPLETE',flush=True)
finally:
 if q.poll() is None:os.killpg(q.pid,signal.SIGTERM);q.wait(timeout=5)
