"""Compare wallpaper engines only on explicitly supplied private Wayland outputs."""
import argparse,json,math,os,re,signal,subprocess,sys,tempfile,time
from pathlib import Path

def private_environment(runtime,display,signature):
 runtime=Path(runtime).resolve(strict=True)
 host=Path('/run/user')/str(os.getuid())
 if runtime==host or str(runtime).startswith(str(host)+'/'):
  raise ValueError('A separate private compositor runtime is required; host outputs are never benchmarked')
 socket=Path(display) if Path(display).is_absolute() else runtime/display
 if socket.parent.resolve()!=runtime or not socket.is_socket():raise ValueError('Display must be a socket inside the private runtime')
 if not re.fullmatch(r'[A-Za-z0-9_.-]{1,180}',signature):raise ValueError('Invalid private compositor signature')
 compositor_socket=runtime/'hypr'/signature/'.socket.sock'
 if not compositor_socket.resolve().is_relative_to(runtime):raise ValueError('Compositor socket must remain inside the private runtime')
 if not compositor_socket.is_socket():raise ValueError('Private Hyprland socket not found')
 env=dict(os.environ,XDG_RUNTIME_DIR=str(runtime),WAYLAND_DISPLAY=str(socket),HYPRLAND_INSTANCE_SIGNATURE=signature,DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent',QT_QPA_PLATFORM='wayland')
 env.pop('DISPLAY',None)
 return env

def cpu_seconds(pid):
 fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
 return (int(fields[11])+int(fields[12]))/os.sysconf('SC_CLK_TCK')

def memory(pid):
 try:
  text=Path(f'/proc/{pid}/smaps_rollup').read_text()
  return {name.lower()+'MiB':int(re.search(r'^'+name+r':\s+(\d+)',text,re.M)[1])/1024 for name in ('Rss','Pss')}
 except (OSError,TypeError):return {}

def benchmark(args):
 env=private_environment(args.runtime,args.display,args.signature)
 video=Path(args.video).expanduser().resolve(strict=True)
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,codec_name,avg_frame_rate','-of','json',str(video)],text=True,timeout=20))['streams'][0]
 rate=info.get('avg_frame_rate','0/1').split('/');rate=float(rate[0])/max(float(rate[1]),1)
 frames_target=min(360,max(1,math.ceil(rate)))
 with tempfile.TemporaryDirectory(prefix='qi-playback-bench-') as temporary:
  home=Path(temporary);env.update(HOME=temporary,XDG_CONFIG_HOME=str(home/'.config'),XDG_CACHE_HOME=str(home/'.cache'),XDG_STATE_HOME=str(home/'.state'))
  log=home/'player.log'
  if args.backend=='qt':
   app=home/'player';app.mkdir();(app/'shell.qml').write_text((Path(args.qt_root)/'wallpaper-benchmark.qml').read_text())
   env.update(QUICKINTOSH_BENCHMARK_VIDEO=video.as_uri(),QT_LOGGING_RULES='qt.multimedia.ffmpeg.hwaccel.debug=true')
   command=[args.qs,'-p',str(app)]
   def state():return json.loads(subprocess.check_output([args.qs,'-p',str(app),'ipc','call','wallpaperBenchmark','state'],env=env,text=True,stderr=subprocess.DEVNULL,timeout=5))
  else:
   # Full quality, no overlays/audio/background polling that could distort this comparison.
   config=home/'anima.toml';config.write_text('[general]\nfps='+str(frames_target)+'\ndefault_wallpaper='+json.dumps(str(video),ensure_ascii=False)+'\ncompositor="hyprland"\nlow_battery_pause=0\npause_on_fullscreen=false\npause_on_maximized=false\npause_on_battery=false\naudio_capture=false\nmute=true\n[character]\nenabled=false\n')
   command=[args.daemon,'--config',str(config)]
   def state():
    result=json.loads(subprocess.check_output([args.cli,'status','--json'],env=env,text=True,stderr=subprocess.DEVNULL,timeout=5))
    return {key:result.get(key) for key in ('version','uptime_secs','monitors')}
  with log.open('w') as stream:player=subprocess.Popen(command,env=env,stdout=stream,stderr=stream,start_new_session=True)
  try:
   deadline=time.monotonic()+15
   while True:
    if player.poll() is not None:raise RuntimeError(log.read_text()[-3000:])
    try:
     initial=state()
     ready=initial.get('frames',0)>=15 if args.backend=='qt' else any(m.get('configured') and m.get('frames',0)>=15 and not m.get('error') for m in initial.get('monitors',[]))
     if ready:break
    except (ValueError,subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
    if time.monotonic()>deadline:raise RuntimeError('Player did not become ready: '+log.read_text()[-1500:])
    time.sleep(.2)
   time.sleep(1);before=cpu_seconds(player.pid);start=time.monotonic();time.sleep(args.seconds)
   cpu=cpu_seconds(player.pid)-before;elapsed=time.monotonic()-start
   report={'backend':args.backend,'durationSeconds':elapsed,'cpuPercentOneCore':cpu/elapsed*100,'memory':memory(player.pid),'source':info,'state':state(),'quality':'original; no fast scaler profile','isolated':True,'softwareRendering':env.get('LIBGL_ALWAYS_SOFTWARE')=='1' or env.get('QSG_RHI_BACKEND')=='software'}
   messages=log.read_text()
   report['hardwareSelection']=re.findall(r'Selected format[^\n]*for hw[^\n]*|hwdec-current=[^\s,]+',messages)
   report['timingMeaning']='decoded frame delivery' if args.backend=='qt' else 'surface commits; can include repeated video frames'
   return report
  finally:
   if player.poll() is None:
    os.killpg(player.pid,signal.SIGTERM)
    try:player.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(player.pid,signal.SIGKILL);player.wait()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--backend',choices=['qt','anima'],required=True);p.add_argument('--video',required=True)
 p.add_argument('--runtime',required=True);p.add_argument('--display',required=True);p.add_argument('--signature',required=True)
 p.add_argument('--seconds',type=int,default=10);p.add_argument('--qs',required=True);p.add_argument('--qt-root',required=True);p.add_argument('--daemon',required=True);p.add_argument('--cli',required=True)
 args=p.parse_args()
 if not 5<=args.seconds<=60:p.error('Measurement duration must be between 5 and 60 seconds')
 try:os.nice(10);print(json.dumps(benchmark(args),ensure_ascii=False))
 except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:print(str(error),file=sys.stderr);return 1
 return 0
if __name__=='__main__':sys.exit(main())
