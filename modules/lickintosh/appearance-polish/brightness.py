"""Backlight/DDC control shared by Lickintosh panels and shortcuts."""
import fcntl,json,os,subprocess,sys,time
from pathlib import Path
state=Path(os.environ.get('XDG_RUNTIME_DIR',f'/tmp/lickintosh-{os.getuid()}'))/'lickintosh-brightness'
state.mkdir(mode=0o700,exist_ok=True)
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=10,check=True)
 return p.stdout.strip()
def read():
 if list(Path('/sys/class/backlight').glob('*')):
  value=run(['brightnessctl','-c','backlight','-m','info']).split(',')[3].rstrip('%')
  return {'available':True,'value':int(value),'backend':'backlight'}
 fields=run(['ddcutil','getvcp','10','--brief']).split()
 if fields[:3]!=['VCP','10','C']:raise ValueError('Monitor does not expose brightness')
 return {'available':True,'value':round(int(fields[3])*100/int(fields[4])),'maximum':int(fields[4]),'backend':'ddc'}
def main():
 with (state/'lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  cache=state/'value.json'
  try:old=json.loads(cache.read_text())
  except (OSError,ValueError):old={}
  op=sys.argv[1] if len(sys.argv)>1 else 'get'
  cached=old.get('available') and time.time()-old.get('at',0)<4
  current=old if cached else read()
  if op in ('set','change'):
   value=max(1,min(100,round(float(sys.argv[2])+(current['value'] if op=='change' else 0))))
   if current['backend']=='ddc':run(['ddcutil','setvcp','10',str(round(value*current.get('maximum',100)/100))])
   else:run(['brightnessctl','-c','backlight','set',str(value)+'%'])
   current['value']=value
  if not cached or op in ('set','change'):current['at']=time.time()
  tmp=state/'value.tmp';tmp.write_text(json.dumps(current));tmp.replace(cache)
  print(json.dumps(current))
if __name__=='__main__':
 try:main()
 except Exception as error:
  print(json.dumps({'available':False,'error':type(error).__name__}));sys.exit(1)
