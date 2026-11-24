import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import qs.services
import qs.components
import qs.components.glass
FloatingWindow{
 id:window;visible:false;implicitWidth:420;implicitHeight:340;title:'Quick Note';color:'transparent'
 function open(){visible=true;Qt.callLater(()=>editor.forceActiveFocus())}
 function save(){if(editor.text.trim()){NotesState.addNote(editor.text);editor.text=''}visible=false}
 Rectangle{anchors.fill:parent;radius:18;color:Theme.isLight ? '#f3f0e2':'#292820';border.width:1;border.color:Theme.cardRim
  ColumnLayout{anchors.fill:parent;anchors.margins:20;spacing:14
   Text{text:'Quick Note';font.family:'SF Pro Display';font.pixelSize:21;font.weight:Font.DemiBold;color:Theme.textPrimary}
   TextArea{id:editor;Layout.fillWidth:true;Layout.fillHeight:true;placeholderText:'New note';color:Theme.textPrimary;wrapMode:TextEdit.Wrap;selectByMouse:true;background:Item{}}
   RowLayout{Layout.alignment:Qt.AlignRight;TahoeButton{text:'Close';onClicked:window.visible=false}TahoeButton{text:'Save';enabled:editor.text.trim().length>0;onClicked:window.save()}}
  }
 }
 Shortcut{sequence:'Escape';onActivated:window.visible=false}
 Shortcut{sequence:'Ctrl+Return';onActivated:window.save()}
}
