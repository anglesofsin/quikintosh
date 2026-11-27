"""A real MPRIS test service on an explicitly private bus, never the host bus."""
import os,json,sys,time
from pathlib import Path
import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio,GLib
address=os.environ.get('DBUS_SESSION_BUS_ADDRESS','')
assert address.startswith('unix:path=/tmp/qi-review-'),address
ROOT='org.mpris.MediaPlayer2';PLAYER=ROOT+'.Player';OBJECT='/org/mpris/MediaPlayer2'
status='Playing';position=65_000_000
metadata={'mpris:trackid':GLib.Variant('o','/org/mpris/MediaPlayer2/track/test'),'mpris:length':GLib.Variant('x',203_000_000),'mpris:artUrl':GLib.Variant('s',os.environ.get('QA_MEDIA_ART','')),'xesam:title':GLib.Variant('s','Levitating'),'xesam:artist':GLib.Variant('as',['Dua Lipa']),'xesam:album':GLib.Variant('s','Visual review fixture')}
props={ROOT:{'CanQuit':('b',False),'Fullscreen':('b',False),'CanSetFullscreen':('b',False),'CanRaise':('b',True),'HasTrackList':('b',False),'Identity':('s','Quickintosh visual test'),'DesktopEntry':('s','quickintosh-qa'),'SupportedUriSchemes':('as',['file']),'SupportedMimeTypes':('as',['audio/flac'])},PLAYER:{'PlaybackStatus':('s',status),'LoopStatus':('s','None'),'Rate':('d',1.),'Shuffle':('b',False),'Metadata':('a{sv}',metadata),'Volume':('d',.6),'Position':('x',position),'MinimumRate':('d',1.),'MaximumRate':('d',1.),'CanGoNext':('b',True),'CanGoPrevious':('b',True),'CanPlay':('b',True),'CanPause':('b',True),'CanSeek':('b',True),'CanControl':('b',True)}}
methods={ROOT:'<method name="Raise"/><method name="Quit"/>',PLAYER:''.join('<method name="'+n+'"/>' for n in ['Next','Previous','PlayPause','Stop','Play','Pause'])+'<method name="Seek"><arg type="x" direction="in"/></method><method name="SetPosition"><arg type="o" direction="in"/><arg type="x" direction="in"/></method><method name="OpenUri"><arg type="s" direction="in"/></method><signal name="Seeked"><arg type="x"/></signal>'}
xml='<node>'+''.join('<interface name="'+iface+'">'+methods[iface]+''.join('<property name="'+name+'" type="'+value[0]+'" access="'+('readwrite' if name in ['Volume','LoopStatus','Shuffle','Rate','Fullscreen'] else 'read')+'"/>' for name,value in fields.items())+'</interface>' for iface,fields in props.items())+'</node>'
connection=Gio.DBusConnection.new_for_address_sync(address,Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT|Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION,None,None)
connection.call_sync('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','RequestName',GLib.Variant('(su)',('org.mpris.MediaPlayer2.quickintoshQA',0)),GLib.VariantType('(u)'),Gio.DBusCallFlags.NONE,2000,None)
def changed(fields):connection.emit_signal(None,OBJECT,'org.freedesktop.DBus.Properties','PropertiesChanged',GLib.Variant('(sa{sv}as)',(PLAYER,{n:GLib.Variant(*props[PLAYER][n]) for n in fields},[])))
def get_property(conn,sender,path,iface,name):return GLib.Variant(*props[iface][name])
def set_property(conn,sender,path,iface,name,value):props[iface][name]=(value.get_type_string(),value.unpack());changed([name]);return True
def method(conn,sender,path,iface,name,params,invocation):
 with Path(sys.argv[1]).open('a') as f:f.write(json.dumps({'method':name,'params':params.unpack()})+'\n')
 if name in ['PlayPause','Pause','Play','Stop']:
  state=props[PLAYER]['PlaybackStatus'][1];props[PLAYER]['PlaybackStatus']=('s','Paused' if name=='Pause' or (name=='PlayPause' and state=='Playing') else 'Stopped' if name=='Stop' else 'Playing');changed(['PlaybackStatus'])
 elif name in ['SetPosition','Seek']:
  props[PLAYER]['Position']=('x',params.unpack()[-1] if name=='SetPosition' else props[PLAYER]['Position'][1]+params.unpack()[0]);connection.emit_signal(None,OBJECT,PLAYER,'Seeked',GLib.Variant('(x)',(props[PLAYER]['Position'][1],)))
 invocation.return_value(GLib.Variant('()',()))
for info in Gio.DBusNodeInfo.new_for_xml(xml).interfaces:connection.register_object(OBJECT,info,method,get_property,set_property)
print('MPRIS_QA_READY',flush=True)
GLib.MainLoop().run()
