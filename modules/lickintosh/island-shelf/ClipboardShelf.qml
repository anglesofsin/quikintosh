import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import Quickshell.Widgets
import qs.services
Item {
 id:root
 property string query:''
 property string category:'all'
 property string selectedPath:''
 readonly property var entries:ShelfState.clips.filter(x=>(category==='all' || x.kind===category) && (!query || String(x.text).toLowerCase().includes(query)))
 ColumnLayout{anchors.fill:parent;spacing:14
  RowLayout{Layout.fillWidth:true;spacing:10
   Repeater{model:[{key:'all',label:qsTr('Clipboard'),icon:'clipboard'},{key:'color',label:qsTr('Colors'),icon:'droplet'},{key:'link',label:qsTr('Links'),icon:'link'},{key:'image',label:qsTr('Images'),icon:'image'}]
    delegate:ShelfButton{required property var modelData;text:modelData.label;icon:'notch/'+modelData.icon+'.svg';flat:true;selected:root.category===modelData.key;onClicked:root.category=modelData.key}
   }
   Item{Layout.fillWidth:true}
   TextField{Layout.preferredWidth:Math.min(180,root.width*.18);implicitHeight:30;leftPadding:12;rightPadding:12;placeholderText:qsTr('Search');placeholderTextColor:ShelfStyle.secondary;onTextChanged:root.query=text.toLowerCase();color:ShelfStyle.primary;font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.body;selectByMouse:true;background:Rectangle{radius:15;color:ShelfStyle.surface;border.width:parent.activeFocus ? 1:0;border.color:'#66ffffff'}}
   ShelfButton{flat:true;icon:'notch/refresh-cw.svg';accessibleLabel:qsTr('Refresh clipboard');onClicked:ShelfState.send({action:'clipboard'})}
  }
  ListView{id:list;Layout.fillWidth:true;Layout.fillHeight:true;orientation:ListView.Horizontal;clip:true;spacing:12;model:root.entries;boundsBehavior:Flickable.StopAtBounds;reuseItems:true
   ScrollBar.horizontal:ScrollBar{policy:ScrollBar.AsNeeded}
   delegate:ClippingRectangle{id:card;required property var modelData;width:220;height:list.height-12;radius:16;color:card.colorValue ? String(modelData.text).trim():'#141616';border.width:root.selectedPath===modelData.path ? 3:1;border.color:root.selectedPath===modelData.path ? 'white':ShelfStyle.outline
    readonly property bool colorValue:/^#[a-fA-F0-9]{6}$/.test(String(modelData.text).trim())
    ColumnLayout{z:1;anchors.fill:parent;spacing:0
     RowLayout{Layout.fillWidth:true;Layout.preferredHeight:30;Layout.leftMargin:12;Layout.rightMargin:8;spacing:6
      ShelfIcon{size:12;Layout.preferredWidth:12;Layout.preferredHeight:12;icon:card.modelData.kind==='image' ? 'notch/image.svg':'notch/type.svg';color:ShelfStyle.secondary}
      Text{Layout.fillWidth:true;text:(card.modelData.pinned ? '• ':'')+(card.modelData.kind==='image' ? qsTr('Image'):card.colorValue ? qsTr('Color'):card.modelData.kind==='link' ? qsTr('Link'):qsTr('Text'));font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.caption;color:ShelfStyle.secondary}
      ShelfButton{flat:true;implicitWidth:24;implicitHeight:24;icon:'notch/more-horizontal.svg';accessibleLabel:qsTr('Clipboard options');onClicked:clipMenu.popup()}
     }
     Rectangle{Layout.fillWidth:true;Layout.fillHeight:true;color:card.colorValue ? String(card.modelData.text).trim():'transparent'
      Image{anchors.fill:parent;anchors.margins:8;visible:card.modelData.kind==='image';source:visible ? card.modelData.image:'';sourceSize:Qt.size(440,360);fillMode:Image.PreserveAspectFit;asynchronous:true}
      Text{anchors.fill:parent;anchors.margins:14;visible:card.modelData.kind!=='image';text:card.modelData.text || '';textFormat:Text.PlainText;wrapMode:Text.Wrap;maximumLineCount:8;elide:Text.ElideRight;font.family:ShelfStyle.textFamily;font.pixelSize:card.colorValue ? 20:ShelfStyle.body;font.weight:card.colorValue ? Font.DemiBold:Font.Normal;color:card.colorValue ? '#111114':ShelfStyle.primary;verticalAlignment:card.colorValue ? Text.AlignVCenter:Text.AlignTop;horizontalAlignment:card.colorValue ? Text.AlignHCenter:Text.AlignLeft}
     }
     Text{Layout.fillWidth:true;Layout.margins:12;text:card.modelData.kind==='image' ? qsTr('Click to copy'):qsTr('%1 characters').arg(String(card.modelData.text).length);font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.caption;color:ShelfStyle.secondary;elide:Text.ElideRight}
    }
    MouseArea{id:area;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;acceptedButtons:Qt.LeftButton|Qt.RightButton;onClicked:e=>{root.selectedPath=card.modelData.path;if(e.button===Qt.RightButton)clipMenu.popup();else ShelfState.send({action:'copyClip',path:card.modelData.path})}}
    ShelfMenu{id:clipMenu
     ShelfMenuItem{text:card.modelData.pinned ? qsTr('Unpin'):qsTr('Pin');onTriggered:ShelfState.send({action:'pinClip',path:card.modelData.path})}
     ShelfMenuItem{text:qsTr('Copy');onTriggered:ShelfState.send({action:'copyClip',path:card.modelData.path})}
     ShelfMenuItem{text:qsTr('Remove');onTriggered:ShelfState.send({action:'removeClip',path:card.modelData.path})}
    }
    activeFocusOnTab:true;Keys.onReturnPressed:ShelfState.send({action:'copyClip',path:card.modelData.path})
    Accessible.role:Accessible.Button;Accessible.name:qsTr('Copy %1').arg(card.modelData.kind==='image' ? qsTr('image'):String(card.modelData.text).slice(0,100))
   }
   Text{anchors.centerIn:parent;visible:list.count===0;text:root.query ? qsTr('No matching items'):qsTr('No clipboard items');color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.body}
  }
 }
 onVisibleChanged:if(visible)ShelfState.send({action:'clipboard'})
 Component.onCompleted:ShelfState.send({action:'clipboard'})
}
