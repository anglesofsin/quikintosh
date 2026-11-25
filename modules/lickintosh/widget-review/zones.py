"""Validated IANA clock locations; no shell evaluation of widget input."""
from datetime import datetime
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
import json,sys
import zoneinfo
from pathlib import Path
DATABASE="@TZ_DATABASE@"
if Path(DATABASE).is_dir():zoneinfo.reset_tzpath([DATABASE,*zoneinfo.TZPATH])

def clocks(entries,twelve=False):
 result={}
 for entry in entries[:8]:
  zone=str(entry.get('tz',''))
  try:
   now=datetime.now(ZoneInfo(zone));result[zone]={'time':now.strftime('%I:%M %p' if twelve else '%H:%M').lstrip('0') if twelve else now.strftime('%H:%M'),'day':now.strftime('%a'),'valid':True}
  except (ZoneInfoNotFoundError,ValueError):result[zone]={'time':'—','day':'Invalid time zone','valid':False}
 return result
if __name__=='__main__':
 try:print(json.dumps(clocks(json.loads(sys.argv[1]),len(sys.argv)>2 and sys.argv[2]=='true')))
 except (ValueError,IndexError,TypeError):print('{}')
