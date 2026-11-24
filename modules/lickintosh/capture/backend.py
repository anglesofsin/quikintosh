"""Private stdio capture worker. Native Quickshell owns selection and annotation."""
import json,os,sys,subprocess,tempfile,time,uuid,signal,ctypes,threading,re,colorsys,urllib.parse,urllib.request,math
from pathlib import Path
from datetime import datetime
from PIL import Image,ImageFilter

def interface_scale():
    try:
        value=float(os.environ.get('QT_SCALE_FACTOR','1'))
        return value if math.isfinite(value) and .75<=value<=2 else 1
    except (ValueError,TypeError):return 1

def run(args,**kwargs):return subprocess.run(args,check=True,timeout=kwargs.pop('timeout',15),**kwargs)
def output(args):return subprocess.check_output(args,text=True,timeout=8)
def emit(kind,**data):print(json.dumps(dict(type=kind,**data),ensure_ascii=False),flush=True)
def notify(title,body='',path=None):
    def worker():
        try:
            args=['notify-send','-a','Lickintosh Capture',title,body]
            if path:args[1:1]=['--action=default=Show in folder']
            result=subprocess.run(args,capture_output=True,text=True,timeout=30)
            if path and result.stdout.strip()=='default':
                subprocess.run(['busctl','--user','call','org.freedesktop.FileManager1','/org/freedesktop/FileManager1','org.freedesktop.FileManager1','ShowItems','ass','1',Path(path).as_uri(),''],capture_output=True,timeout=5)
        except (OSError,subprocess.SubprocessError):pass
    threading.Thread(target=worker,daemon=True).start()
_clipboard=None
def copy_data(path=None,text=None):
    global _clipboard
    previous=_clipboard
    args=['wl-copy','--foreground','--type','image/png' if path else 'text/plain']
    if path:
        with Path(path).open('rb') as source:_clipboard=subprocess.Popen(args,stdin=source,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    else:
        _clipboard=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        _clipboard.stdin.write(text.encode());_clipboard.stdin.close()
    time.sleep(.06)
    if _clipboard.poll() not in (None,0):raise RuntimeError('Clipboard provider failed')
    if previous and previous.poll() is None:
        previous.terminate()
        try:previous.wait(timeout=1)
        except subprocess.TimeoutExpired:previous.kill()
def copy_png(path):copy_data(path=path)
def filename(config,size,mode):
    now=datetime.now();values={'date':now.strftime('%Y-%m-%d'),'time':now.strftime('%H-%M-%S'),'datetime':now.strftime('%Y-%m-%d_%H-%M-%S'),'w':str(size[0]),'h':str(size[1]),'mode':mode}
    text=str(config.get('filenameTemplate','Screenshot_{datetime}_{w}x{h}.png'))
    for k,v in values.items():text=text.replace('{'+k+'}',v)
    text=re.sub(r'[/\\\x00-\x1f]','_',text)
    return (text[:180] or 'Screenshot.png') if text.lower().endswith('.png') else text[:175]+'.png'
def save_png(source,config,mode,target=None):
    with Image.open(source) as image:size=image.size;image.verify()
    if target:
        from urllib.parse import unquote,urlparse
        target=Path(unquote(urlparse(target).path)) if str(target).startswith('file:') else Path(target).expanduser()
        if target.suffix.lower()!='.png':target=target.with_name(target.name+'.png')
        stem=target.stem;counter=1;original=target
        while target.exists():target=original.with_name(stem+'_'+str(counter)+'.png');counter+=1
    else:
        directory=Path(config.get('directory','~/Desktop')).expanduser();directory.mkdir(parents=True,exist_ok=True)
        target=directory/filename(config,size,mode)
        stem=target.stem;counter=1
        while target.exists():target=directory/(stem+'_'+str(counter)+'.png');counter+=1
    target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_name('.'+target.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        temp.write_bytes(Path(source).read_bytes());temp.chmod(0o600);temp.replace(target)
    finally:temp.unlink(missing_ok=True)
    return str(target)

class Worker:
    def __init__(self,root):self.root=Path(root);self.frame=None;self.meta=None;self.session=None;self.pins=set();self.last_pixel=(0,0,0);self.recorder=None;self.mic_recorder=None;self.record_lock=threading.Lock();self.record_output=None;self.record_config={};self.record_pidfile=Path.home()/".local/state/nixos-rice/wf-recorder.pid"
    def owned(self,path):
        path=Path(path).resolve()
        if not path.is_relative_to(self.root.resolve()) or not path.is_file():raise ValueError('Invalid capture file')
        return path
    def prune(self):
        for path in self.root.iterdir():
            if path.is_file() and str(path) not in self.pins:path.unlink(missing_ok=True)
    def capture(self,request):
        self.prune()
        monitors=json.loads(output(['hyprctl','monitors','-j']));cursor=json.loads(output(['hyprctl','cursorpos','-j']))
        def logical(m):
            w,h=m['width'],m['height']
            if int(m.get('transform',0))%2:w,h=h,w
            return w/m.get('scale',1),h/m.get('scale',1)
        monitor=next((m for m in monitors if m['x']<=cursor['x']<m['x']+logical(m)[0] and m['y']<=cursor['y']<m['y']+logical(m)[1]),next((m for m in monitors if m.get('focused')),monitors[0]))
        self.session=uuid.uuid4().hex;path=self.root/(self.session+'.png');run(['grim','-o',monitor['name'],str(path)],stderr=subprocess.PIPE)
        with Image.open(path) as raw:self.frame=raw.convert('RGB')
        w,h=logical(monitor);ui_scale=interface_scale();w/=ui_scale;h/=ui_scale;factor=self.frame.width/w
        clients=json.loads(output(['hyprctl','clients','-j']));active=monitor.get('activeWorkspace',{}).get('id');special=monitor.get('specialWorkspace',{}).get('id',0);visible_workspaces={m.get(key,{}).get('id') for m in monitors for key in ['activeWorkspace','specialWorkspace']}
        clients=sorted(clients,key=lambda c:((4000 if c.get('pinned') else 0)+(2000 if c.get('workspace',{}).get('id')==special and special else 0)+(1000 if c.get('floating') else 0)-c.get('focusHistoryID',9999)),reverse=True)
        windows=[]
        for c in clients:
            if c.get('hidden') or c.get('mapped') is False or (not c.get('pinned') and c.get('workspace',{}).get('id') not in visible_workspaces):continue
            x,y=c.get('at',[0,0]);cw,ch=c.get('size',[0,0]);x=(x-monitor['x'])/ui_scale;y=(y-monitor['y'])/ui_scale;cw/=ui_scale;ch/=ui_scale;x2=min(w,x+cw);y2=min(h,y+ch);x=max(0,x);y=max(0,y)
            if x2>x and y2>y:windows.append(dict(x=x,y=y,w=x2-x,h=y2-y))
        self.meta=dict(filename=filename(request.get('config',{}),self.frame.size,'region'),session=self.session,path=str(path),exportPath=str(self.root/(self.session+'-export.png')),monitor=monitor['name'],width=w,height=h,pixelWidth=self.frame.width,pixelHeight=self.frame.height,factor=factor,uiScale=ui_scale,windows=windows,cursorX=(cursor['x']-monitor['x'])/ui_scale,cursorY=(cursor['y']-monitor['y'])/ui_scale)
        config=request.get('config',{});mode=request.get('mode','region')
        if mode=='recordFull':
            self.start_record([0,0,w,h],config);return
        if mode=='fullscreen':
            copy_png(path);saved=save_png(path,config,'fullscreen') if config.get('autoSave',True) else ''
            emit('complete',action='fullscreen',saved=saved,flash=config.get('feedback','notification')!='off',monitor=monitor['name'])
        else:emit('prepared',mode=mode,**self.meta)
    def edit_image(self,request):
        from PIL import ImageOps
        source=request['path'];source=urllib.parse.unquote(urllib.parse.urlsplit(source).path) if str(source).startswith('file:') else source
        with Image.open(source) as original:image=ImageOps.exif_transpose(original).convert('RGBA')
        monitors=json.loads(output(['hyprctl','monitors','-j']));monitor=next((m for m in monitors if m.get('focused')),monitors[0])
        sw,sh=monitor['width']/monitor.get('scale',1),monitor['height']/monitor.get('scale',1)
        if int(monitor.get('transform',0))%2:sw,sh=sh,sw
        ui_scale=interface_scale();sw/=ui_scale;sh/=ui_scale
        fit=min(1,(sw-140)/image.width,(sh-180)/image.height);dw,dh=image.width*fit,image.height*fit;factor=min(2,1/fit)
        x,y=(sw-dw)/2,(sh-dh)/2
        self.prune();self.session=uuid.uuid4().hex;path=self.root/(self.session+'.png')
        self.frame=Image.new('RGB',(round(sw*factor),round(sh*factor)),'#161619');image=image.resize((round(dw*factor),round(dh*factor)),Image.Resampling.LANCZOS);self.frame.paste(image,(round(x*factor),round(y*factor)),image);self.frame.save(path)
        self.meta=dict(filename=Path(source).stem+' annotated.png',session=self.session,path=str(path),exportPath=str(self.root/(self.session+'-export.png')),monitor=monitor['name'],width=sw,height=sh,pixelWidth=self.frame.width,pixelHeight=self.frame.height,factor=factor,uiScale=ui_scale,windows=[],cursorX=sw/2,cursorY=sh/2,editSelection=dict(x=x,y=y,w=dw,h=dh))
        emit('prepared',mode='annotate',**self.meta)
    def command(self,r):
        action=r.get('action')
        if action=='prepare':return self.capture(r)
        if action=='editImage':return self.edit_image(r)
        if action=='stopRecord':self.stop_record();return
        if action=='pinFile':
            source=Path(r['path']).expanduser().resolve()
            with Image.open(source) as image:
                image.load();size=image.size
                if image.width*image.height>100_000_000:raise ValueError('Image is too large to pin')
                target=self.root/('import-'+uuid.uuid4().hex+'.png');image.convert('RGBA').save(target)
            if source.parent==Path(os.environ.get('XDG_RUNTIME_DIR','/nonexistent')) and source.name.startswith('lickintosh-camera-'):source.unlink(missing_ok=True)
            self.pins.add(str(target));emit('pinned',path=str(target),id=uuid.uuid4().hex,width=min(600,size[0]),height=min(600,size[0])*size[1]/size[0],monitor=self.meta['monitor'] if self.meta else '')
            return
        if action=='colorResult':
            rgb=self.last_pixel;h,s,v=colorsys.rgb_to_hsv(*(c/255 for c in rgb));_,l,sl=colorsys.rgb_to_hls(*(c/255 for c in rgb));hexvalue='#%02X%02X%02X'%rgb;copy_data(text=hexvalue)
            emit('result',title='Pixel color',text=f'{hexvalue}\nRGB: {rgb[0]}, {rgb[1]}, {rgb[2]}\nHSV: {h*360:.1f}°, {s*100:.1f}%, {v*100:.1f}%\nHSL: {h*360:.1f}°, {sl*100:.1f}%, {l*100:.1f}%',palette=[hexvalue]);return
        if action=='cancel':self.frame=None;self.prune();return
        if action=='unpin':
            path=self.owned(r['path']);self.pins.discard(str(path));path.unlink(missing_ok=True);return
        if action=='sample' and self.frame:
            x=max(0,min(self.frame.width-1,int(r['x'])));y=max(0,min(self.frame.height-1,int(r['y'])));rgb=self.frame.getpixel((x,y));self.last_pixel=rgb;emit('sample',x=x,y=y,rgb=list(rgb),hex='#%02X%02X%02X'%rgb);return
        if action=='text':copy_data(text=str(r.get('text','')));return
        if action=='mosaic' and self.frame:
            factor=self.meta['factor'];box=r['box'];rect=tuple(round(v*factor) for v in box);x,y,w,h=rect
            if w<1 or h<1:return
            image=self.frame.crop((x,y,x+w,y+h));block=max(2,int(r.get('block',12)*factor))
            if r.get('effect')=='blur':image=image.filter(ImageFilter.GaussianBlur(block/2))
            else:image=image.resize((max(1,w//block),max(1,h//block)),Image.Resampling.BOX).resize((w,h),Image.Resampling.NEAREST)
            path=self.root/(self.session+'-mosaic-'+str(int(r['id']))+'.png');image.save(path);emit('mosaic',id=r['id'],path=str(path),box=box);return
        if action=='record':self.start_record(r['box'],r.get('config',{}));return
        if action=='finish':
            source=self.owned(r['path']);kind=r.get('kind','copy');config=r.get('config',{});saved=''
            if kind=='qr':
                result=subprocess.run(['zbarimg','--quiet','--raw',str(source)],capture_output=True,text=True,timeout=10)
                if result.returncode:emit('result',title='QR / barcode',text='No readable QR code or barcode found.');return
                text=result.stdout.strip();copy_data(text=text);emit('result',title='QR / barcode',text=text);return
            if kind=='palette':
                with Image.open(source) as image:
                    image=image.convert('RGB');image.thumbnail((256,256),Image.Resampling.NEAREST);quantized=image.quantize(colors=12,method=Image.Quantize.MEDIANCUT);palette=quantized.getpalette();colors=[];picked=[]
                    for count,index in sorted(quantized.getcolors() or [],reverse=True):
                        rgb=tuple(palette[index*3:index*3+3])
                        if picked and (count < image.width*image.height*.01 or any(sum((a-b)**2 for a,b in zip(rgb,other)) < 28**2 for other in picked)):continue
                        picked.append(rgb);colors.append('#%02X%02X%02X'%rgb)
                        if len(colors)==8:break
                emit('result',title='Color palette',palette=colors,text='\n'.join(colors));return
            if kind=='lens':
                # Only reached after the explicit in-editor upload confirmation.
                response=subprocess.check_output(['curl','--fail','--silent','--show-error','--connect-timeout','10','--max-time','45','-F','files[]=@'+str(source),'https://uguu.se/upload'],text=True,timeout=50)
                data=json.loads(response);url=data.get('files',[{}])[0].get('url','');parsed=urllib.parse.urlparse(url)
                if parsed.scheme!='https' or not parsed.netloc:raise ValueError('Image upload did not return a valid HTTPS address')
                subprocess.Popen(['xdg-open','https://lens.google.com/uploadbyurl?url='+urllib.parse.quote(url,safe='')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                emit('complete',action='lens',saved='');return
            if kind=='ocr':
                text=output(['tesseract',str(source),'stdout','-l',config.get('ocrLanguages','eng'),'--psm','6']).strip()
                if not text:emit('emptyOcr');return
                copy_data(text=text);emit('complete',action='ocr',saved='');return
            if kind=='pin':self.pins.add(str(source));emit('pinned',path=str(source),id=uuid.uuid4().hex,width=r['width'],height=r['height'],monitor=self.meta['monitor']);return
            if kind in ['copy','save']:copy_png(source)
            if kind=='save' or config.get('autoSave',False):saved=save_png(source,config,'region',r.get('target') or None)
            emit('complete',action=kind,saved=saved)

    def start_record(self,box,config):
        if self.recorder and self.recorder.poll() is None:raise ValueError('A screen recording is already active')
        if self.record_pidfile.exists():
            try:os.kill(int(self.record_pidfile.read_text()),0);raise ValueError('Another screen recorder is active')
            except (OSError,ValueError) as error:
                if isinstance(error,ValueError) and str(error)=='Another screen recorder is active':raise
        monitors=json.loads(output(['hyprctl','monitors','-j']));monitor=next((m for m in monitors if m['name']==self.meta['monitor']),None)
        if monitor is None:raise ValueError('Capture display is unavailable')
        ui_scale=self.meta.get('uiScale',1);x,y,w,h=[float(value)*ui_scale for value in box];geometry=f'{int(monitor["x"]+x)},{int(monitor["y"]+y)} {max(2,int(w))}x{max(2,int(h))}'
        directory=Path(config.get('videoDirectory','~/Videos/Screencasts')).expanduser();directory.mkdir(parents=True,exist_ok=True)
        name='Recording_'+datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_'+uuid.uuid4().hex[:4]
        source=directory/('.'+name+'.mp4');self.record_output=directory/(name+('.gif' if config.get('recordFormat')=='gif' else '.mp4'));self.record_config=dict(config,source=str(source))
        args=['wf-recorder','-g',geometry,'-f',str(source)]
        if not config.get('recordCursor',True):args.append('--no-cursor')
        if config.get('recordSystemAudio'):
            args.append('--audio='+output(['pactl','get-default-sink']).strip()+'.monitor')
        elif config.get('recordMic'):args.append('--audio='+output(['pactl','get-default-source']).strip())
        if config.get('recordSystemAudio') and config.get('recordMic'):
            mic=directory/('.'+name+'-mic.wav');self.record_config['mic']=str(mic)
            self.mic_recorder=subprocess.Popen(['ffmpeg','-nostdin','-y','-f','pulse','-i',output(['pactl','get-default-source']).strip(),str(mic)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.recorder=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.record_pidfile.parent.mkdir(parents=True,exist_ok=True);self.record_pidfile.write_text(str(self.recorder.pid))
        process=self.recorder;emit('recording')
        def watch():
            try:process.wait(timeout=max(3,min(3600,int(config.get('recordMaxSeconds',120)))))
            except subprocess.TimeoutExpired:pass
            self.stop_record()
        threading.Thread(target=watch,daemon=True).start()
    def stop_record(self):
        if not self.record_lock.acquire(blocking=False):return
        try:
            process=self.recorder
            if process is None:return
            self.recorder=None
            if process.poll() is None:process.send_signal(signal.SIGINT)
            try:process.wait(timeout=8)
            except subprocess.TimeoutExpired:process.kill();process.wait()
            if self.record_pidfile.exists() and self.record_pidfile.read_text().strip()==str(process.pid):self.record_pidfile.unlink(missing_ok=True)
            if self.mic_recorder:
                if self.mic_recorder.poll() is None:self.mic_recorder.send_signal(signal.SIGINT)
                self.mic_recorder.wait(timeout=5);self.mic_recorder=None
            source=Path(self.record_config['source']);target=self.record_output
            if not source.exists() or source.stat().st_size<512:raise ValueError('Screen recorder did not produce a video')
            if target.suffix=='.gif':
                run(['ffmpeg','-nostdin','-y','-i',str(source),'-filter_complex',r'fps=15,scale=min(960\,iw):-2:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse',str(target)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=180)
                source.unlink(missing_ok=True)
            elif self.record_config.get('mic'):
                run(['ffmpeg','-nostdin','-y','-i',str(source),'-i',self.record_config['mic'],'-filter_complex','[0:a][1:a]amix=inputs=2[a]','-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-movflags','+faststart',str(target)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=90)
                source.unlink(missing_ok=True)
            else:source.replace(target)
            if self.record_config.get('mic'):Path(self.record_config['mic']).unlink(missing_ok=True)
            notify('Recording saved',str(target),str(target));emit('recorded',path=str(target))
        except (OSError,ValueError,subprocess.SubprocessError) as error:emit('error',message=str(error),recording=False)
        finally:self.record_lock.release()

def main():
    signal.signal(signal.SIGTERM,lambda *_:sys.exit(0))
    parent=os.getppid();ctypes.CDLL(None).prctl(1,signal.SIGTERM,0,0,0)
    if parent==1 or os.getppid()!=parent:return
    with tempfile.TemporaryDirectory(prefix='lickintosh-shot-',dir=os.environ.get('XDG_RUNTIME_DIR')) as directory:
        worker=Worker(directory);emit('ready')
        try:
            for line in sys.stdin:
                try:worker.command(json.loads(line))
                except (ValueError,KeyError,IndexError,OSError,RuntimeError,subprocess.SubprocessError) as error:emit('error',message=str(error)[:300])
        finally:worker.stop_record()
if __name__=='__main__':main()
