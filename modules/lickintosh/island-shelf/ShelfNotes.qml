import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import qs.services
Item{
 id:root
 objectName:'shelf-notes'
 property string selectedId:''
 property bool composing:false
 readonly property var selected:NotesState.notes.find(n=>n.id===selectedId) || null
 readonly property bool editing:composing || selected!==null
 property bool held:false
 function syncHold(){if(held!==editing){held=editing;ShelfState.interaction(held)}}
 onEditingChanged:syncHold()
 Component.onDestruction:if(held)ShelfState.interaction(false)
 function save(){if(!editor.text.trim())return;if(composing)NotesState.addNote(editor.text);else if(selected)NotesState.updateNote(selected.id,editor.text);composing=false;selectedId=''}
 ColumnLayout{anchors.fill:parent;spacing:9
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:qsTr('Notes');font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.title;font.weight:Font.DemiBold;color:ShelfStyle.primary}
   ShelfButton{flat:true;icon:root.editing ? 'notch/check.svg':'notch/edit-3.svg';accessibleLabel:root.editing ? qsTr('Save note'):qsTr('New note');onClicked:{if(root.editing)root.save();else{root.composing=true;editor.text='';editor.forceActiveFocus()}}}
  }
  ListView{id:list;visible:!root.editing;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;model:NotesState.notes;spacing:6
   delegate:Rectangle{required property var modelData;width:list.width;height:45;radius:16;color:area.containsMouse ? ShelfStyle.surfaceHover:ShelfStyle.surface
    ColumnLayout{anchors.fill:parent;anchors.leftMargin:12;anchors.rightMargin:12;anchors.topMargin:6;anchors.bottomMargin:6;spacing:2
     Text{Layout.fillWidth:true;text:modelData.text.split('\n')[0];textFormat:Text.PlainText;elide:Text.ElideRight;color:ShelfStyle.primary;font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.body;font.weight:Font.DemiBold}
     Text{Layout.fillWidth:true;text:modelData.text.split('\n').slice(1).join(' ') || qsTr('Open note');textFormat:Text.PlainText;elide:Text.ElideRight;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:10}
    }
    MouseArea{id:area;anchors.fill:parent;hoverEnabled:true;onClicked:{root.selectedId=modelData.id;editor.text=modelData.text;editor.forceActiveFocus()}}
   }
   Text{visible:list.count===0;anchors.centerIn:parent;text:qsTr('Your quick notes appear here.');font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.body;color:ShelfStyle.secondary}
  }
  ScrollView{visible:root.editing;Layout.fillWidth:true;Layout.fillHeight:true
   TextArea{id:editor;wrapMode:TextEdit.Wrap;color:ShelfStyle.primary;selectionColor:'#66888888';font.family:ShelfStyle.textFamily;font.pixelSize:14;placeholderText:qsTr('Write a note…');background:Rectangle{radius:16;color:ShelfStyle.surface}}
  }
  RowLayout{visible:root.editing;Layout.fillWidth:true
   ShelfButton{flat:true;text:qsTr('Cancel');onClicked:{root.composing=false;root.selectedId=''}}
   Item{Layout.fillWidth:true}
   ShelfButton{visible:!root.composing;flat:true;icon:'notch/trash-2.svg';accessibleLabel:qsTr('Delete note');onClicked:{if(root.selected)NotesState.removeNote(root.selected.id);root.selectedId=''}}
  }
 }
}
