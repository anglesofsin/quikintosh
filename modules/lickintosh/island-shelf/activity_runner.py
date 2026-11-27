"""Run an explicitly supplied job and publish bounded Live Activity progress."""
import argparse,json,os,signal,subprocess,sys,time,uuid
from pathlib import Path

def report(event):
    try:subprocess.run(['quickintosh','ipc','call','shelf','activity',json.dumps(event)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3)
    except (OSError,subprocess.SubprocessError):pass

def save_summary(title,seconds,code):
    folder=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'quickintosh/island-shelf'
    folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    path=folder/'job-history.jsonl'
    # No command text, arguments, output, file content or environment is stored.
    row=dict(title=title[:100],seconds=round(seconds,3),code=code,finished=int(time.time()))
    try:
        rows=path.read_text().splitlines()[-199:] if path.exists() and path.stat().st_size<1024*1024 else []
        import tempfile
        fd,tmp=tempfile.mkstemp(dir=folder,prefix='.job-history-')
        try:
            with os.fdopen(fd,'w') as stream:stream.write('\n'.join(rows+[json.dumps(row)])+'\n')
            Path(tmp).replace(path)
        finally:Path(tmp).unlink(missing_ok=True)
    except OSError:pass

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--title',default='Running task');parser.add_argument('--notify',action='store_true');parser.add_argument('command',nargs=argparse.REMAINDER)
    options=parser.parse_args();command=options.command
    if command and command[0]=='--':command=command[1:]
    if not command:parser.error('Supply a command after --')
    title=options.title[:100];identifier='job-'+uuid.uuid4().hex;started=time.monotonic()
    process=subprocess.Popen(command) # Retain caller TTY and environment for interactive tools.
    previous={}
    def forward(number,_):
        if process.poll() is None:process.send_signal(number)
    for number in (signal.SIGTERM,signal.SIGINT):previous[number]=signal.signal(number,forward)
    try:
        while process.poll() is None:
            elapsed=int(time.monotonic()-started)
            report(dict(id=identifier,title=title,subtitle=f'{elapsed//60}:{elapsed%60:02d} elapsed',ttl=12))
            try:process.wait(timeout=3)
            except subprocess.TimeoutExpired:pass
        code=process.returncode;seconds=time.monotonic()-started
        report(dict(id=identifier,title=title,subtitle='Completed' if code==0 else f'Exited with code {code}',progress=1 if code==0 else None,ttl=8))
        save_summary(title,seconds,code)
        if options.notify:
            subprocess.run(['notify-send','--app-name=Quickintosh',title,'Completed' if code==0 else f'Exited with code {code}'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3)
        return code if code>=0 else 128-code
    finally:
        for number,handler in previous.items():signal.signal(number,handler)

if __name__=='__main__':raise SystemExit(main())
