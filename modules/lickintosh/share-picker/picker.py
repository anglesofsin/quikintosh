"""Portal protocol adapter. Never infer a source from the selected UI label."""
import json, os, re, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

def run(args, timeout=3):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return ''

def prefixed(data, pos):
    end=data.index(b':',pos); size=int(data[pos:end]); start=end+1
    if size<0 or start+size>len(data): raise ValueError('length')
    return data[start:start+size].decode(),start+size

def sources(env):
    outputs=[];windows=[];spaces=[]
    data=env.get('XDPH_OUTPUT_SHARING_LIST','').encode();pos=0
    while pos<len(data):
        try:
            name,pos=prefixed(data,pos)
            if data[pos:pos+1]!=b':':break
            end=data.index(b';',pos);x,y,w,h=map(int,data[pos+1:end].split(b':'));pos=end+1
            if w>0 and h>0:outputs.append(dict(kind='screen',key=name,title=name,x=x,y=y,w=w,h=h,preview=''))
        except (ValueError,IndexError,UnicodeError):break
    pattern=r'(\d+)\[HC>\](.*?)\[HT>\](.*?)\[HE>\](.*?)\[HA>\]'
    for ident,app,title,address in re.findall(pattern,env.get('XDPH_WINDOW_SHARING_LIST',''),re.S):
        windows.append(dict(kind='window',key=ident,title=title or app,subtitle=app,address=address,preview=''))
    data=env.get('XDPH_WORKSPACE_SHARING_LIST_V3','').encode();pos=0
    while pos<len(data):
        try:
            end=data.index(b'[HN>]',pos);ident=int(data[pos:end]);name,pos=prefixed(data,end+5)
            if data[pos:pos+5]!=b'[HM>]':break
            pos+=5;end=data.index(b':',pos);count=int(data[pos:end]);pos=end+1;ports=[]
            for _ in range(count):port,pos=prefixed(data,pos);ports.append(port)
            if data[pos:pos+5]!=b'[HE>]':break
            pos+=5
            if ident>0:spaces.append(dict(kind='workspace-id',key=str(ident),title=name,subtitle=', '.join(ports),preview=''))
        except (ValueError,IndexError,UnicodeError):break
    if not data:
        data=env.get('XDPH_WORKSPACE_SHARING_LIST_V2','').encode();pos=0
        while pos<len(data):
            try:
                name,pos=prefixed(data,pos);end=data.index(b';',pos);ident=int(data[pos+1:end]);pos=end+1
                if ident>0:spaces.append(dict(kind='workspace-id',key=str(ident),title=name,preview=''))
            except (ValueError,IndexError,UnicodeError):break
    return [outputs,windows,spaces]

def selection(reply, groups):
    kind=reply.get('kind');key=str(reply.get('key',''));flags='r' if reply.get('remember') else ''
    if kind=='region':
        match=re.fullmatch(r'(-?\d+),(-?\d+),(\d+),(\d+)',key)
        if not match:return ''
        x,y,w,h=map(int,match.groups());areas=[]
        for m in groups[0]:
            left=max(x,m['x']);top=max(y,m['y']);right=min(x+w,m['x']+m['w']);bottom=min(y+h,m['y']+m['h'])
            if right>left and bottom>top:areas.append(((right-left)*(bottom-top),m,left,top,right-left,bottom-top))
        if not areas:return ''
        _,m,x,y,w,h=max(areas,key=lambda a:a[0]);value=f"region:{m['key']}@{x-m['x']},{y-m['y']},{w},{h}"
    else:
        if not any(item['kind']==kind and item['key']==key for group in groups for item in group):return ''
        value=f'{kind}:{key}'
    if any(c in value for c in '\r\n'):return ''
    return '[SELECTION]'+flags+'/'+value

def main():
    groups=sources(os.environ)
    with tempfile.TemporaryDirectory(prefix='quickintosh-share-') as folder:
        root=Path(folder); response=root/'response.json'
        # Capture before mapping the picker. Limit image size and capture time;
        # failure leaves a neutral source card rather than blocking selection.
        monitors=json.loads(run(['hyprctl','monitors','-j']) or '[]')
        clients=json.loads(run(['hyprctl','clients','-j']) or '[]')
        for i,m in enumerate(groups[0]):
            info=next((v for v in monitors if v['name']==m['key']),{})
            m['subtitle']=info.get('description','')+f" · {m['w']} × {m['h']}"
            path=root/f'display-{i}.png'
            run(['grim','-s','0.35','-o',m['key'],str(path)],2)
            if path.exists():
                m['preview']=path.as_uri()
                with Image.open(path) as im:
                    for j,item in enumerate(groups[1]):
                        client=next((c for c in clients if c.get('address')==item['address'] and c.get('mapped') and not c.get('hidden') and c.get('workspace',{}).get('id')==info.get('activeWorkspace',{}).get('id')),None)
                        if not client:continue
                        x,y=client['at'];w,h=client['size']
                        if not (m['x']<=x<m['x']+m['w'] and m['y']<=y<m['y']+m['h']):continue
                        sx=im.width/m['w'];sy=im.height/m['h'];crop=root/f'window-{j}.png'
                        im.crop((max(0,int((x-m['x'])*sx)),max(0,int((y-m['y'])*sy)),min(im.width,int((x+w-m['x'])*sx)),min(im.height,int((y+h-m['y'])*sy)))).save(crop)
                        item['preview']=crop.as_uri()
        config=root/'sources.json';config.write_text(json.dumps(dict(groups=groups,remember='--allow-token' in sys.argv,portuguese=os.environ.get('LANG','').startswith('pt'))))
        env=dict(os.environ,QI_SHARE_DATA=str(config),QI_SHARE_RESPONSE=str(response),QT_QUICK_CONTROLS_STYLE='Basic')
        subprocess.run([os.environ['QI_SHARE_QS'],'-p',str(Path(__file__).with_name('picker.qml'))],env=env,stdout=sys.stderr)
        if response.exists():
            try:answer=selection(json.loads(response.read_text()),groups)
            except (ValueError,TypeError):answer=''
            if answer:print(answer,flush=True)
if __name__=='__main__':main()
