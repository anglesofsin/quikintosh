"""Read-only Discord client identity; never inspect client data or credentials."""
from pathlib import Path
import re

PATTERNS=[('discord-canary',r'discord[-_. ]?canary'),('discord-ptb',r'discord[-_. ]?ptb'),('equibop',r'equibop'),('discord',r'discord(?:[-_. ]stable)?')]
NAMES={'discord':'Discord','discord-canary':'Discord Canary','discord-ptb':'Discord PTB','equibop':'Equibop'}

def discord_key(value):
    value=str(value or '').casefold()
    for key,pattern in PATTERNS:
        if re.search(r'(?:^|[/_. -])'+pattern+r'(?:$|[/_. -])',value):return key
    return ''

class ProcessIdentities:
    def __init__(self,proc=Path('/proc')):
        self.proc=Path(proc);self.cache={}

    def resolve(self,pid):
        try:
            pid=int(pid)
            if pid<=0:return ''
            path=self.proc/str(pid)
            stat=(path/'stat').read_text();fields=stat[stat.rfind(')')+2:].split();started=fields[19]
            executable=str((path/'exe').resolve(strict=True))
            token=(pid,started,executable)
            if token in self.cache:return self.cache[token]
            # argv[0] can be Electron's process title (including flags). Only
            # the executable portion is used; no environment or client files.
            first=(path/'cmdline').read_bytes().split(b'\0',1)[0].decode(errors='replace').split(' --',1)[0]
            key=discord_key(Path(executable).name) or discord_key(first)
            if not key:
                flatpak=path/'root/.flatpak-info'
                try:
                    import configparser
                    info=configparser.ConfigParser(interpolation=None);info.read(flatpak)
                    key=discord_key(info.get('Application','name',fallback=''))
                except (OSError,configparser.Error):pass
            self.cache[token]=key
            if len(self.cache)>256:self.cache={token:key}
            return key
        except (OSError,ValueError,IndexError):return ''

    def identify(self,clients,catalog):
        catalog.refresh();result={}
        for client in clients if isinstance(clients,list) else []:
            if not isinstance(client,dict):continue
            key=self.resolve(client.get('pid'))
            if not key:continue
            app=catalog.aliases.get(key,{})
            result[str(client['pid'])]={'key':key,'name':NAMES[key],'icon':app.get('icon',''),'desktopId':app.get('desktopId','')}
        return result
