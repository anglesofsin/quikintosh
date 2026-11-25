import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.folderlistmodel
import Quickshell
import qs.services
Dialog {
 id:root
 property Item glassBackdrop:null
 property string suggestedName:'Screenshot.png'
 signal saveRequested(string path)
 parent:Overlay.overlay
 x:parent ? (parent.width-width)/2 : 0
 y:parent ? (parent.height-height)/2 : 0
 width:Math.min(700,parent ? parent.width-32 : 700)
 height:Math.min(510,parent ? parent.height-32 : 510)
 modal:true;focus:true;title:'Save screenshot';standardButtons:Dialog.Save | Dialog.Cancel
 function folderUrl(value){if(value.startsWith('file:'))return value;if(value.startsWith('~'))value=Quickshell.env('HOME')+value.slice(1);return 'file://'+value}
 onOpened:{folders.folder=folderUrl(ShellConfig.options.capture.lastSaveDirectory || ShellConfig.options.capture.directory);filename.text=suggestedName;Qt.callLater(()=>{filename.forceActiveFocus();filename.selectAll()})}
 onAccepted:{if(!filename.text.trim())return;const directory=folders.folder.toString().replace(/\/$/,'');ShellConfig.options.capture.lastSaveDirectory=directory;saveRequested(directory+'/'+encodeURIComponent(filename.text.trim()))}
 FolderListModel {id:folders;showDirs:true;showFiles:true;showDotAndDotDot:false;showDirsFirst:true;nameFilters:['*.png'];showHidden:false}
 background:CaptureGlass {radius:18}
 header:Label {text:root.title;color:'white';font.pixelSize:18;font.bold:true;padding:18}
 contentItem:ColumnLayout {
  spacing:10
  RowLayout {
   Button {text:'↑';onClicked:folders.folder=folders.parentFolder}
   TextField {Layout.fillWidth:true;text:decodeURIComponent(folders.folder.toString().replace(/^file:\/\//,''));placeholderText:'Directory';onEditingFinished:folders.folder=root.folderUrl(text)}
  }
  ListView {
   Layout.fillWidth:true;Layout.fillHeight:true;clip:true;model:folders
   ScrollBar.vertical:ScrollBar{}
   delegate:ItemDelegate {
    required property string fileName
    required property bool fileIsDir
    required property url fileUrl
    width:ListView.view.width;height:34
    contentItem:Text {text:(parent.fileIsDir ? '▸  ' : '   ')+parent.fileName;color:'#e8e8ed';elide:Text.ElideRight;verticalAlignment:Text.AlignVCenter;font.pixelSize:13}
    onClicked:if(fileIsDir)folders.folder=fileUrl;else filename.text=fileName
   }
   Label {visible:folders.count===0;anchors.centerIn:parent;text:'No PNG images in this directory';color:'#aaaaaf'}
  }
  TextField {id:filename;Layout.fillWidth:true;placeholderText:'File name.png';validator:RegularExpressionValidator {regularExpression:/[^\/\\]+/}}
  Label {Layout.fillWidth:true;text:'PNG image · Existing files are preserved with a numbered name.';color:'#a6a6ad';wrapMode:Text.WordWrap;font.pixelSize:11}
 }
}
