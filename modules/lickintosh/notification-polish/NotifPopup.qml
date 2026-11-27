import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import qs.services
import qs.components
import qs.components.glass
import qs.ui.topbar.statusarea.notifcenter
Scope{
 id:root
 property var notifServer:null
 property bool warmed:false
 property var displayScreen:Quickshell.screens[0]
 readonly property bool hasPopups:NotifService.popupModel.count>0
 onHasPopupsChanged:if(hasPopups){displayScreen=Quickshell.screens.find(s=>s.name===Hyprland.focusedMonitor?.name) || Quickshell.screens[0];warmed=true}
 readonly property int popupWidth:Math.min(378,(root.displayScreen?.width || 1920)-40)
 Loader{
  active:root.warmed || root.hasPopups
  sourceComponent:PanelWindow{
   visible:root.hasPopups;color:'transparent';exclusiveZone:-1
   screen:root.displayScreen
   anchors{top:true;right:true}
   implicitWidth:root.popupWidth+40;implicitHeight:Math.max(1,column.implicitHeight+64)
   WlrLayershell.namespace:'quickintosh:notification-banners';WlrLayershell.layer:WlrLayer.Overlay;WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
   mask:Region{item:column}
   GlassBackdrop{id:bannerGlass;element:'notifpopup';gateEnabled:false}
   Column{
    id:column;anchors{top:parent.top;right:parent.right;topMargin:48;rightMargin:14};spacing:10
    move:Transition{NumberAnimation{properties:'y';duration:ShellMotion.spatial(.48);easing.type:Easing.OutCubic}}
    Repeater{
     model:NotifService.popupModel
     delegate:Item{
      id:wrap
      required property var notifObj
      width:root.popupWidth;height:card.height*(leaving ? progress:1)
      property real progress:0
      property bool leaving:false
      property bool dismissAfter:false
      readonly property string app:String(notifObj?.appName || '')
      readonly property string summary:SettingsPreferences.canPreview() ? String(notifObj?.summary || ''):I18n.tr('Notification')
      readonly property string body:SettingsPreferences.canPreview() ? String(notifObj?.body || '').replace(/<br\s*\/?\s*>/gi,'\n').replace(/<[^>]*>/g,''):''
      readonly property var actions:SettingsPreferences.canPreview() ? Array.from(notifObj?.actions || []).filter(action=>action.identifier!=='default'):[]
      function hide(dismiss){if(leaving)return;leaving=true;dismissAfter=!!dismiss;arrival.stop();departure.start()}
      function invoke(action){if(action)action.invoke();else NotifService.openAppOptions(notifObj);hide(true)}
      Component.onCompleted:arrival.start()
      NumberAnimation{id:arrival;target:wrap;property:'progress';from:0;to:1;duration:ShellMotion.enter(.56);easing.type:Easing.OutCubic}
      NumberAnimation{id:departure;target:wrap;property:'progress';to:0;duration:ShellMotion.exit(.5);easing.type:Easing.InOutCubic;onFinished:{const n=wrap.notifObj,dismiss=wrap.dismissAfter;NotifService.removePopup(n,true);if(dismiss && n)n.dismiss()}}
      Connections{target:NotifService;function onDismissGenChanged(){wrap.hide(false)}function onPopupRemovalRequested(notification){if(notification===wrap.notifObj)wrap.hide(false)}}
      HoverHandler{id:hover}
      Timer{interval:SettingsPreferences.notifications.duration;running:!wrap.leaving && !hover.hovered;onTriggered:wrap.hide(false)}
      Item{
       id:card;width:parent.width;height:content.implicitHeight+28;opacity:wrap.progress;scale:.97+.03*wrap.progress;transformOrigin:Item.TopRight
       transform:Translate{x:(1-wrap.progress)*38}
       BoxGlass{anchors.fill:parent;radius:23;visible:!bannerGlass.nativeOverride}
       Rectangle{anchors.fill:parent;radius:23;color:bannerGlass.nativeOverride ? (Theme.isLight ? '#14ffffff':'#10000000'):'transparent';border.width:1;border.color:Theme.isLight ? '#20000000':'#25ffffff'}
       MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:wrap.invoke(NotifService.findDefaultAction(wrap.notifObj))}
       RowLayout{
        id:content;anchors{left:parent.left;right:parent.right;top:parent.top;margins:14};spacing:12
        Item{Layout.preferredWidth:38;Layout.preferredHeight:38;Layout.alignment:Qt.AlignTop;Layout.topMargin:3
         Rectangle{anchors.fill:parent;radius:10;color:Theme.fillControl;visible:!appIcon.resolvedSource;Text{anchors.centerIn:parent;text:wrap.app.charAt(0).toUpperCase() || '•';color:Theme.textPrimary;font.pixelSize:20;font.weight:Font.DemiBold}}
         NotifIcon{id:appIcon;anchors.fill:parent;icon:wrap.notifObj?.appIcon || '';appName:wrap.app;size:38;visible:!!resolvedSource}
        }
        ColumnLayout{Layout.fillWidth:true;spacing:5
         RowLayout{Layout.fillWidth:true
          Text{Layout.fillWidth:true;text:wrap.app;color:Theme.textSecondary;font.pixelSize:11;font.weight:Font.DemiBold;elide:Text.ElideRight;textFormat:Text.PlainText}
          Text{text:I18n.tr('Now');color:Theme.textSecondary;font.pixelSize:10}
          TahoeButton{implicitWidth:24;implicitHeight:24;text:'×';Accessible.name:'Dismiss';onClicked:wrap.hide(true)}
         }
         Text{visible:!!wrap.summary;Layout.fillWidth:true;text:wrap.summary;color:Theme.textPrimary;font.family:'SF Pro Text';font.pixelSize:13;font.weight:Font.DemiBold;wrapMode:Text.WordWrap;maximumLineCount:2;elide:Text.ElideRight;textFormat:Text.PlainText}
         Text{visible:!!wrap.body;Layout.fillWidth:true;text:wrap.body;color:Theme.textSecondary;font.family:'SF Pro Text';font.pixelSize:12;wrapMode:Text.WordWrap;maximumLineCount:3;elide:Text.ElideRight;textFormat:Text.PlainText}
         Flow{visible:wrap.actions.length>0;Layout.fillWidth:true;spacing:6
          Repeater{model:wrap.actions;delegate:TahoeButton{required property var modelData;text:modelData.text;onClicked:wrap.invoke(modelData)}}
         }
        }
       }
      }
     }
    }
   }
  }
 }
}
