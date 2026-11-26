import json,os,re,struct,subprocess
from pathlib import Path

def tint(source,target,color):
    target.mkdir(parents=True,exist_ok=True)
    channels=tuple(int(color[i:i+2],16) for i in (1,3,5))
    for p in source.iterdir():
        out=target/p.name
        if p.is_symlink():
            if not out.exists():out.symlink_to(os.readlink(p))
            continue
        data=bytearray(p.read_bytes())
        if data[:4]!=b'Xcur':continue
        _,_,_,count=struct.unpack_from('<4I',data)
        for i in range(count):
            typ,_,pos=struct.unpack_from('<3I',data,16+i*12)
            if typ!=0xfffd0002:continue
            header,_,_,_,w,h=struct.unpack_from('<6I',data,pos)
            for j in range(w*h):
                at=pos+header+j*4;pixel=struct.unpack_from('<I',data,at)[0];a=pixel>>24
                if not a:continue
                r,g,b=(pixel>>16)&255,(pixel>>8)&255,pixel&255
                brightness=max(r,g,b)*255/a
                if brightness>150:continue # preserve the contrasting outline
                factor=.65+.35*brightness/150
                rr,gg,bb=(min(a,round(c*factor*a/255)) for c in channels)
                struct.pack_into('<I',data,at,(a<<24)|(rr<<16)|(gg<<8)|bb)
        out.write_bytes(data)

def apply(values):
    def get(key,default):return values.get('qi-cursor:'+key,default)
    size=max(16,min(96,int(get('size',31))));theme=get('theme','MacTahoe-cursors');color=get('color','original')
    if theme not in ['MacTahoe-cursors','MacTahoe-dark-cursors','Bibata-Modern-Classic']:raise ValueError('Unknown cursor theme')
    if color!='original':
        if not re.fullmatch('#[0-9a-fA-F]{6}',str(color)):raise ValueError('Cursor color must be #RRGGBB')
        dirs=[Path('/run/current-system/sw/share/icons'),*[Path(d)/'icons' for d in os.environ.get('XDG_DATA_DIRS','').split(':') if d],Path.home()/'.local/share/icons']
        source=next((p/theme/'cursors' for p in dirs if (p/theme/'cursors').is_dir()),None)
        if source is None:raise ValueError('Cursor theme is not installed')
        name='Quickintosh-'+theme+'-'+color[1:].lower();dest=Path.home()/'.local/share/icons'/name
        if not (dest/'index.theme').exists():
            tint(source,dest/'cursors',color);(dest/'index.theme').write_text('[Icon Theme]\nName='+name+'\n')
        theme=name
    opts=dict(size=size,theme=theme,shake=bool(get('shake',True)),scale=max(1.5,min(4,float(get('scale',2.5)))),sensitivity=max(.5,min(2,float(get('sensitivity',1)))))
    lua='{'+','.join(k+'='+('true' if v is True else 'false' if v is False else json.dumps(v)) for k,v in opts.items())+'}'
    path=Path.home()/'.config/quickintosh/cursor.lua';path.parent.mkdir(parents=True,exist_ok=True)
    content='return '+lua+'\n'
    if path.exists() and path.read_text()==content:return
    path.write_text(content)
    result=subprocess.run(['hyprctl','eval','if quickintosh_cursor then quickintosh_cursor('+lua+') end'],capture_output=True,text=True,timeout=4)
    if result.returncode:raise ValueError(result.stderr or result.stdout)
