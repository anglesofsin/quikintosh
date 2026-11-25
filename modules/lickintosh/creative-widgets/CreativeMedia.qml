pragma Singleton
import QtQuick
import Quickshell
import qs.services
import qs.rosa.services as Rosa
Singleton{
 readonly property bool locked:Rosa.IslandBus.locked
 readonly property bool desktopActive:DesktopFiles.desktopFocused && !locked && WidgetState.galleryZone==='' && WidgetState.editingId===''
 readonly property bool canPlayAudio:AudioActivity.mayPlay
 property var lyrics:({})
 function lrc(path,lines){const next=Object.assign({},lyrics);next[path]=lines;const keys=Object.keys(next);if(keys.length>16)delete next[keys[0]];lyrics=next}
 property var frames:({})
 property var posters:({})
 function frame(id,path){if(!id || id==='preview' || frames[id]===path)return;const next=Object.assign({},frames);next[id]=path;frames=next}
 function poster(path,url){if(!path || !url || posters[path]===url)return;const next=Object.assign({},posters);next[path]=url;const keys=Object.keys(next);if(keys.length>160)delete next[keys[0]];posters=next}
}
