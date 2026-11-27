"""Fetch daily reference rates off the UI thread; retain dated offline data."""
import json,os,time,urllib.request
from pathlib import Path
p=Path(os.environ.get('XDG_CACHE_HOME',str(Path.home()/'.cache')))/'quickintosh/calculator-rates.json'
data={}
try:data=json.loads(p.read_text())
except (OSError,ValueError):pass
try:
 if not data or time.time()-p.stat().st_mtime>21600:
  request=urllib.request.Request('https://api.frankfurter.dev/v1/latest',headers={'User-Agent':'Quickintosh-Calculator/1.0'})
  with urllib.request.urlopen(request,timeout=8) as response:fresh=json.load(response)
  if not isinstance(fresh.get('rates'),dict) or not fresh.get('date'):raise ValueError('Invalid rates response')
  data=fresh;data['rates']['EUR']=1
  p.parent.mkdir(parents=True,exist_ok=True)
  tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(data));tmp.replace(p)
except Exception:
 data['error']='Offline · '+data.get('date','Rates unavailable')
print(json.dumps(data))
