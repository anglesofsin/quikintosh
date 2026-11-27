import QtQuick
import qs.services
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs
Item{
 id:root;objectName:'shelf-vault'
 property string note:''
 property string modified:''
 property bool dirty:false
 property bool loading:false
 property bool held:false
 onDirtyChanged:{if(held!==dirty){held=dirty;ShelfState.interaction(held)}}
 Component.onDestruction:if(held)ShelfState.interaction(false)
 function open(name){if(dirty)return;loading=true;ShelfState.send({action:'vaultRead',name:name})}
 Component.onCompleted:ShelfState.send({action:'vaultList'})
 Connections{target:ShelfState;function onVaultNote(name,text,modified){root.note=name;root.modified=modified;editor.text=text;root.dirty=false;root.loading=false}}
 FolderDialog{id:folder;title:qsTr('Choose your Obsidian vault');onAccepted:ShelfState.send({action:'vaultSelect',path:String(selectedFolder)})}
 ColumnLayout{anchors.fill:parent;spacing:8
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:root.note || qsTr('Obsidian · Markdown vault');elide:Text.ElideMiddle;color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:16;font.weight:Font.DemiBold}
   ShelfButton{flat:true;text:qsTr('Choose vault');enabled:!root.dirty;onClicked:folder.open()}
   ShelfButton{visible:root.note!=='';text:qsTr('Save');selected:true;enabled:root.dirty;onClicked:ShelfState.send({action:'vaultSave',name:root.note,text:editor.text,modified:root.modified})}
  }
  RowLayout{Layout.fillWidth:true;Layout.fillHeight:true;spacing:12
   ListView{id:notes;Layout.preferredWidth:170;Layout.fillHeight:true;clip:true;spacing:4;model:ShelfState.vaultInfo.notes || []
    delegate:ItemDelegate{required property var modelData;width:notes.width;height:34;enabled:!root.dirty;onClicked:root.open(modelData.name)
     contentItem:Text{text:parent.modelData.name.replace(/\.md$/,'');elide:Text.ElideMiddle;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:12;verticalAlignment:Text.AlignVCenter}
     background:Rectangle{radius:9;color:root.note===parent.modelData.name ? '#307aff':'#15ffffff'}
    }
   }
   ScrollView{clip:true;Layout.fillWidth:true;Layout.fillHeight:true
    ShelfTextArea{id:editor;enabled:root.note!=='';wrapMode:TextEdit.Wrap;selectByMouse:true;placeholderText:ShelfState.vaultInfo.path ? qsTr('Choose a note'):qsTr('Choose a vault. Files remain in your existing Markdown folder.');color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:14; onTextChanged:if(root.note)root.dirty=true}
   }
  }
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:root.dirty ? qsTr('Unsaved changes'):ShelfState.vaultInfo.path || qsTr('No vault selected');elide:Text.ElideMiddle;color:'#aaaab3';font.family:ShelfStyle.textFamily;font.pixelSize:11}
   ShelfButton{visible:root.dirty;flat:true;text:qsTr('Discard');onClicked:{root.dirty=false;root.open(root.note)}}
   ShelfButton{visible:!root.dirty && !!ShelfState.vaultInfo.path;flat:true;text:qsTr('Refresh');onClicked:ShelfState.send({action:'vaultList'})}
  }
 }
}
