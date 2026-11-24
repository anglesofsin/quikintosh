"""Rice-scoped file opener. Never switches shells or recursively invokes itself."""
import base64,json,mimetypes,subprocess,sys,urllib.parse,os
from pathlib import Path
from mime_types import compatible_mime,external_app

def path_for(value):
 u=urllib.parse.urlsplit(value)
 if u.scheme:
  if u.scheme!='file' or u.netloc not in ('','localhost'):raise ValueError('Quick Look opens local files only')
  return Path(urllib.parse.unquote(u.path))
 return Path(value).expanduser().absolute()
def launch_external(paths):
 from gi.repository import Gio
 groups={}
 for path in paths:
  mime=Gio.content_type_guess(str(path),None)[0];app=external_app(mime)
  if not app:raise ValueError('No external application for '+path.name)
  key=app.get_id() or app.get_executable()
  groups.setdefault(key,(app,[]))[1].append(Gio.File.new_for_path(str(path)))
 for app,files in groups.values():app.launch(files,None)
def main(argv):
 external=bool(argv and argv[0]=='--external')
 if external:argv=argv[1:]
 paths=[path_for(v) for v in argv]
 if not paths:return 0
 if external:launch_external(paths);return 0
 from gi.repository import Gio
 preview=[];other=[]
 for path in paths:
  mime=Gio.content_type_guess(str(path),None)[0]
  (preview if path.is_file() and compatible_mime(mime) else other).append(path)
 if preview:
  result=subprocess.run([os.environ.get('LICKINTOSH_CLI','lickintosh'),'ipc','call','quicklook','openFiles',base64.b64encode(json.dumps([str(p) for p in preview]).encode()).decode()],capture_output=True,text=True,timeout=15)
  if result.returncode or result.stdout.strip()!='opened':launch_external(preview)
 if other:launch_external(other)
 return 0
if __name__=='__main__':
 try:sys.exit(main(sys.argv[1:]))
 except Exception as error:
  subprocess.run(['notify-send','-a','Quick Look','Unable to open file',str(error)],check=False);sys.exit(1)
