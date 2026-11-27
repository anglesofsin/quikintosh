"""Capability-aware MPRIS TrackList; only the selected media-player bus is used."""
import re,threading
from pathlib import Path
import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio,GLib
TRACKS='org.mpris.MediaPlayer2.TrackList';OBJECT='/org/mpris/MediaPlayer2'

def plain(value):
    if isinstance(value,GLib.Variant):return plain(value.unpack())
    if isinstance(value,dict):return {key:plain(item) for key,item in value.items()}
    if isinstance(value,(list,tuple)):return [plain(item) for item in value]
    return value

class MediaQueue:
    def queue_connection(self,bus):
        if not re.fullmatch(r'org\.mpris\.MediaPlayer2\.[A-Za-z0-9_.-]{1,180}',bus or ''):raise ValueError('Choose an MPRIS media player')
        return Gio.bus_get_sync(Gio.BusType.SESSION,None)
    def queue_call(self,bus,interface,method,parameters=None):
        return plain(self.queue_connection(bus).call_sync(bus,OBJECT,interface,method,parameters,None,Gio.DBusCallFlags.NO_AUTO_START,2500,None))
    def queue_property(self,bus,interface,name):return self.queue_call(bus,'org.freedesktop.DBus.Properties','Get',GLib.Variant('(ss)',(interface,name)))[0]
    def queue_fetch(self,bus):
        if not bus:return dict(type='queue',fetched=True,player='',supported=False,editable=False,items=[])
        bridge=getattr(self,'spotify_bridge',None)
        external=bridge.queue(bus) if bridge else None
        if external is not None:return external
        try:
            tracks=self.queue_property(bus,TRACKS,'Tracks')[:200]
            editable=bool(self.queue_property(bus,TRACKS,'CanEditTracks'))
            metadata=self.queue_call(bus,TRACKS,'GetTracksMetadata',GLib.Variant('(ao)',(tracks,)))[0] if tracks else []
            current=self.queue_property(bus,'org.mpris.MediaPlayer2.Player','Metadata').get('mpris:trackid','')
            rows=[]
            by_id={item.get("mpris:trackid"):item for item in metadata}
            for track_id in tracks:
                item=by_id.get(track_id,{})
                track=item.get('mpris:trackid','')
                if track not in tracks:continue
                artists=item.get('xesam:artist',[])
                try:length=max(0,int(item.get('mpris:length',0) or 0))/1000000
                except (TypeError,ValueError):length=0
                rows.append(dict(id=track,title=str(item.get('xesam:title','Untitled'))[:300],artist=', '.join(str(a) for a in artists[:3])[:300] if isinstance(artists,list) else str(artists)[:300],art=str(item.get('mpris:artUrl',''))[:2048],length=length))
            return dict(type='queue',fetched=True,player=bus,supported=True,editable=editable,current=current,items=rows)
        except GLib.Error:return dict(type='queue',fetched=True,player=bus,supported=False,editable=False,items=[])
    def queue_watch(self,event):
        bus=event.get('player','');connection=Gio.bus_get_sync(Gio.BusType.SESSION,None)
        # Subscriptions do not own the shared bus connection; retain it explicitly.
        self.queue_bus_connection=connection
        selected=bus if event.get('enabled') else ''
        if selected and selected==getattr(self,'queue_watch_bus','') and getattr(self,'queue_subscriptions',[]):return self.queue_fetch(selected)
        self.queue_watch_bus=selected
        if self.queue_watch_bus:self.queue_connection(bus)
        if not getattr(self,'queue_context',None):
            self.queue_context=GLib.MainContext.new();self.queue_loop=GLib.MainLoop.new(self.queue_context,False)
            threading.Thread(target=self.queue_loop.run,daemon=True,name='mpris-queue-events').start()
        installed=threading.Event();errors=[]
        def install(*_):
            self.queue_context.push_thread_default()
            try:
                for subscription in getattr(self,'queue_subscriptions',[]):connection.signal_unsubscribe(subscription)
                self.queue_subscriptions=[]
                if self.queue_watch_bus:
                    def changed(*_):
                        if getattr(self,'queue_pending_bus','')==bus:return
                        self.queue_pending_bus=bus
                        def update():
                            try:
                                if self.queue_watch_bus==bus and hasattr(self,'emit_event'):self.emit_event(self.queue_fetch(bus))
                            finally:
                                if self.queue_pending_bus==bus:self.queue_pending_bus=''
                        timer=threading.Timer(.08,update);timer.daemon=True;timer.start()
                    owner=connection.call_sync('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetNameOwner',GLib.Variant('(s)',(bus,)),GLib.VariantType('(s)'),Gio.DBusCallFlags.NONE,2000,None).unpack()[0]
                    self.queue_subscriptions=[connection.signal_subscribe(owner,TRACKS,member,OBJECT,None,Gio.DBusSignalFlags.NONE,changed) for member in ('TrackListReplaced','TrackAdded','TrackRemoved','TrackMetadataChanged')]
                    self.queue_subscriptions.append(connection.signal_subscribe(owner,'org.freedesktop.DBus.Properties','PropertiesChanged',OBJECT,'org.mpris.MediaPlayer2.Player',Gio.DBusSignalFlags.NONE,changed))
            except Exception as error:errors.append(error)
            finally:self.queue_context.pop_thread_default();installed.set()
            return False
        self.queue_context.invoke_full(GLib.PRIORITY_DEFAULT,install)
        if not installed.wait(3):raise ValueError('Queue event listener did not start')
        if errors:raise errors[0]
        return self.queue_fetch(bus) if event.get('enabled') else dict(type='queueUnwatched')
    def queue_action(self,event):
        bus=event.get('player','');data=self.queue_fetch(bus)
        if not data['supported']:raise ValueError('This player does not expose a queue')
        operation=event.get('operation');track=event.get('id','')
        if operation in ('jump','remove'):
            if track not in [item['id'] for item in data['items']]:raise ValueError('Choose a track currently in this queue')
            if operation=='remove' and not data['editable']:raise ValueError('This player has a read-only queue')
            if data.get('provider')=='spicetify':
                row=next(item for item in data['items'] if item['id']==track)
                self.queue_call(bus,'org.mpris.MediaPlayer2.Player','OpenUri',GLib.Variant('(s)',(row['uri'],)))
            else:self.queue_call(bus,TRACKS,'GoTo' if operation=='jump' else 'RemoveTrack',GLib.Variant('(o)',(track,)))
        elif operation=='add':
            if not data['editable']:raise ValueError('This player has a read-only queue')
            path=self.path(str(event.get('path','')))
            if not path.is_file() or path.suffix.lower() not in ('.mp3','.wav','.flac','.ogg','.opus','.m4a','.aac','.mp4','.mkv'):raise ValueError('Choose a local audio or video file')
            after=data['items'][-1]['id'] if data['items'] else '/org/mpris/MediaPlayer2/TrackList/NoTrack'
            self.queue_call(bus,TRACKS,'AddTrack',GLib.Variant('(sob)',(path.as_uri(),after,False)))
        else:raise ValueError('Unknown queue action')
        return self.queue_fetch(bus)
