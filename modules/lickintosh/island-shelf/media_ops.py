"""Local video, PDF and segmentation jobs; originals are never replaced."""
from pathlib import Path
import json,os,subprocess,mimetypes,shutil,re

class MediaOperations:
    def video_transform(self,paths,event):
        op=event.get('operation','compress');fmt=event.get('format','automatic')
        if op not in ('compress','convert','resize','rotate','metadata'):raise ValueError('Choose a video operation')
        if fmt not in ('automatic','mp4','webm','mkv','gif'):raise ValueError('Choose MP4, WebM, MKV or GIF')
        outputs=[];side=int(event.get('side',0));quality=int(event.get('quality',72));fps=int(event.get('fps',0))
        if not 0<=fps<=240:raise ValueError('Frame rate must be between 1 and 240, or original')
        for src in paths:
            info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(src)],timeout=15))
            if not any(s.get('codec_type')=='video' for s in info.get('streams',[])):raise ValueError('No video stream found')
            target=src.suffix.lstrip('.').lower() if op=='metadata' and fmt=='automatic' else ('mp4' if fmt=='automatic' else fmt)
            if target not in ('mp4','webm','mkv','mov','gif'):target='mp4'
            dst=self.output(src,'.'+target,event.get('destination','downloads'))
            cmd=['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-threads','2','-filter_threads','2','-i',str(src),'-map','0:v:0','-map','0:a?','-threads','2']
            if event.get('stripMetadata',True) or op=='metadata':cmd+=['-map_metadata','-1','-map_chapters','-1']
            if op=='metadata' and target!='gif':cmd+=['-c','copy']
            else:
                filters=[]
                if side:filters.append(f"scale=w='min(iw,{side})':h='min(ih,{side})':force_original_aspect_ratio=decrease:force_divisible_by=2")
                if op=='rotate':filters.append('transpose=clock')
                if fps:filters.append('fps='+str(fps))
                if filters:cmd+=['-vf',','.join(filters)]
                if target=='webm':cmd+=['-c:v','libvpx-vp9','-crf',str(round(63-quality*.5)),'-b:v','0','-deadline','realtime','-cpu-used','5','-c:a','libopus']
                elif target=='gif':cmd+=['-an','-loop','0']
                else:cmd+=['-c:v','libx264','-preset','veryfast','-crf',str(round(40-quality*.25)),'-pix_fmt','yuv420p','-c:a','aac']
            budget=int(event.get('targetBytes',0))
            if budget and op!='metadata' and target!='gif':
                duration=float(info.get('format',{}).get('duration',0))
                if duration<=0:raise ValueError('Cannot determine video duration')
                bitrate=int((budget*.92*8/duration)-128000)
                if bitrate<64000:raise ValueError('Choose a larger target size for this video')
                cmd+=['-b:v',str(bitrate),'-maxrate',str(bitrate),'-bufsize',str(bitrate*2),'-b:a','96k']
            if target in ('mp4','mov'):cmd+=['-movflags','+faststart']
            cmd+=[str(dst)]
            try:
                subprocess.run(cmd,check=True,capture_output=True,timeout=1800)
                if dst.stat().st_size==0:raise ValueError('Video conversion produced no data')
                outputs.append(str(dst))
            except BaseException:dst.unlink(missing_ok=True);raise
        self.add(outputs);return outputs

    def pdf_transform(self,paths,event):
        import pymupdf as fitz
        op=event.get('operation','compress');outputs=[]
        if op not in ('compress','convert','rotate','metadata','pdf','split'):raise ValueError('Choose a PDF operation')
        merged=fitz.open() if op=='pdf' else None
        try:
            for src in paths:
                with fitz.open(src) as doc:
                    if doc.needs_pass:raise ValueError('Unlock the PDF before transforming it')
                    if doc.page_count>2000:raise ValueError('Choose a PDF with at most 2000 pages')
                    if merged is not None:
                        if doc.is_pdf:merged.insert_pdf(doc)
                        else:
                            with fitz.open('pdf',doc.convert_to_pdf()) as converted:merged.insert_pdf(converted)
                        continue
                    if op in ('split','convert'):
                        chosen=str(event.get('pages','')).strip();indices=list(range(doc.page_count))
                        if chosen:
                            indices=[]
                            for part in chosen.split(','):
                                values=part.strip().split('-');first=int(values[0])-1;last=int(values[-1])-1
                                if len(values)>2 or first<0 or last<first or last>=doc.page_count:raise ValueError('Choose a valid page range')
                                indices.extend(range(first,last+1))
                            indices=list(dict.fromkeys(indices))
                        if len(indices)>200:raise ValueError('Export at most 200 pages at once')
                        fmt=event.get('format','png')
                        for index in indices:
                            if op=='convert' and fmt in ('png','jpeg','webp'):
                                dst=self.output(src,f'-page-{index+1}.'+fmt,event.get('destination','downloads'))
                                try:
                                    pix=doc[index].get_pixmap(dpi=144,alpha=False)
                                    if fmt=='webp':
                                        from PIL import Image
                                        Image.frombytes('RGB',[pix.width,pix.height],pix.samples).save(dst,format='WEBP',quality=int(event.get('quality',72)))
                                    else:pix.save(dst)
                                except BaseException:dst.unlink(missing_ok=True);raise
                            else:
                                dst=self.output(src,f'-page-{index+1}.pdf',event.get('destination','downloads'))
                                try:
                                    with fitz.open() as part:part.insert_pdf(doc,from_page=index,to_page=index);part.save(dst,garbage=4,deflate=True)
                                except BaseException:dst.unlink(missing_ok=True);raise
                            outputs.append(str(dst))
                        continue
                    if op=='rotate':
                        for page in doc:page.set_rotation((page.rotation+90)%360)
                    if op=='metadata' or event.get('stripMetadata',True):doc.set_metadata({});doc.del_xml_metadata()
                    if op=='compress':doc.rewrite_images(dpi_threshold=180,dpi_target=144,quality=int(event.get('quality',72)))
                    dst=self.output(src,'.pdf',event.get('destination','downloads'))
                    try:doc.save(dst,garbage=4,deflate=True,use_objstms=1)
                    except BaseException:dst.unlink(missing_ok=True);raise
                    outputs.append(str(dst))
            if merged is not None:
                dst=self.output(paths[0],'.pdf',event.get('destination','downloads'))
                try:merged.save(dst,garbage=4,deflate=True)
                except BaseException:dst.unlink(missing_ok=True);raise
                outputs.append(str(dst))
        finally:
            if merged is not None:merged.close()
        self.add(outputs);return outputs

    def remove_background(self,paths,event):
        for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[key]='2'
        from rembg import remove,new_session
        from PIL import Image,ImageOps
        model=event.get('backgroundModel','u2netp')
        if model not in ('u2net','u2netp'):raise ValueError('Choose a supported background model')
        session=new_session(model,providers=['CPUExecutionProvider']);outputs=[]
        for src in paths:
            dst=self.output(src,'.png',event.get('destination','downloads'))
            try:
                with Image.open(src) as original:
                    image=ImageOps.exif_transpose(original).convert('RGBA')
                    remove(image,session=session).save(dst,format='PNG',optimize=True)
                outputs.append(str(dst))
            except BaseException:dst.unlink(missing_ok=True);raise
        self.add(outputs);return outputs

    def presets(self,event):
        path=self.root/'transform-presets.json'
        try:rows=json.loads(path.read_text())
        except (OSError,ValueError):rows=[]
        if event.get('action')=='savePreset':
            name=str(event.get('name','')).strip()[:48]
            if not name:raise ValueError('Name the preset')
            settings=event.get('settings',{})
            allowed=('operation','quality','format','side','fps','stripMetadata','destination','backgroundModel','targetBytes')
            preset={'name':name,'settings':{k:settings[k] for k in allowed if k in settings}}
            rows=[r for r in rows if r.get('name')!=name][-19:]+[preset]
        elif event.get('action')=='removePreset':rows=[r for r in rows if r.get('name')!=event.get('name')]
        if event.get('action')!='presets':
            tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(rows));tmp.replace(path)
        return dict(type='presets',items=rows)
