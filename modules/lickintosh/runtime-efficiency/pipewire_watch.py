"""Incremental PipeWire metadata only: no audio/video capture or client control."""
import codecs,json,os,selectors,signal,subprocess,sys,time

class Frames:
 def __init__(self,limit=16*1024*1024):self.buffer='';self.decoder=codecs.getincrementaldecoder('utf-8')();self.json=json.JSONDecoder();self.limit=limit
 def feed(self,data):
  self.buffer+=self.decoder.decode(data);result=[]
  if len(self.buffer)>self.limit:raise ValueError('PipeWire monitor frame exceeded limit')
  while self.buffer.strip():
   self.buffer=self.buffer.lstrip()
   try:value,end=self.json.raw_decode(self.buffer)
   except ValueError:break
   result.append(value);self.buffer=self.buffer[end:]
  return result

def merge(old,new):
 result=dict(old)
 for key,value in new.items():
  if value is None:result.pop(key,None)
  elif isinstance(value,dict) and isinstance(result.get(key),dict):result[key]=merge(result[key],value)
  else:result[key]=value
 return result

PROPS={'media.class','media.role','node.name','node.description','node.disabled','stream.capture.sink','device.class','application.name','application.id','application.process.binary','application.process.id','client.id','api.v4l2.path','link.output.node','link.input.node'}
def metadata(event):
 result={key:event[key] for key in ('id','type') if key in event}
 if 'info' not in event:return result
 if event['info'] is None:result['info']=None;return result
 info=event['info'];out={}
 if 'state' in info:out['state']=info['state']
 if 'props' in info:out['props']={k:v for k,v in info['props'].items() if k in PROPS} if isinstance(info['props'],dict) else info['props']
 if 'params' in info:
  params=info['params']
  if params is None:out['params']=None
  elif 'Props' in params:out['params']={'Props':[{k:v for k,v in item.items() if k in ('mute','channelVolumes','volume')} for item in params['Props']]}
 result['info']=out;return result

class Registry:
 def __init__(self):self.objects={}
 def update(self,events):
  changed=False
  for event in events if isinstance(events,list) else [events]:
   if not isinstance(event,dict) or 'id' not in event:continue
   key=event['id']
   if 'info' in event and event['info'] is None:
    changed=bool(self.objects.pop(key,None)) or changed;continue
   old=self.objects.get(key,{})
   if str(event.get('type',old.get('type',''))).rsplit(':',1)[-1] not in ('Node','Client','Link'):continue
   value=merge(old,metadata(event))
   if value!=old:self.objects[key]=value;changed=True
  return changed
 def values(self):return [self.objects[key] for key in sorted(self.objects)]

def emit(kind,**data):print(json.dumps(dict(type=kind,**data),separators=(',',':')),flush=True)

def monitor():
 proc=subprocess.Popen(['pw-dump','--monitor','--no-colors','--indent','0'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 try:
  selector=selectors.DefaultSelector();selector.register(proc.stdout,selectors.EVENT_READ);frames=Frames();registry=Registry();dirty=False;first=True;deadline=0;heartbeat=time.monotonic()+2
  while True:
   now=time.monotonic();timeout=max(0,min(heartbeat,deadline if dirty else heartbeat)-now)
   events=selector.select(timeout)
   if events:
    data=os.read(proc.stdout.fileno(),65536)
    if not data:raise RuntimeError('PipeWire monitor disconnected')
    for frame in frames.feed(data):
     if registry.update(frame):
      if not dirty:deadline=time.monotonic()+.08
      dirty=True
   now=time.monotonic()
   if dirty and now>=deadline:
    emit('state',data=registry.values());dirty=False;first=False;heartbeat=now+2
   elif now>=heartbeat:
    if first:emit('state',data=registry.values());first=False
    else:emit('heartbeat')
    heartbeat=now+2
 finally:
  selector.close() if 'selector' in locals() else None
  if proc.poll() is None:proc.terminate()
  try:proc.wait(timeout=2)
  except subprocess.TimeoutExpired:proc.kill();proc.wait()

if __name__=='__main__':
 def stop(*_):raise SystemExit(0)
 signal.signal(signal.SIGTERM,stop)
 while True:
  try:monitor()
  except (OSError,ValueError,RuntimeError):emit('unavailable');time.sleep(2)
