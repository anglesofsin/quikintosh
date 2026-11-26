import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects
import Quickshell
import Quickshell.Wayland
import qs.services
import qs.components
Scope {
 PanelWindow {
  id:win
  screen:Quickshell.screens.find(s=>s.name===EmojiState.screenName) || Quickshell.screens[0]
  visible:EmojiState.opened || appearance.running
  onVisibleChanged:if(!visible)EmojiState.finishPaste()
  color:'transparent'
  anchors{top:true;bottom:true;left:true;right:true}
  exclusionMode:ExclusionMode.Ignore
  WlrLayershell.layer:WlrLayer.Overlay
  WlrLayershell.namespace:'quickintosh-emoji-picker'
  WlrLayershell.keyboardFocus:EmojiState.opened ? WlrKeyboardFocus.OnDemand:WlrKeyboardFocus.None
  mask:EmojiState.opened ? null:emptyMask
  Region{id:emptyMask}
  property real progress:EmojiState.opened ? 1:0
  Behavior on progress{NumberAnimation{id:appearance;duration:ShellMotion.duration(100);easing.type:Easing.OutCubic}}
  Connections{target:EmojiState
   function onOpenedChanged(){if(EmojiState.opened){grid.currentIndex=0;search.text=Qt.binding(()=>EmojiState.query);Qt.callLater(()=>search.forceActiveFocus())}else tones.close()}
   function onFilteredChanged(){grid.currentIndex=0;grid.positionViewAtBeginning()}
  }
  Shortcut{sequence:'Escape';enabled:EmojiState.opened;onActivated:EmojiState.close()}
  MouseArea{anchors.fill:parent;enabled:EmojiState.opened;onClicked:EmojiState.close()}
  Item {
   id:card
   width:Math.min(384,win.width-24);height:Math.min(552,Math.max(180,(above ? EmojiState.pointer.y:win.height-EmojiState.pointer.y)-24))
   x:Math.max(12,Math.min(win.width-width-12,EmojiState.pointer.x-45))
   readonly property bool above:EmojiState.pointer.y>win.height/2
   y:Math.max(14,Math.min(win.height-height-14,above ? EmojiState.pointer.y-height-14:EmojiState.pointer.y+14))
   scale:.96+.04*win.progress
   transformOrigin:above ? Item.BottomLeft:Item.TopLeft
   readonly property color fill:Theme.plainSurfaces ? '#292b2e':'#b8202427'
   Rectangle{width:15;height:15;rotation:45;x:Math.max(22,Math.min(card.width-38,EmojiState.pointer.x-card.x-7));y:card.above ? card.height-8:-7;color:card.fill;radius:3}
   Rectangle{anchors.fill:parent;radius:18;color:card.fill;border.width:1;border.color:'#35ffffff'}
   MouseArea{anchors.fill:parent}
   ColumnLayout {
    anchors.fill:parent;anchors.margins:12;spacing:8
    RowLayout {
     Layout.fillWidth:true;Layout.preferredHeight:24
     Button{implicitWidth:24;implicitHeight:24;Accessible.name:I18n.tr('Close');onClicked:EmojiState.close()
      contentItem:Text{text:'×';font.pixelSize:22;color:'#c6cbcc';horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter}
      background:Rectangle{radius:12;color:'#20ffffff'}
     }
     Item{Layout.fillWidth:true}
    }
    RowLayout {
     Layout.fillWidth:true;spacing:7
     TahoeField {
      id:search;Layout.fillWidth:true;implicitHeight:34;font.pixelSize:14;leftPadding:32;color:"#f2f2f4";placeholderTextColor:"#b9bec1"
      placeholderText:I18n.tr('Search');text:EmojiState.query
      onTextEdited:EmojiState.query=text
      cursorVisible:EmojiState.opened && activeFocus
      Accessible.name:I18n.tr('Search emojis')
      background:Rectangle{radius:17;color:'#19ffffff';border.width:search.activeFocus ? 2:0;border.color:Qt.rgba(Theme.accent.r,Theme.accent.g,Theme.accent.b,.65)}
      Image{anchors{left:parent.left;leftMargin:10;verticalCenter:parent.verticalCenter}width:15;height:15;source:Quickshell.shellDir+'/assets/icons/search.svg';sourceSize:Qt.size(30,30);layer.enabled:true;layer.effect:MultiEffect{colorization:1;colorizationColor:"#b9bec1"}}
      Keys.onDownPressed:{grid.forceActiveFocus();grid.currentIndex=Math.max(0,grid.currentIndex)}
      Keys.onReturnPressed:if(EmojiState.filtered.length)EmojiState.choose(EmojiState.filtered[Math.max(0,grid.currentIndex)])
     }
     Button{
      id:toneButton;implicitWidth:30;implicitHeight:32
      Accessible.name:I18n.tr('Skin tone')
      contentItem:Text{text:'✋'+(EmojiState.tone ? String.fromCodePoint(0x1f3fa+EmojiState.tone):'');font.family:'Apple Color Emoji';font.pixelSize:21;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter}
      background:Rectangle{radius:9;color:toneButton.hovered ? '#24ffffff':'transparent'}
      onClicked:tones.open()
     }
    }
    GridView {
     id:grid
     Layout.fillWidth:true;Layout.fillHeight:true
     clip:true;cellWidth:(width-6)/6;cellHeight:50
     model:EmojiState.filtered
     cacheBuffer:100;reuseItems:true
     boundsBehavior:Flickable.StopAtBounds
     keyNavigationEnabled:true
     ScrollBar.vertical:ScrollBar{width:5;policy:ScrollBar.AsNeeded}
     Keys.onReturnPressed:if(currentIndex>=0 && currentIndex<count)EmojiState.choose(EmojiState.filtered[currentIndex])
     delegate:Item {
      id:cell
      required property var modelData
      required property int index
      width:grid.cellWidth;height:grid.cellHeight
      Accessible.role:Accessible.Button;Accessible.name:EmojiState.label(modelData)
      Rectangle{anchors.fill:parent;anchors.margins:3;radius:9;color:mouse.containsMouse || (grid.activeFocus && grid.currentIndex===cell.index) ? '#24ffffff':'transparent';border.width:grid.activeFocus && grid.currentIndex===cell.index ? 1:0;border.color:Theme.accent}
      Text{anchors.centerIn:parent;text:EmojiState.glyph(cell.modelData);font.family:'Apple Color Emoji';font.pixelSize:40;renderType:Text.NativeRendering}
      MouseArea{id:mouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:EmojiState.choose(cell.modelData)}
      ToolTip.visible:mouse.containsMouse;ToolTip.delay:600;ToolTip.text:EmojiState.label(modelData)
     }
     Text{anchors.centerIn:parent;visible:grid.count===0;text:I18n.tr('No emojis found');color:"#d1d4d5";font.pixelSize:13}
    }
    Rectangle{Layout.fillWidth:true;implicitHeight:1;color:Theme.isLight ? '#14000000':'#18ffffff'}
    RowLayout {
     Layout.fillWidth:true;spacing:0
     Repeater{model:EmojiState.categories
      delegate:Button {
       required property var modelData
       Layout.fillWidth:true;Layout.preferredHeight:30
       Accessible.name:I18n.tr(modelData.name);checkable:true;checked:EmojiState.category===modelData.group && !EmojiState.query
       onClicked:{EmojiState.query='';EmojiState.category=modelData.group;search.forceActiveFocus()}
       contentItem:Text{text:parent.modelData.icon;font.family:'Symbols Nerd Font Mono';font.pixelSize:18;color:parent.checked ? Theme.accent:'#d1d4d5';horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter}
       background:Rectangle{radius:8;color:parent.checked ? Qt.rgba(Theme.accent.r,Theme.accent.g,Theme.accent.b,.12):'transparent'}
       ToolTip.visible:hovered;ToolTip.delay:700;ToolTip.text:I18n.tr(modelData.name)
      }
     }
    }
   }
   Popup{
    id:tones;x:card.width-width-8;y:46;padding:6;implicitWidth:6*38+12;implicitHeight:50
    background:Rectangle{radius:12;color:Theme.isLight ? '#f1f1f4':'#303136';border.width:1;border.color:Theme.cardRim}
    contentItem:Row{
     Repeater{model:6
      delegate:Button {
       required property int index
       width:38;height:38
       contentItem:Text{text:'✋'+(parent.index ? String.fromCodePoint(0x1f3fa+parent.index):'');font.family:'Apple Color Emoji';font.pixelSize:24;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter}
       background:Rectangle{radius:8;color:parent.index===EmojiState.tone ? '#24ffffff':'transparent'}
       onClicked:{EmojiState.tone=index;tones.close()}
      }
     }
    }
   }
  }
 }
}
