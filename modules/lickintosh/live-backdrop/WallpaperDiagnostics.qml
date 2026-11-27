import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.components
import qs.ui.settings.widgets
import qs.services
ColumnLayout {
 id:root
 Layout.fillWidth:true;spacing:8
 property bool initialized:false
 property bool enabledByUser:false
 property bool ownsMeasurement:false
 property bool received:false
 property var snapshot:[]
 property var ipcPrefix:['quickshell','-p',Quickshell.shellDir,'ipc','call','wallpaperVideo']
 function sync(){if(!initialized)return;const wanted=visible && enabledByUser;if(wanted===ownsMeasurement)return;ownsMeasurement=wanted;if(wanted){received=false;if(!lease.running)lease.running=true;stats.reload()}else{snapshot=[];Quickshell.execDetached(ipcPrefix.concat(['monitor','false']))}}
 onVisibleChanged:sync()
 onEnabledByUserChanged:sync()
 Component.onCompleted:{initialized=true;Qt.callLater(root.sync)}
 Component.onDestruction:if(ownsMeasurement)Quickshell.execDetached(ipcPrefix.concat(['monitor','false']))
 Process{id:lease;command:root.ipcPrefix.concat(['lease']);onExited:code=>{if(code===0)firstReport.restart()}}
 Timer{id:firstReport;interval:120;onTriggered:stats.reload()}
 FileView{
  id:stats;watchChanges:true
  path:(Quickshell.env('XDG_STATE_HOME') || Quickshell.env('HOME')+'/.local/state')+'/lickintosh/settings/wallpaper-playback.json'
  onFileChanged:reload()
  onLoaded:{try{const data=JSON.parse(text());if(data.instance===Quickshell.env('HYPRLAND_INSTANCE_SIGNATURE') && Date.now()-data.time<4000){root.received=true;root.snapshot=(data.streams || []).map(stream=>Object.assign({name:stream.name},stream.frames))}}catch(_){}}
 }
 Text{visible:root.enabledByUser && root.snapshot.length===0;Layout.fillWidth:true;text:I18n.tr(root.received ? 'No animated wallpaper is playing':'Waiting for playback data…');font.family:'SF Pro Text';font.pixelSize:11;color:Theme.textSecondary}
 RowLayout {
  Layout.fillWidth:true
  ConfigSwitch{text:'Playback diagnostics';checked:root.enabledByUser;onToggled:value=>root.enabledByUser=value}
  Item{Layout.fillWidth:true}
 }
 Repeater {
  model:root.enabledByUser ? root.snapshot:[]
  Rectangle {
   required property var modelData
   Layout.fillWidth:true;implicitHeight:details.implicitHeight+24;radius:12;color:Theme.isLight ? '#10000000':'#10ffffff'
   ColumnLayout {
    id:details;anchors{left:parent.left;right:parent.right;top:parent.top;margins:12}spacing:6
    Text{Layout.fillWidth:true;text:modelData.name;elide:Text.ElideMiddle;font.family:'SF Pro Text';font.pixelSize:12;font.weight:Font.DemiBold;color:Theme.textPrimary}
    Text{Layout.fillWidth:true;text:modelData.width+' × '+modelData.height+' · '+modelData.fps.toFixed(1)+' FPS';font.family:'SF Pro Text';font.pixelSize:12;color:Theme.textPrimary}
    Text{Layout.fillWidth:true;text:I18n.tr('Frame interval (95%)')+': '+modelData.p95GapMs.toFixed(1)+' ms · '+I18n.tr('Stalls')+': '+modelData.stallsOver100ms;font.family:'SF Pro Text';font.pixelSize:11;color:Theme.textSecondary;wrapMode:Text.WordWrap}
    Text{Layout.fillWidth:true;text:I18n.tr('Frame storage')+': '+I18n.tr(modelData.frameStorage==='gpu-texture' ? 'GPU texture':modelData.frameStorage==='cpu-memory' ? 'CPU memory':'Unavailable')+' · '+modelData.pixelFormat;font.family:'SF Pro Text';font.pixelSize:11;color:Theme.textSecondary;wrapMode:Text.WordWrap}
   }
  }
 }
 Timer{interval:3000;repeat:true;running:root.ownsMeasurement;onTriggered:if(!lease.running)lease.running=true}
}
