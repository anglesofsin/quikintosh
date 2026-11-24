import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import Quickshell
import Quickshell.Wayland
import qs.services
import qs.components
import qs.components.glass
Scope {
 id:root
 readonly property var entry:WidgetState.entryOf(WidgetState.editingZone,WidgetState.editingId)
 Loader{
  active:WidgetState.editingId!=='' && root.entry!==null
  sourceComponent:FloatingWindow{
   id:win;visible:true;title:'Edit Widget';implicitWidth:460;implicitHeight:column.implicitHeight+40;color:'transparent'
   onClosed:WidgetState.editingId=''

   BoxGlass{
    anchors.fill:parent;radius:22;color:Theme.isLight ? '#f3f3f6':'#252529'
    MouseArea{anchors.fill:parent}
    ColumnLayout{
     id:column;anchors{left:parent.left;right:parent.right;top:parent.top;margins:20}spacing:14
     Text{text:'Edit '+(WidgetRegistry.info(root.entry.type)?.title || 'Widget');font.family:'SF Pro Display';font.pixelSize:20;color:Theme.textPrimary;font.weight:Font.DemiBold}
     RowLayout{Layout.fillWidth:true
      Text{text:'Size';color:Theme.textPrimary;Layout.fillWidth:true}
      ComboBox{model:WidgetRegistry.sizesOf(root.entry.type,root.entry.variant || '');textRole:'';currentIndex:Math.max(0,model.indexOf(root.entry.size));displayText:WidgetRegistry.sizeLabels[currentText] || currentText;onActivated:i=>WidgetState.resizeWidget(WidgetState.editingZone,WidgetState.editingId,model[i])}
     }
     RowLayout{Layout.fillWidth:true
      Text{text:'Appearance';color:Theme.textPrimary;Layout.fillWidth:true}
      ComboBox{model:['Follow Settings','Full Color','Clear','Light','Dark','Tinted'];currentIndex:Math.max(0,['auto','color','clear','light','dark','tinted'].indexOf(root.entry.theme || 'auto'));onActivated:i=>WidgetState.setTheme(WidgetState.editingZone,WidgetState.editingId,['auto','color','clear','light','dark','tinted'][i])}
     }
     RowLayout{visible:root.entry.type==='clock';Layout.fillWidth:true
      Text{text:'Clock';color:Theme.textPrimary;Layout.fillWidth:true}
      ComboBox{model:['Analog','Digital'];currentIndex:root.entry.variant==='digital' ? 1:0;onActivated:i=>{WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{variant:i===1 ? 'digital':'analog'});if(i===0 && root.entry.size!=='s')WidgetState.resizeWidget(WidgetState.editingZone,WidgetState.editingId,'s')}}
     }
     RowLayout{visible:root.entry.type==='image';Layout.fillWidth:true
      Text{text:'Photo';color:Theme.textPrimary;Layout.fillWidth:true}
      Button{text:'Choose Photo…';onClicked:picker.open()}
     }
     TextField{visible:root.entry.type==='image';Layout.fillWidth:true;text:root.entry.image || '';placeholderText:'Image or GIF path';selectByMouse:true;color:Theme.textPrimary;onEditingFinished:WidgetState.setImage(WidgetState.editingZone,WidgetState.editingId,text.trim());background:Rectangle{radius:8;color:Theme.fillControl}}
     Button{visible:root.entry.type==='image' && !!root.entry.image;text:'Remove Image';onClicked:WidgetState.setImage(WidgetState.editingZone,WidgetState.editingId,'')}
     RowLayout{Layout.alignment:Qt.AlignRight
      Button{text:'Remove Widget';onClicked:{WidgetState.removeWidget(WidgetState.editingZone,WidgetState.editingId);WidgetState.editingId=''}}
      Button{text:'Done';highlighted:true;onClicked:WidgetState.editingId=''}
     }
    }
   }
   Shortcut{sequence:'Escape';onActivated:WidgetState.editingId=''}
   FileDialog{id:picker;title:'Choose Photo';nameFilters:['Images (*.png *.jpg *.jpeg *.webp *.avif *.gif *.bmp)'];onAccepted:WidgetState.setImage(WidgetState.editingZone,WidgetState.editingId,decodeURIComponent(String(selectedFile).replace(/^file:\/\//,'')))}
  }
 }
}
