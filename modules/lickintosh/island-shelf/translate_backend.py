"""Explicit online translation; input goes over stdin, never shell interpolation."""
import json,subprocess,sys,re,shutil,os,signal

def translate(event):
 text=event.get('text','');source=event.get('source','auto');target=event.get('target','pt')
 if not isinstance(text,str) or not text.strip() or len(text)>10000:raise ValueError('Enter between 1 and 10,000 characters')
 if not all(isinstance(code,str) and re.fullmatch(r'(auto|[a-z]{2,3}(-[A-Za-z]{2,4})?)',code) for code in (source,target)):raise ValueError('Invalid language')
 if target=='auto':raise ValueError('Choose a target language')
 if not shutil.which('trans'):raise ValueError('Translate Shell is not installed')
 process=subprocess.Popen(['trans','-no-init','-brief','-no-ansi','-engine','google','-source',source,'-target',target,'-input','/dev/stdin'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
 try:
  output,_=process.communicate(text,timeout=25)
  output=output.strip()
  if process.returncode or not output:raise ValueError('Translation unavailable. Check the network and try again.')
 finally:
  if process.poll() is None:
   try:os.killpg(process.pid,signal.SIGKILL)
   except ProcessLookupError:pass
   process.wait()
 return {'text':output[:20000]}
if __name__=='__main__':
 signal.signal(signal.SIGTERM,lambda *_:sys.exit(143))
 try:print(json.dumps(translate(json.loads(sys.stdin.readline(65536)))))
 except Exception as error:print(json.dumps({'error':str(error)}));sys.exit(1)
