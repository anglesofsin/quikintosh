import QtQuick
import Quickshell
import qs.services
import qs.components
Item{
 id:root
 property var look:null
 property string size:'m'
 property var widgetData:null
 property bool isSnapshot:false
 property bool desktopWidget:false
 readonly property bool fullBleed:true
 readonly property bool allowed:desktopWidget && !isSnapshot && widgetData?.id!=='preview' && CreativeMedia.desktopActive && visible
 property var paths:['','']
 property int front:0
 property int target:1
 property bool switching:false
 property real progress:1
 readonly property string transition:widgetData?.mediaTransition || 'dissolve'
 readonly property int transitionMs:SettingsPreferences.accessibility.reduceMotion || transition==='cut' ? 0:Math.max(0,Math.min(2000,widgetData?.mediaTransitionMs ?? 550))
 function request(path){
  if(paths[front]===path)return
  if(!paths[front]){const list=['',''];list[front]=path;paths=list;return}
  motion.stop();switching=false;target=1-front
  const list=paths.slice();list[target]=path;paths=list
  if(!path){front=target;return}
  Qt.callLater(check)
 }
 function check(){if(paths[target]===playlist.path && paths[target] && frames.itemAt(target)?.ready && !switching){progress=0;switching=true;motion.restart()}}
 MediaPlaylist{id:playlist;widgetData:root.widgetData;isSnapshot:root.isSnapshot;active:root.allowed;onPathChanged:root.request(path)}
 NumberAnimation{id:motion;target:root;property:'progress';from:0;to:1;duration:root.transitionMs;easing.type:Easing.InOutCubic;onFinished:{root.front=root.target;root.switching=false;const list=root.paths.slice();list[1-root.front]='';root.paths=list}}
 CFClippingRect{
  anchors.fill:parent;radius:root.widgetData?.shape==='circle' ? Math.min(width,height)/2:root.widgetData?.shape==='rectangle' ? 0:(root.widgetData?.cornerRadius ?? 22);color:'transparent'
  Repeater{
   id:frames;model:2
   delegate:MediaFrame{
    required property int index
    width:parent.width;height:parent.height
    path:root.paths[index];desktopWidget:root.desktopWidget;isSnapshot:root.isSnapshot
    playing:root.allowed && index===(root.switching ? root.target:root.front)
    sound:!!root.widgetData?.mediaSound;volume:root.widgetData?.mediaVolume ?? .35
    loop:!root.widgetData?.mediaFinishVideo || playlist.files.length<2
    fit:root.widgetData?.imageFit || 'crop'
    z:index===root.target && root.switching ? 2:1
    opacity:index===root.front ? 1:root.switching && index===root.target ? root.progress:0
    x:root.switching && root.transition==='slide' ? (index===root.target ? (1-root.progress)*width:-root.progress*width):0
    scale:root.switching && root.transition==='zoom' && index===root.target ? .92+.08*root.progress:1
    visible:!!path && (index===root.front || root.switching && index===root.target)
    onReadyChanged:root.check()
    onFinished:if(index===root.front && root.allowed && root.widgetData?.mediaFinishVideo)playlist.next()
   }
  }
 }
 Column{
  anchors.centerIn:parent;width:parent.width-28;spacing:8
  visible:!playlist.path || !!playlist.error || !!frames.itemAt(root.front)?.error
  Text{width:parent.width;text:playlist.error || frames.itemAt(root.front)?.error || 'Your media, your space';color:root.look?.primary || Theme.textPrimary;horizontalAlignment:Text.AlignHCenter;wrapMode:Text.WordWrap;font.family:'SF Pro Display';font.pixelSize:Math.min(20,root.width*.06);font.weight:Font.DemiBold}
  Text{width:parent.width;text:'Add photos, GIFs, videos or a folder';color:root.look?.secondary || Theme.textSecondary;horizontalAlignment:Text.AlignHCenter;wrapMode:Text.WordWrap;font.pixelSize:12}
 }
 Component.onCompleted:request(playlist.path)
}
