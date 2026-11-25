import QtQuick
import QtQuick.Layouts
import qs.services
import qs.components
ColumnLayout{
 id:root
 property var entry:({})
 property string fontKey:'widgetFont'
 property string label:'Font'
 property bool customEditing:false
 readonly property string selected:entry[fontKey] || ''
 readonly property bool custom:!!selected && !WidgetFonts.families.includes(selected)
 function set(value){const changes={};changes[fontKey]=value;WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,changes)}
 Layout.fillWidth:true;spacing:8
 RowLayout{Layout.fillWidth:true;Layout.minimumHeight:40
  Text{text:I18n.tr(root.label);color:Theme.textPrimary;Layout.fillWidth:true}
  TahoeCombo{Layout.preferredWidth:260;Layout.minimumWidth:140;Layout.maximumWidth:280;model:WidgetFonts.names.concat(['Custom']);currentIndex:root.custom || root.customEditing ? WidgetFonts.names.length:Math.max(0,WidgetFonts.families.indexOf(root.selected));onActivated:i=>{root.customEditing=i===WidgetFonts.names.length;if(!root.customEditing)root.set(WidgetFonts.families[i])}}
 }
 TahoeField{visible:root.custom || root.customEditing;Layout.fillWidth:true;text:root.selected;placeholderText:'Custom font family';onEditingFinished:root.set(text.trim())}
}
