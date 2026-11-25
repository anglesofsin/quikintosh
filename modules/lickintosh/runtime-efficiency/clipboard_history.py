"""List the existing local clipboard store without rehashing unchanged images."""
import hashlib,json,os,sys,tempfile
from pathlib import Path

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as file:
  for chunk in iter(lambda:file.read(256*1024),b''):h.update(chunk)
 return h.hexdigest()

def history(directory,limit,cache):
 directory=Path(os.path.expandvars(str(directory))).expanduser();limit=max(0,min(1000,int(limit)))
 try:old=json.loads(cache.read_text())
 except (OSError,ValueError):old={}
 candidates=[]
 try:
  for path in directory.iterdir():
   if path.suffix not in ('.png','.txt'):continue
   try:
    info=path.stat()
    if path.is_file():candidates.append((info.st_mtime_ns,path,info.st_size))
   except OSError:pass
 except OSError:return []
 selected=sorted(candidates,key=lambda entry:entry[0],reverse=True)[:limit];seen=set();rows=[];new={}
 for modified,path,size in selected:
  key=str(path);fingerprint=[modified,size];entry=old.get(key)
  try:
   if not entry or entry.get('version')!=fingerprint:entry={'version':fingerprint,'digest':digest(path)}
   info=path.stat()
   if [info.st_mtime_ns,info.st_size]!=fingerprint:continue
   new[key]=entry
   if entry['digest'] in seen:continue
   seen.add(entry['digest']);preview=''
   if path.suffix=='.txt':
    with path.open(encoding='utf-8',errors='replace') as file:preview=file.read(4096).replace('\n',' ').replace('\r',' ').replace('\t',' ')[:80]
   if '\n' not in key and '\t' not in key:rows.append(('image' if path.suffix=='.png' else 'text',key,preview))
  except OSError:continue
 if new!=old:
  cache.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
  fd,temporary=tempfile.mkstemp(prefix='.clipboard-index-',dir=cache.parent)
  try:
   with os.fdopen(fd,'w') as file:json.dump(new,file,separators=(',',':'))
   Path(temporary).replace(cache)
  finally:Path(temporary).unlink(missing_ok=True)
 return rows
if __name__=='__main__':
 cache=Path(os.environ.get('XDG_CACHE_HOME',str(Path.home()/'.cache')))/'quickintosh/performance/clipboard-index.json'
 for row in history(sys.argv[1],sys.argv[2],cache):print('\t'.join(row))
