import QtQuick
import qs.services
import QtQuick.Controls.Basic
import QtQuick.Layouts
Item {
 id:root
 objectName:'shelf-teleprompter'
 property bool reading:false
 property bool playing:false
 property bool mirrored:false
 property real pixelsPerSecond:28
 property real fontSize:24
 property bool held:false
 onPlayingChanged:{if(held!==playing){held=playing;ShelfState.interaction(held)}}
 onVisibleChanged:if(!visible)playing=false
 FrameAnimation{running:root.visible && root.reading && root.playing;onTriggered:{scroller.contentY=Math.min(Math.max(0,scroller.contentHeight-scroller.height),scroller.contentY+root.pixelsPerSecond*Math.min(frameTime,.1));if(scroller.contentY>=scroller.contentHeight-scroller.height)root.playing=false}}
 ColumnLayout{anchors.fill:parent;spacing:9
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:qsTr('Teleprompter');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:18;font.weight:Font.DemiBold}
   ShelfButton{flat:true;icon:'notch/edit-3.svg';accessibleLabel:qsTr('Edit script');visible:root.reading;onClicked:{root.playing=false;root.reading=false}}
   ShelfButton{text:root.reading ? root.playing ? qsTr('Pause'):qsTr('Play'):qsTr('Read');selected:true;enabled:editor.text.trim().length>0;onClicked:{if(!root.reading){root.reading=true;scroller.contentY=0}root.playing=!root.playing}}
  }
  ScrollView{visible:!root.reading;Layout.fillWidth:true;Layout.fillHeight:true
   TextArea{id:editor;objectName:'teleprompter-script';text:ShelfState.utilityPreferences.teleprompterText || '';placeholderText:qsTr('Paste your script…');wrapMode:TextEdit.Wrap;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:16;selectByMouse:true;background:Rectangle{radius:14;color:'#151518'} onTextChanged:save.restart()}
  }
  Flickable{id:scroller;visible:root.reading;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;contentWidth:width;contentHeight:script.height+height;boundsBehavior:Flickable.StopAtBounds
   Text{id:script;width:scroller.width;text:editor.text;textFormat:Text.PlainText;wrapMode:Text.Wrap;horizontalAlignment:Text.AlignHCenter;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:root.fontSize;lineHeight:1.45;topPadding:16;transform:Scale{origin.x:script.width/2;xScale:root.mirrored ? -1:1}}
  }
  RowLayout{Layout.fillWidth:true
   Text{text:qsTr('Speed');color:'#aaaab3';font.family:ShelfStyle.textFamily;font.pixelSize:11}
   ShelfSlider{Layout.fillWidth:true;from:8;to:100;value:root.pixelsPerSecond;onMoved:root.pixelsPerSecond=value}
   ShelfButton{flat:true;text:'A−';accessibleLabel:qsTr('Smaller text');onClicked:root.fontSize=Math.max(14,root.fontSize-2)}
   ShelfButton{flat:true;text:'A+';accessibleLabel:qsTr('Larger text');onClicked:root.fontSize=Math.min(48,root.fontSize+2)}
   ShelfButton{flat:true;text:qsTr('Mirror');selected:root.mirrored;onClicked:root.mirrored=!root.mirrored}
  }
 }
 Timer{id:save;interval:600;onTriggered:ShelfState.send({action:'utilityPreferences',values:{teleprompterText:editor.text}})}
 Component.onDestruction:{if(held)ShelfState.interaction(false);if(save.running)ShelfState.send({action:'utilityPreferences',values:{teleprompterText:editor.text}})}
}
