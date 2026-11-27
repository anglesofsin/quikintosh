"""Explicitly selected Markdown vault; no discovery of private user folders."""
import json,os,tempfile
from pathlib import Path

class VaultOperations:
    def vault(self,event):
        config=self.root/'vault.json'
        try:settings=json.loads(config.read_text())
        except (OSError,ValueError):settings={}
        action=event.get('action')
        if action=='vaultSelect':
            path=self.path(str(event.get('path',''))).resolve(strict=True)
            if not path.is_dir():raise ValueError('Choose a vault folder')
            settings={'path':str(path)}
            config.write_text(json.dumps(settings))
        folder=Path(settings['path']) if settings.get('path') else None
        if folder is None:return dict(type='vault',path='',notes=[],text='',name='')
        if not folder.is_dir():raise ValueError('The selected vault is unavailable')
        if action in ('vaultRead','vaultSave'):
            name=str(event.get('name',''))
            if not name or Path(name).is_absolute() or '..' in Path(name).parts or not name.endswith('.md'):raise ValueError('Choose a Markdown note inside the vault')
            path=folder/name
            if path.is_symlink() or not path.resolve().is_relative_to(folder.resolve()):raise ValueError('Note must stay inside the selected vault')
            if action=='vaultSave':
                text=str(event.get('text',''))
                if len(text)>512*1024:raise ValueError('Note is limited to 512 KiB')
                if not path.parent.is_dir():raise ValueError('Note folder is unavailable')
                # Detect external edits so the UI cannot silently overwrite Obsidian.
                expected=event.get('modified')
                if path.exists() and expected is not None and str(path.stat().st_mtime_ns)!=str(expected):raise ValueError('This note changed in another app. Reopen it before saving.')
                fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.quickintosh-note-')
                try:
                    with os.fdopen(fd,'w') as stream:stream.write(text)
                    Path(tmp).replace(path)
                finally:Path(tmp).unlink(missing_ok=True)
            if path.stat().st_size>512*1024:raise ValueError('Open this large note in Obsidian')
            return dict(type='vaultNote',name=name,text=path.read_text(),modified=str(path.stat().st_mtime_ns))
        notes=[];visited=0
        # Do not follow symlinks or enter hidden metadata/plugin folders.
        for parent,dirs,files in os.walk(folder,followlinks=False):
            dirs[:]=[d for d in dirs if not d.startswith('.') and not (Path(parent)/d).is_symlink()]
            for name in files:
                visited+=1
                if visited>10000:break
                path=Path(parent)/name
                if name.endswith('.md') and not path.is_symlink():notes.append(dict(name=str(path.relative_to(folder)),modified=str(path.stat().st_mtime_ns)))
            if visited>10000:break
        notes.sort(key=lambda n:n['modified'],reverse=True)
        return dict(type='vault',path=str(folder),notes=notes[:1000])
