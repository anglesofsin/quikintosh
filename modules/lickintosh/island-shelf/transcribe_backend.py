"""Local, explicit microphone/file transcription. Temporary recordings never persist."""
import json,os,selectors,shutil,signal,subprocess,sys,tempfile,time
from pathlib import Path

class Transcriber:
    def __init__(self,emit):self.emit=emit;self.process=None
    def cancel(self,*_):
        if self.process and self.process.poll() is None:
            try:os.killpg(self.process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        raise SystemExit(143)
    def command(self,args,timeout):
        self.process=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,start_new_session=True)
        try:_,error=self.process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:self.cancel()
        if self.process.returncode:raise ValueError(error.decode(errors='replace')[-700:] or 'Audio processing failed')
    def run(self,event):
        binary=shutil.which('whisper-cli');model=Path(os.environ.get('QUICKINTOSH_WHISPER_MODEL',str(Path.home()/'.local/share/quickintosh/models/ggml-base.bin')))
        if not binary or not model.is_file():raise ValueError('The local speech model is unavailable')
        language=event.get('language','auto')
        if language not in ('auto','pt','en','es','fr','de','it','ja','ko','zh','ru'):raise ValueError('Choose a supported transcription language')
        with tempfile.TemporaryDirectory(prefix='quickintosh-transcribe-') as folder:
            wav=Path(folder)/'audio.wav';output=Path(folder)/'transcript'
            if event.get('action')=='record':
                environment=dict(os.environ,PULSE_PROP='application.name=Quickintosh-Transcribe media.name=Microphone')
                self.process=subprocess.Popen(['ffmpeg','-v','error','-nostats','-f','pulse','-i','default','-t','60','-ar','16000','-ac','1','-c:a','pcm_s16le','-y',str(wav)],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,start_new_session=True,env=environment)
                self.emit(dict(type='phase',value='recording'));selector=selectors.DefaultSelector();selector.register(sys.stdin,selectors.EVENT_READ)
                started=time.monotonic()
                try:
                    while self.process.poll() is None:
                        if selector.select(.1):
                            if sys.stdin.readline().strip()=='stop':self.process.stdin.write(b'q\n');self.process.stdin.flush();break
                        if time.monotonic()-started>63:break
                    _,error=self.process.communicate(timeout=5)
                finally:selector.close()
                if self.process.returncode:raise ValueError(error.decode(errors='replace')[-700:] or 'Microphone capture failed')
            elif event.get('action')=='file':
                path=Path(str(event.get('path','')))
                if not path.is_absolute() or not path.is_file() or path.stat().st_size>1024**3:raise ValueError('Choose a local audio file smaller than 1 GiB')
                self.emit(dict(type='phase',value='processing'))
                self.command(['ffmpeg','-v','error','-nostdin','-threads','2','-i',str(path),'-t','300','-ar','16000','-ac','1','-c:a','pcm_s16le','-y',str(wav)],60)
            else:raise ValueError('Choose Record or an audio file')
            if not wav.exists() or wav.stat().st_size<2048:raise ValueError('No audio was captured')
            self.emit(dict(type='phase',value='processing'))
            self.command([binary,'-m',str(model),'-f',str(wav),'-l',language,'-t','2','-ng','-otxt','-of',str(output),'-np','-nt'],300)
            text=output.with_suffix('.txt').read_text().strip()
            self.emit(dict(type='transcript',text=text))

def main():
    emit=lambda event:print(json.dumps(event),flush=True)
    worker=Transcriber(emit);signal.signal(signal.SIGTERM,worker.cancel)
    try:
        os.nice(5);event=json.loads(sys.stdin.readline(16385));worker.run(event)
    except (ValueError,OSError,subprocess.SubprocessError) as error:emit(dict(type='error',text=str(error)));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
