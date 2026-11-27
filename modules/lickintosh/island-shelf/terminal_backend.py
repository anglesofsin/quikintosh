"""Explicit command runner, bounded output/runtime and cancellation of owned jobs."""
import json,os,selectors,signal,subprocess,sys,time

def run(event,emit):
    command=event.get('command','')
    if not isinstance(command,str) or not command.strip() or len(command)>16384:raise ValueError('Enter a command of at most 16 KiB')
    process=subprocess.Popen(['bash','--noprofile','--norc','-c',command],cwd=os.path.expanduser('~'),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
    def stop(*_):
        if process.poll() is None:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
    previous=signal.signal(signal.SIGTERM,lambda *_:(stop(),sys.exit(143)))
    selector=selectors.DefaultSelector();selector.register(process.stdout,selectors.EVENT_READ)
    started=time.monotonic();size=0
    try:
        while selector.get_map():
            if time.monotonic()-started>60:stop();emit(dict(type='output',text='\nCommand stopped after 60 seconds. Open Terminal for longer jobs.\n'));break
            for key,_ in selector.select(.1):
                chunk=os.read(key.fileobj.fileno(),8192)
                if not chunk:selector.unregister(key.fileobj);continue
                size+=len(chunk)
                if size>256*1024:stop();emit(dict(type='output',text='\nOutput limit reached.\n'));break
                emit(dict(type='output',text=chunk.decode(errors='replace')))
        code=process.wait(timeout=3)
        emit(dict(type='exit',code=code))
        return code
    finally:stop();selector.close();process.stdout.close();signal.signal(signal.SIGTERM,previous)

if __name__=='__main__':
    try:
        line=sys.stdin.readline(32769)
        if len(line)>32768:raise ValueError('Command request is too large')
        run(json.loads(line),lambda event:print(json.dumps(event),flush=True))
    except (ValueError,OSError,subprocess.SubprocessError) as error:print(json.dumps(dict(type='error',text=str(error))),flush=True);sys.exit(1)
