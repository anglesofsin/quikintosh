import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import qs.services
import qs.components
import qs.components.glass
Scope {
 id:root
 readonly property bool opened:WidgetState.galleryZone!==''
 property string category:'all'
 property string query:''
 readonly property var filtered:WidgetRegistry.types.filter(t=>(category==='all' || t.type===category) && (!query || t.title.toLowerCase().includes(query.toLowerCase())))
 onOpenedChanged:if(opened){category='all';query=''}
 Loader{
  active:root.opened
  sourceComponent:PanelWindow{
   id:win;anchors{left:true;right:true;bottom:true}
   implicitHeight:Math.min(screen.height-60,580);color:'transparent';exclusiveZone:-1
   WlrLayershell.namespace:'lickintosh:widget-gallery';WlrLayershell.layer:WlrLayer.Overlay
   WlrLayershell.keyboardFocus:WidgetState.typing ? WlrKeyboardFocus.None:WlrKeyboardFocus.Exclusive
   mask:Region{item:panel}
   GlassBackdrop{element:'menus'}
   BoxGlass{
    id:panel;anchors.horizontalCenter:parent.horizontalCenter;anchors.bottom:parent.bottom;anchors.bottomMargin:18
    width:Math.min(parent.width-40,1080);height:parent.height-24;radius:24;color:Theme.isLight ? '#d8f0f0f4':'#d824252c'
    FocusScope{
     anchors.fill:parent;focus:true;Keys.onEscapePressed:WidgetState.closeGallery()
     RowLayout{
      anchors.fill:parent;anchors.margins:16;spacing:20
      ColumnLayout{
       Layout.preferredWidth:204;Layout.minimumWidth:204;Layout.maximumWidth:204;Layout.fillHeight:true;spacing:12
       Text{text:'Widgets';font.family:'SF Pro Display';font.pixelSize:25;font.weight:Font.Bold;color:Theme.textPrimary;Layout.leftMargin:8}
       TextField{Layout.fillWidth:true;placeholderText:'Search Widgets';selectByMouse:true;text:root.query;onTextEdited:root.query=text}
       ListView{
        Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:3
        model:[{type:'all',title:'All Widgets',icon:'notch/columns.svg',tint:'#8e8e93'}].concat(WidgetRegistry.types)
        delegate:Rectangle{
         required property var modelData;width:ListView.view.width;height:35;radius:8;color:root.category===modelData.type ? '#285b8cbe':categoryMouse.containsMouse ? '#16ffffff':'transparent'
         RowLayout{anchors.fill:parent;anchors.leftMargin:9;anchors.rightMargin:8;spacing:9
          Rectangle{width:24;height:24;radius:6;color:modelData.tint || '#888888';Image{anchors.fill:parent;anchors.margins:4;source:Quickshell.shellDir+'/assets/icons/'+modelData.icon;sourceSize:Qt.size(32,32)}}
          Text{text:modelData.title;Layout.fillWidth:true;color:Theme.textPrimary;font.family:'SF Pro Text';font.pixelSize:12;elide:Text.ElideRight}
         }
         MouseArea{id:categoryMouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:{root.category=modelData.type;list.positionViewAtBeginning()}}
        }
       }
      }
      Rectangle{Layout.fillHeight:true;implicitWidth:1;color:'#24a0a0a0'}
      ColumnLayout{
       Layout.fillWidth:true;Layout.minimumWidth:0;Layout.fillHeight:true;spacing:10
       RowLayout{Layout.fillWidth:true
        Text{text:WidgetState.galleryZone==='desktop' ? 'Desktop Widgets':'Notification Center Widgets';font.pixelSize:17;font.family:'SF Pro Display';font.weight:Font.DemiBold;color:Theme.textPrimary;Layout.fillWidth:true}
        ComboBox{model:['Automatic','Full Color','Clear','Tinted'];currentIndex:Math.max(0,['auto','color','clear','tinted'].indexOf(WidgetState.galleryTheme));onActivated:i=>WidgetState.galleryTheme=['auto','color','clear','tinted'][i]}
       }
       ListView{
        id:list;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;reuseItems:true;cacheBuffer:100;spacing:24
        model:root.filtered;ScrollBar.vertical:ScrollBar{}
        delegate:Column{
         id:section;required property var modelData;width:list.width;spacing:12
         Text{text:section.modelData.title;color:Theme.textPrimary;font.family:'SF Pro Display';font.pixelSize:16;font.weight:Font.DemiBold}
         Flickable{
          width:parent.width;height:previews.height+6;contentWidth:previews.width;clip:true;boundsBehavior:Flickable.StopAtBounds
          Row{
           id:previews;spacing:16
           Repeater{
            model:WidgetRegistry.tilesOf(section.modelData.type)
            delegate:Column{
             id:tile;required property var modelData;readonly property var dims:WidgetState.sizeOf(modelData.size);spacing:8
             Item{
              id:face;width:tile.dims.w*.78;height:tile.dims.h*.78
              Drag.active:drag.active;Drag.dragType:Drag.Automatic;Drag.supportedActions:Qt.CopyAction;Drag.proposedAction:Qt.CopyAction
              Drag.mimeData:({'text/plain':'widget:'+section.modelData.type+':'+tile.modelData.size+':'+(tile.modelData.variant || '')+':'+WidgetState.galleryTheme})
              Drag.hotSpot.x:width/2;Drag.hotSpot.y:height/2
              WidgetView{transformOrigin:Item.TopLeft;scale:.78;widgetData:({id:'preview',type:section.modelData.type,variant:tile.modelData.variant,size:tile.modelData.size,theme:WidgetState.galleryTheme})}
              Rectangle{anchors.fill:parent;radius:18;color:addMouse.containsMouse ? '#16ffffff':'transparent';border.width:addMouse.containsMouse ? 1:0;border.color:'#60ffffff'}
              Rectangle{anchors.right:parent.right;anchors.top:parent.top;anchors.margins:7;width:23;height:23;radius:12;visible:addMouse.containsMouse;color:'#30bd62';Text{anchors.centerIn:parent;text:'+';color:'white';font.pixelSize:20}}
              MouseArea{id:addMouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onPressed:face.grabToImage(result=>face.Drag.imageSource=result.url);onClicked:WidgetState.addWidget(WidgetState.galleryZone,section.modelData.type,tile.modelData.size,tile.modelData.variant,WidgetState.galleryTheme)}
              DragHandler{id:drag;target:null;grabPermissions:PointerHandler.CanTakeOverFromAnything}
             }
             Text{width:face.width;text:tile.modelData.label;color:Theme.textSecondary;horizontalAlignment:Text.AlignHCenter;font.pixelSize:11}
            }
           }
          }
         }
        }
        Text{anchors.centerIn:parent;text:'No Widgets Found';visible:list.count===0;color:Theme.textSecondary}
       }
       RowLayout{Layout.fillWidth:true
        Text{Layout.fillWidth:true;text:'Click to add, or drag a widget onto your desktop.';font.pixelSize:11;color:Theme.textSecondary;wrapMode:Text.WordWrap}
        Button{text:'Done';highlighted:true;onClicked:WidgetState.closeGallery()}
       }
      }
     }
    }
   }
  }
 }
}
