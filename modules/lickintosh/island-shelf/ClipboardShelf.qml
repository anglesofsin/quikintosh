import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import qs.services
Item {
 id:root;property string query:''
 ColumnLayout{anchors.fill:parent;spacing:12
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:qsTr('Clipboard');color:'white';font.family:'SF Pro Display';font.pixelSize:18;font.weight:Font.DemiBold}
   TextField{Layout.preferredWidth:260;placeholderText:qsTr('Search copied text');placeholderTextColor:'#92929a';onTextChanged:root.query=text.toLowerCase();color:'white';font.family:'SF Pro Text';background:Rectangle{radius:12;color:'#222225'}}
   ShelfButton{text:qsTr('Refresh');onClicked:ShelfState.send({action:'clipboard'})}
  }
  ListView{id:list;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:7;model:ShelfState.clips.filter(x=>!root.query || x.text.toLowerCase().includes(root.query));ScrollBar.vertical:ScrollBar{}
   delegate:Rectangle {required property var modelData;width:list.width;height:64;radius:14;color:mouse.containsMouse ? '#29292d':'#17171a'
    RowLayout{anchors.fill:parent;anchors.margins:12;spacing:12
     Image{visible:modelData.kind==='image';Layout.preferredWidth:45;Layout.preferredHeight:40;source:modelData.image;sourceSize:Qt.size(90,80);fillMode:Image.PreserveAspectFit;asynchronous:true}
     Text{Layout.fillWidth:true;text:modelData.text || qsTr('Image');color:'white';font.family:'SF Pro Text';font.pixelSize:13;maximumLineCount:2;wrapMode:Text.Wrap;elide:Text.ElideRight;textFormat:Text.PlainText}
     ShelfButton{text:qsTr('Copy');onClicked:ShelfState.send({action:'copyClip',path:modelData.path})}
    }
    HoverHandler{id:mouse}
   }
   Text{anchors.centerIn:parent;visible:list.count===0;text:qsTr('No clipboard items');color:'#9999a0';font.family:'SF Pro Text';font.pixelSize:14}
  }
 }
 Component.onCompleted:ShelfState.send({action:'clipboard'})
}
