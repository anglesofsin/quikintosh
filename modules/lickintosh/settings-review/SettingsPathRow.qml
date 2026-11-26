import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import Quickshell
import qs.components
import qs.services
RowLayout {
 id:root
 property string label:''
 property string path:''
 signal edited(string value)
 Layout.fillWidth:true;Layout.minimumHeight:48;spacing:14
 Text{Layout.fillWidth:true;text:I18n.tr(root.label);font.family:'SF Pro Text';font.pixelSize:13;color:Theme.textPrimary;wrapMode:Text.WordWrap}
 TahoeField{Layout.preferredWidth:190;Layout.maximumWidth:root.width*.47;text:root.path;selectByMouse:true;Accessible.name:I18n.tr(root.label);onEditingFinished:if(text!==root.path)root.edited(text)}
 TahoeButton{text:I18n.tr('Choose…');onClicked:folder.open()}
 FolderDialog{id:folder;title:I18n.tr(root.label);currentFolder:'file://'+(root.path.startsWith('~/') ? Quickshell.env('HOME')+root.path.slice(1):root.path.startsWith('/') ? root.path:Quickshell.env('HOME'));onAccepted:root.edited(decodeURIComponent(String(selectedFolder).replace(/^file:\/\//,'')))}
}
