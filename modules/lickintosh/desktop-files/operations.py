"""Serial desktop file operations with session undo/redo and recoverable trash."""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.parse
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'quicklook'))
from backend import local_path, transfer

class Operations:
 def __init__(self,data_home=None):
  self.trash=Path(data_home or os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))/'Trash'
  self.undo_stack=[];self.redo_stack=[];self.changes=[]
 def move(self,source,target):
  from gi.repository import Gio
  if target.exists() or target.is_symlink():raise FileExistsError(f'File already exists: {target}')
  Gio.File.new_for_path(str(source)).move(Gio.File.new_for_path(str(target)),Gio.FileCopyFlags.NOFOLLOW_SYMLINKS,None,None,None)
 def trash_file(self,path):
  path=local_path(path)
  if not path.exists() and not path.is_symlink():raise FileNotFoundError(path)
  if path in [Path('/'),Path.home()] or self.trash==path or self.trash.is_relative_to(path):raise ValueError('This location cannot be moved to Trash')
  files=self.trash/'files';info=self.trash/'info'
  for folder in [self.trash,files,info]:folder.mkdir(mode=0o700,parents=True,exist_ok=True)
  token=uuid.uuid4().hex
  meta=info/(token+'.trashinfo');stored=files/token
  with meta.open('x',encoding='utf-8') as f:
   f.write('[Trash Info]\nPath='+urllib.parse.quote(str(path),safe='/')+'\nDeletionDate='+datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')+'\n')
  try:shutil.move(str(path),str(stored))
  except BaseException:meta.unlink();raise
  return {'kind':'restore','source':str(stored),'target':str(path),'meta':str(meta)}
 def apply(self,step):
  if step['kind']=='trash':return self.trash_file(step['path'])
  source=Path(step['source']);target=Path(step['target'])
  self.move(source,target)
  self.changes.append({'old':str(source),'new':str(target)})
  if step['kind']=='restore':
   Path(step['meta']).unlink(missing_ok=True)
   return {'kind':'trash','path':str(target)}
  return {'kind':'move','source':str(target),'target':str(source)}
 def history(self,redo=False):
  stack=self.redo_stack if redo else self.undo_stack;other=self.undo_stack if redo else self.redo_stack
  if not stack:return []
  group=stack[-1];inverse=[];paths=[]
  try:
   while group:
    step=group[-1];inverse.append(self.apply(step));group.pop()
    if step['kind']!='trash':paths.append(step['target'])
  finally:
   if not group:stack.pop()
   if inverse:other.append(inverse)
  return paths
 def clipboard(self,paths,cut=False):
  urls=[local_path(p).as_uri() for p in paths]
  if urls:subprocess.run(['wl-copy','--type','x-special/gnome-copied-files'],input=('cut' if cut else 'copy')+'\n'+'\n'.join(urls),text=True,check=True,timeout=5)
 def read_clipboard(self):
  result=subprocess.run(['wl-paste','--no-newline','--type','x-special/gnome-copied-files'],capture_output=True,timeout=5)
  if result.returncode==0:
   lines=result.stdout.decode().splitlines();mode=lines.pop(0) if lines else 'copy'
   return [v for v in lines if v and not v.startswith('#')],'move' if mode=='cut' else 'copy',result.stdout
  result=subprocess.run(['wl-paste','--no-newline','--type','text/uri-list'],capture_output=True,check=True,timeout=5)
  return [v.strip() for v in result.stdout.decode().splitlines() if v.strip() and not v.startswith('#')],'copy',None
 def perform(self,request):
  self.changes=[]
  op=request['operation'];values=request.get('paths',[]);destination=request.get('destination','');steps=[];paths=[]
  if op in ['copy','cut']:self.clipboard(values,op=='cut');return []
  if op in ['undo','redo']:return self.history(op=='redo')
  if op in ['new-folder','new-file']:
   folder=local_path(destination);base='untitled folder' if op=='new-folder' else 'untitled file';target=folder/base;index=2
   while target.exists() or target.is_symlink():target=folder/(base+' '+str(index));index+=1
   if op=='new-folder':target.mkdir()
   else:target.open('x').close()
   self.undo_stack.append([{'kind':'trash','path':str(target)}]);self.redo_stack=[]
   return [str(target)]
  clipboard=None
  if op=='paste':values,mode,clipboard=self.read_clipboard();op='transfer'
  else:mode=request.get('mode','copy')
  if len(values)>1000:raise ValueError('Too many files selected')
  try:
   for value in values:
    if urllib.parse.urlsplit(str(value)).scheme=='trash' and op=='transfer':
     target=transfer([value],destination,mode)[0];paths.append(target);steps.append({'kind':'trash','path':target});continue
    source=local_path(value)
    if op in ['transfer','duplicate']:
     action='copy' if op=='duplicate' else mode
     dest=str(source.parent) if op=='duplicate' else destination
     target=Path(transfer([str(source)],dest,action)[0]);paths.append(str(target))
     if target!=source:steps.append({'kind':'move','source':str(target),'target':str(source)} if action=='move' else {'kind':'trash','path':str(target)})
    elif op=='trash':steps.append(self.trash_file(source))
    elif op=='rename':
     name=request.get('name','').strip()
     if not name or name in ['.','..'] or '/' in name or '\0' in name:raise ValueError('Invalid file name')
     target=source.with_name(name)
     if source!=target:self.move(source,target);steps.append({'kind':'move','source':str(target),'target':str(source)})
     self.changes.append({'old':str(source),'new':str(target)})
     paths.append(str(target))
    else:raise ValueError('Unsupported desktop operation')
  finally:
   if steps:self.undo_stack.append(steps);self.undo_stack=self.undo_stack[-100:];self.redo_stack=[]
  if clipboard is not None and mode=='move':
   current=subprocess.run(['wl-paste','--no-newline','--type','x-special/gnome-copied-files'],capture_output=True,timeout=5)
   if current.returncode==0 and current.stdout==clipboard:subprocess.run(['wl-copy','--clear'],check=True,timeout=5)
  return paths

def main():
 ops=Operations()
 for line in sys.stdin:
  request={}
  try:
   request=json.loads(line);paths=ops.perform(request)
   reply={'ok':True,'paths':paths,'operation':request['operation'],'token':request.get('token',0),'changes':ops.changes}
  except Exception as e:reply={'ok':False,'message':str(e),'token':request.get('token',0)}
  print(json.dumps(reply),flush=True)
if __name__=='__main__':main()
