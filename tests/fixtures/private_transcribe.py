from pathlib import Path
import tempfile,subprocess,os,time,json,sys
with tempfile.TemporaryDirectory(prefix='qi-private-pulse-') as directory:
 root=Path(directory);socket=root/'native'
 env=dict(os.environ,PULSE_SERVER='unix:'+str(socket),PULSE_RUNTIME_PATH=str(root/'runtime'),DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
 Path(env['PULSE_RUNTIME_PATH']).mkdir(mode=0o700)
 pulse=subprocess.Popen(['/nix/store/zj0y80bzx43np3lr4374fxy69sbh9gn2-pulseaudio-17.0/bin/pulseaudio','--daemonize=no','--exit-idle-time=-1','-n','--load=module-native-protocol-unix socket='+str(socket)+' auth-anonymous=1','--load=module-null-sink sink_name=qi_private'],env=env,stdout=subprocess.DEVNULL,stderr=(root/'pulse.log').open('w'),start_new_session=True)
 job=None
 try:
  for _ in range(100):
   if socket.exists():break
   if pulse.poll() is not None:raise RuntimeError((root/'pulse.log').read_text())
   time.sleep(.05)
  env.update(PULSE_SOURCE='qi_private.monitor',QUICKINTOSH_WHISPER_MODEL='/nix/store/6l0yf883n3nmy8lsdayp1a32625pkrdf-ggml-base.bin',PATH='/nix/store/xvwi61mvrlj81l5sib5306cwn95riv05-whisper-cpp-1.9.2/bin:'+os.environ['PATH'])
  job=subprocess.Popen([sys.executable,str(Path(__file__).resolve().parents[2]/'modules/lickintosh/island-shelf/transcribe_backend.py')],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  print('PRIVATE_SERVER_READY',flush=True)
  job.stdin.write(json.dumps(dict(action='record',language='en'))+'\n');job.stdin.flush()
  first=json.loads(job.stdout.readline());assert first==dict(type='phase',value='recording'),first
  print('CAPTURE_PHASE_READY',flush=True)
  time.sleep(1.5);job.stdin.write('stop\n');job.stdin.flush()
  print('STOP_SENT',flush=True)
  output,error=job.communicate(timeout=90);events=[json.loads(line) for line in output.splitlines()]
  assert job.returncode==0 and any(e['type']=='transcript' for e in events),(events,error)
  Path('/tmp/qi-private-recording-validation.json').write_text(json.dumps(dict(success=True,source='isolated PulseAudio null-sink monitor',realMicrophone=False,stopButtonProtocol=True),indent=2))
  print('PRIVATE_NULL_SOURCE_CAPTURE_STOP_AND_LOCAL_TRANSCRIPTION_OK')
 finally:
  if job and job.poll() is None:job.terminate();job.wait(timeout=5)
  pulse.terminate();pulse.wait(timeout=5)
