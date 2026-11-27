"""Exercise the real freedesktop notification inline reply on a private bus."""
import os,sys,json,subprocess,tempfile,time,signal
from pathlib import Path
from gi.repository import Gio,GLib
# Called by the private compositor harness; never connect to the host bus.
assert os.environ.get('QUICKINTOSH_TEST_PRIVATE_RUNTIME','').startswith('/tmp/')
source=Path(os.environ['QUICKINTOSH_TEST_SOURCE']);qs=os.environ['QUICKINTOSH_TEST_QS']
with tempfile.TemporaryDirectory(prefix='qi-notification-') as tmp:
 root=Path(tmp)
 for entry in source.iterdir():
  if entry.name!='shell.qml':(root/entry.name).symlink_to(entry,target_is_directory=entry.is_dir())
 (root/'shell.qml').write_text('''import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.Notifications
ShellRoot{
 property var received:null
 NotificationServer{id:server;inlineReplySupported:true;actionsSupported:true;bodySupported:true;onNotification:n=>{n.tracked=true;received=n}}
 IpcHandler{target:'notifyQA';function reply():string{if(!received)return 'missing';if(!received.hasInlineReply)return 'unsupported';received.sendInlineReply('Native reply test');return 'sent'}}
}''')
 bus=subprocess.Popen(['dbus-daemon','--session','--nofork','--print-address=1','--address=unix:path='+tmp+'/bus'],stdout=subprocess.PIPE,text=True)
 address=bus.stdout.readline().strip();assert address.startswith('unix:path='+tmp)
 env=dict(os.environ,DBUS_SESSION_BUS_ADDRESS=address,HOME=tmp,XDG_RUNTIME_DIR=os.environ['QUICKINTOSH_TEST_PRIVATE_RUNTIME'],WAYLAND_DISPLAY=os.environ['QUICKINTOSH_TEST_PRIVATE_WAYLAND'],HYPRLAND_INSTANCE_SIGNATURE=os.environ['QUICKINTOSH_TEST_PRIVATE_HYPRLAND']);env.pop('DISPLAY',None)
 with (root/'log').open('w') as log:process=subprocess.Popen([qs,'-p',tmp],env=env,stdout=log,stderr=log,start_new_session=True)
 try:
  connection=Gio.DBusConnection.new_for_address_sync(address,Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT|Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION,None,None)
  def call(method,parameters,signature):return connection.call_sync('org.freedesktop.Notifications','/org/freedesktop/Notifications','org.freedesktop.Notifications',method,parameters,GLib.VariantType.new(signature),Gio.DBusCallFlags.NONE,2000,None)
  for _ in range(100):
   try:capabilities=call('GetCapabilities',None,'(as)').unpack()[0];break
   except GLib.Error:time.sleep(.1)
  else:raise AssertionError((root/'log').read_text())
  assert 'inline-reply' in capabilities,capabilities
  replies=[]
  connection.signal_subscribe(None,'org.freedesktop.Notifications','NotificationReplied','/org/freedesktop/Notifications',None,Gio.DBusSignalFlags.NONE,lambda c,s,p,i,n,params:replies.append(params.unpack()))
  result=call('Notify',GLib.Variant('(susssasa{sv}i)',('Native Test',0,'','Alex','Reply through the island',['inline-reply','Reply'],{'x-kde-reply-placeholder-text':GLib.Variant('s','Reply')},10000)),'(u)');notification_id=result.unpack()[0]
  for _ in range(100):
   p=subprocess.run([qs,'-p',tmp,'ipc','call','notifyQA','reply'],env=env,capture_output=True,text=True,timeout=3)
   if p.stdout.strip()=='sent':break
   time.sleep(.1)
  else:raise AssertionError(p.stdout+(root/'log').read_text())
  end=time.monotonic()+3
  while not replies and time.monotonic()<end:
   while GLib.MainContext.default().pending():GLib.MainContext.default().iteration(False)
   time.sleep(.01)
  assert replies==[(notification_id,'Native reply test')],replies
  print('REAL_FREEDESKTOP_INLINE_REPLY_SIGNAL_OK')
 finally:
  if process.poll() is None:os.killpg(process.pid,signal.SIGTERM);process.wait(timeout=5)
  bus.terminate();bus.wait(timeout=5)
