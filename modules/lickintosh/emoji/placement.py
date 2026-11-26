"""Warm placement worker. Reads accessibility geometry, never field contents."""
import json,os,select,subprocess,sys,time
from gi.repository import Gio,GLib
connection=None
app_cache={}
def call(bus,path,interface,method,parameters=None,timeout=25):
 return connection.call_sync(bus,path,interface,method,parameters,None,Gio.DBusCallFlags.NONE,timeout,None).unpack()
def caret(pid):
 global connection
 started=time.monotonic()
 try:
  if connection is None:
   session=Gio.bus_get_sync(Gio.BusType.SESSION,None)
   address=session.call_sync('org.a11y.Bus','/org/a11y/bus','org.a11y.Bus','GetAddress',None,None,Gio.DBusCallFlags.NONE,30,None).unpack()[0]
   connection=Gio.DBusConnection.new_for_address_sync(address,Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT|Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION,None,None)
  apps=call('org.a11y.atspi.Registry','/org/a11y/atspi/accessible/root','org.a11y.atspi.Accessible','GetChildren')[0]
  for bus,path in apps:
   if time.monotonic()-started>.065:return None
   owner=app_cache.get(bus)
   if owner is None:
    owner=call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetConnectionUnixProcessID',GLib.Variant('(s)',(bus,)))[0];app_cache[bus]=owner
   if owner!=pid:continue
   queue=[path];visited=0
   while queue and visited<80 and time.monotonic()-started<.065:
    path=queue.pop(0);visited+=1
    states=call(bus,path,'org.a11y.atspi.Accessible','GetState')[0]
    if states and states[0] & (1<<12):
     offset=call(bus,path,'org.freedesktop.DBus.Properties','Get',GLib.Variant('(ss)',('org.a11y.atspi.Text','CaretOffset')))[0]
     if hasattr(offset,'unpack'):offset=offset.unpack()
     rect=call(bus,path,'org.a11y.atspi.Text','GetCharacterExtents',GLib.Variant('(iu)',(int(offset),0)))[0]
     if len(rect)==4 and rect[0]>=0 and rect[1]>=0 and rect[3]>0:return {'x':rect[0],'y':rect[1]+rect[3],'height':rect[3]}
    children=call(bus,path,'org.a11y.atspi.Accessible','GetChildren')[0]
    queue.extend(p for b,p in children if b==bus and p!='/org/a11y/atspi/null')
 except (GLib.Error,ValueError,TypeError,IndexError):pass
 return None
def placement():
 result=subprocess.run(['hyprctl','-j','--batch','activewindow;cursorpos;monitors'],capture_output=True,text=True,timeout=.4)
 import re
 data=json.loads('['+re.sub(r'}\s*(?=[{\[])','},',result.stdout.strip())+']')
 active,mouse,monitors=data
 monitor=next((m for m in monitors if m['id']==active.get('monitor')),next((m for m in monitors if m.get('focused')),{}))
 anchor=caret(active.get('pid',-1))
 # Apps that do not expose a caret get an honest fallback at the pointer.
 point=anchor or mouse
 scale=float(os.environ.get('QT_SCALE_FACTOR','1'))
 return {'target':active.get('address',''),'screen':monitor.get('name',''),'x':(point['x']-monitor.get('x',0))/scale,'y':(point['y']-monitor.get('y',0))/scale,'caret':bool(anchor)}
def main():
 print(json.dumps({'type':'ready'}),flush=True)
 for line in sys.stdin:
  request={}
  try:
   request=json.loads(line)
   result=placement();result.update(type='placement',serial=request['serial'])
  except Exception:result={'type':'placement','serial':request.get('serial',0),'target':'','screen':'','x':200,'y':100,'caret':False}
  print(json.dumps(result),flush=True)
if __name__=='__main__':main()
