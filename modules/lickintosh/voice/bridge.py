"""Loopback call metadata broker. Only bounded avatar images are cached on disk."""
import asyncio,json,re,sys,os,signal,ctypes,time,uuid
from websockets.asyncio.server import serve
from avatar_cache import AvatarCache
CLIENTS=('canary','ptb','stable','equibop')
ORIGINS=('https://canary.discord.com','https://ptb.discord.com','https://discord.com')

def parent_lifetime():
    parent=os.getppid()
    if sys.platform=='linux': ctypes.CDLL(None).prctl(1,signal.SIGTERM,0,0,0)
    if os.getppid()!=parent or parent==1: os.kill(os.getpid(),signal.SIGTERM)

def clean(value):
    if not isinstance(value,dict) or value.get('type')!='voice' or value.get('version')!=1 or value.get('client') not in CLIENTS:
        return None
    participants=[]
    if not isinstance(value.get('participants'),list): return None
    for p in value['participants'][:64]:
        if not isinstance(p,dict) or not re.fullmatch(r'\d{1,24}',str(p.get('id',''))): continue
        avatar=str(p.get('avatar',''))
        if not re.fullmatch(r'https://cdn\.discordapp\.com/avatars/\d{1,24}/[a-zA-Z0-9_]+\.png\?size=80',avatar): avatar=''
        participants.append(dict(id=str(p['id']),name=str(p.get('name','Participant'))[:100],avatar=avatar,
            **{k:p.get(k) is True for k in ('self','muted','deaf','speaking')}))
    return dict(state=value.get('state') if value.get('state') in ('incoming','active','idle') else 'active',incomingControls=value.get('incomingControls') is True,client=value['client'],active=value.get('active') is True,channel=str(value.get('channel',''))[:160],
        channelId=str(value.get('channelId',''))[:24],
        image=str(value.get('image','')) if re.fullmatch(r'https://cdn\.discordapp\.com/(?:icons|channel-icons|avatars)/\d{1,24}/[a-zA-Z0-9_]+\.png\?size=80',str(value.get('image',''))) else '',
        controls=value.get('controls') is True, joinedAt=min(time.time()*1000,max(0,float(value.get('joinedAt') or time.time()*1000))),
        guild=str(value.get('guild',''))[:160],streamer=value.get('streamer') is True,participants=participants)

class Broker:
    def __init__(self,emit): self.sessions={}; self.emit=emit; self.generic=None; self.images=None; self.external={}
    def publish(self):
        # One snapshot per client, newest connection wins; never combine accounts.
        clients={}
        for value in self.sessions.values(): clients[value['client']]=value
        for name,value in self.external.items():
            if not clients.get(name,{}).get('active'):clients[name]=value
        if self.images:
            self.images.needed=set()
            cached={}
            for name,call in clients.items():
                data=dict(call);data['image']=self.images.image(call.get('image',''))
                data['participants']=[dict(p,avatar=self.images.image(p.get('avatar',''))) for p in call['participants']]
                cached[name]=data
            clients=cached
        self.emit(dict(clients=clients,generic=self.generic))
    def update(self,key,value):
        value=clean(value)
        if value is not None:
            previous=self.sessions.get(key,{})
            value['session']=previous.get('session') or uuid.uuid4().hex
            self.sessions[key]=value; self.publish()
    def remove(self,key):
        self.sessions.pop(key,None); self.publish()

async def pipewire(broker):
    """Only explicit Communication roles; microphone usage alone is not a call."""
    nodes={}; process=None
    try:
        process=await asyncio.create_subprocess_exec('pw-dump','-m',stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL,preexec_fn=parent_lifetime)
        decoder=json.JSONDecoder(); buffer=''; previous=None
        while True:
            chunk=await process.stdout.read(65536)
            if not chunk: break
            buffer+=chunk.decode('utf-8',errors='replace')
            while buffer.strip():
                buffer=buffer.lstrip()
                try: events,end=decoder.raw_decode(buffer)
                except ValueError: break
                buffer=buffer[end:]
                if not isinstance(events,list): continue
                for event in events:
                    if not isinstance(event,dict): continue
                    node_id=event.get('id'); info=event.get('info')
                    if not info: nodes.pop(node_id,None); continue
                    if node_id in nodes and info.get('state'):nodes[node_id]['_state']=info['state']
                    if event.get('type','').endswith(':Node'):
                        props=info.get('props')
                        if isinstance(props,dict): nodes[node_id]=dict(props,**{'_state':info.get('state','running')})
                # Discord exposes a distinct WebRTC duplex stream during voice.
                # Use it only as a degraded fallback, never as fabricated metadata.
                external={}
                for client,binary in [('canary','discordcanary'),('ptb','discordptb'),('stable','discord'),('equibop','equibop')]:
                    matching=[p for p in nodes.values() if str(p.get('application.process.binary','')).lower().strip('.').removesuffix('-wrapped')==binary and str(p.get('application.name','')).lower()=='webrtc voiceengine' and p.get('_state')=='running']
                    kinds={p.get('media.class') for p in matching}
                    if {'Stream/Input/Audio','Stream/Output/Audio'}.issubset(kinds):
                        external[client]=dict(client=client,active=True,channel='Discord '+client.title()+' call',channelId='',image='',controls=False,guild='',streamer=False,participants=[],external=True)
                external_changed=external!=broker.external
                broker.external=external
                calls=sorted({str(p.get('application.name') or p.get('application.process.binary') or 'Communication app')[:100]
                    for p in nodes.values() if str(p.get('media.role','')).lower() in ('communication','phone')
                    and p.get('_state')=='running' and str(p.get('media.class','')).startswith('Stream/')
                    and not any(x in str(p.get('application.name','')).lower() for x in ('discord','equibop'))})
                value=dict(client='system',active=True,channel=' · '.join(calls),guild='',streamer=False,participants=[]) if calls else None
                if value!=previous or external_changed: previous=value; broker.generic=value; broker.publish()
            if len(buffer)>8*1024*1024: break
    except (OSError,ValueError): pass
    finally:
        broker.generic=None; broker.external={}; broker.publish()
        if process and process.returncode is None:
            process.terminate(); await process.wait()

async def main():
    broker=Broker(lambda value:print(json.dumps(value,separators=(',',':')),flush=True))
    broker.images=AvatarCache(broker.publish)
    async def connection(ws):
        try:
            async for data in ws:
                if not isinstance(data,str): continue
                try:
                    value=json.loads(data)
                    if isinstance(value,dict) and value.get('type')=='control':
                        action=value.get('action')
                        if action not in ('mute','deaf','disconnect','accept','reject'): continue
                        for target,call in list(broker.sessions.items()):
                            if (call.get('incomingControls') and call.get('state')=='incoming' if action in ('accept','reject') else call.get('controls') and call.get('state')!='incoming') and call.get('active') and call.get('session')==value.get('session') and call.get('channelId')==value.get('channelId'):
                                await target.send(json.dumps(dict(type='control',action=action,channelId=call['channelId'])))
                                break
                    else: broker.update(ws,value)
                except (ValueError,TypeError): continue
        finally:
            if ws in broker.sessions: broker.remove(ws)
    broker.publish()
    try:
        async with serve(connection,'127.0.0.1',6891,origins=ORIGINS,max_size=65536,max_queue=8,ping_interval=15,ping_timeout=10):
            monitor=asyncio.create_task(pipewire(broker))
            try: await asyncio.Future()
            finally:
                monitor.cancel()
                try: await monitor
                except asyncio.CancelledError: pass
    except OSError:
        # Status goes to UI, never silently reuse an unrelated local service.
        print(json.dumps({'clients':{},'error':'Voice bridge port 6891 is already in use'}),flush=True)
        return 1
async def send_control():
    from websockets.asyncio.client import connect
    async with connect('ws://127.0.0.1:6891/voice',origin='https://discord.com') as ws:
        await ws.send(json.dumps(dict(type='control',session=sys.argv[2],channelId=sys.argv[3],action=sys.argv[4])))

if __name__=='__main__':
    if len(sys.argv)==5 and sys.argv[1]=='control':
        asyncio.run(send_control()); sys.exit(0)
    parent_lifetime()
    sys.exit(asyncio.run(main()))
