"""Install owned Nautilus actions, preserving unrelated or user-edited scripts."""
import os,shlex,sys
from pathlib import Path

def install(python,bridge,home=None):
    folder=Path(home or Path.home())/'.local/share/nautilus/scripts'
    folder.mkdir(parents=True,exist_ok=True)
    for name,arguments in [('Send to Dynamic Island',[]),('Send to Floating File Tray',['--floating'])]:
        path=folder/name
        marker='# Quickintosh managed file tray service'
        if path.exists() and marker not in path.read_text(errors='replace'):continue
        text='#!/bin/sh\n'+marker+'\nexec '+shlex.join([python,bridge,*arguments])+' "$@"\n'
        if not path.exists() or path.read_text()!=text:path.write_text(text);path.chmod(0o755)

if __name__=='__main__':install(*sys.argv[1:3])
