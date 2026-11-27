"""Read-only battery inventory from UPower and paired KDE Connect devices."""
import json,math,time,os,tempfile
from pathlib import Path
from gi.repository import Gio,GLib

def call(bus,service,path,interface,method,args=None):
 return bus.call_sync(service,path,interface,method,args,None,Gio.DBusCallFlags.NO_AUTO_START,900,None).unpack()
def properties(bus,service,path,interface):
 return call(bus,service,path,'org.freedesktop.DBus.Properties','GetAll',GLib.Variant('(s)',(interface,)))[0]
def row(identifier,name,percent,charging,kind,source):
 try:value=float(percent)
 except (TypeError,ValueError):return None
 if not math.isfinite(value) or not 0<=value<=100:return None
 return dict(id=identifier,name=str(name or 'Device')[:120],percent=round(value),charging=bool(charging),kind=kind,source=source)
def inventory():
 rows=[];sources=[]
 try:
  bus=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)
  paths=call(bus,'org.freedesktop.UPower','/org/freedesktop/UPower','org.freedesktop.UPower','EnumerateDevices')[0]
  for path in paths[:24]:
   try:
    p=properties(bus,'org.freedesktop.UPower',path,'org.freedesktop.UPower.Device')
    if not p.get('IsPresent',True) or p.get('Type') in (0,1) or p.get('PowerSupply') and p.get('Type')!=2:continue
    kind={2:'laptop',3:'ups',5:'mouse',6:'keyboard',8:'phone',17:'headphones',28:'headphones'}.get(p.get('Type'),'battery')
    item=row('upower:'+path,p.get('Model') or p.get('NativePath'),p.get('Percentage'),p.get('State') in (1,5),kind,'UPower')
    if item:rows.append(item)
   except GLib.Error:continue
  sources.append('UPower')
 except GLib.Error:pass
 try:
  bus=Gio.bus_get_sync(Gio.BusType.SESSION,None)
  devices=call(bus,'org.kde.kdeconnect','/modules/kdeconnect','org.kde.kdeconnect.daemon','devices',GLib.Variant('(bb)',(True,True)))[0]
  for device in devices[:16]:
   path='/modules/kdeconnect/devices/'+device
   try:
    p=properties(bus,'org.kde.kdeconnect',path,'org.kde.kdeconnect.device');battery=properties(bus,'org.kde.kdeconnect',path+'/battery','org.kde.kdeconnect.device.battery')
    item=row('kdeconnect:'+device,p.get('name'),battery.get('charge'),battery.get('isCharging'),'phone','KDE Connect')
    if item:rows.append(item)
   except GLib.Error:continue
  sources.append('KDE Connect')
 except GLib.Error:pass
 return dict(devices=rows,sources=sources)
def merge(previous,current,now):
 result=[];known=set()
 for item in current:
  result.append(dict(item,connected=True,lastSeen=now));known.add(item['id'])
 for item in previous:
  if item.get('id') not in known and 0<=now-float(item.get('lastSeen',0))<86400:
   result.append(dict(item,connected=False,charging=False))
 return result[:40]

def snapshot():
 result=inventory();directory=Path.home()/'.local/state/quickintosh/island-shelf';directory.mkdir(parents=True,exist_ok=True,mode=0o700);file=directory/'battery-cache.json'
 try:previous=json.loads(file.read_text())
 except (ValueError,OSError):previous=[]
 if not isinstance(previous,list):previous=[]
 result['devices']=merge(previous,result['devices'],time.time())
 fd,tmp=tempfile.mkstemp(dir=directory,prefix='.battery-')
 try:
  with os.fdopen(fd,'w') as stream:json.dump(result['devices'],stream)
  Path(tmp).replace(file)
 finally:Path(tmp).unlink(missing_ok=True)
 return result
if __name__=='__main__':print(json.dumps(snapshot()))
