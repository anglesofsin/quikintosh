import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.services
import qs.rosa.services
FloatingWindow {
 id:root;title:'Quickintosh Transform';visible:ShelfState.transformOpen && !IslandBus.locked;color:'transparent'
 implicitWidth:414;implicitHeight:680;minimumSize:Qt.size(380,580)
 property string operation:ShelfState.transformOperation
 property int quality:72
 property int largestSide:0
 property string format:'automatic'
 property bool stripMetadata:true
 property string destination:'downloads'
 readonly property var operations:[{key:'compress',label:qsTr('Compress'),icon:'minimize-2'},{key:'convert',label:qsTr('Convert'),icon:'refresh-cw'},{key:'resize',label:qsTr('Resize'),icon:'maximize-2'},{key:'rotate',label:qsTr('Rotate'),icon:'rotate-cw'},{key:'metadata',label:qsTr('Remove metadata'),icon:'eye-off'},{key:'pdf',label:qsTr('Combine into PDF'),icon:'file-text'},{key:'zip',label:qsTr('ZIP'),icon:'package'}]
 readonly property var entries:ShelfState.items.filter(item=>ShelfState.transformPaths.includes(item.path))
 property int placementAttempts:0
 onVisibleChanged:{if(visible){operation=ShelfState.transformOperation;placementAttempts=0;sizeSoon.restart()}else sizeSoon.stop()}
 Timer{id:sizeSoon;interval:100;repeat:true;onTriggered:{if(!root.visible || ++root.placementAttempts>20){stop();return}if(!placement.running)placement.running=true}}
 Process{id:placement;command:['hyprctl','eval','for _,w in ipairs(hl.get_windows()) do if w.title=="Quickintosh Transform" then if not w.floating then hl.dispatch(hl.dsp.window.float({action="enable",window="address:"..w.address})) end;hl.dispatch(hl.dsp.window.resize({x=414,y=680,window="address:"..w.address}));print("qi-transform-placed") end end'];stdout:SplitParser{onRead:data=>{if(data.includes('qi-transform-placed'))sizeSoon.stop()}}}
 Rectangle{anchors.fill:parent;radius:28;color:'#fa080809';border.color:ShelfStyle.outline
  Flickable{id:scroll;anchors.fill:parent;anchors.margins:18;anchors.bottomMargin:72;contentHeight:formContent.implicitHeight;clip:true;boundsBehavior:Flickable.StopAtBounds
   ScrollBar.vertical:ScrollBar{policy:ScrollBar.AsNeeded}
   ColumnLayout{id:formContent;width:scroll.width;spacing:16
   RowLayout{Layout.fillWidth:true
    ShelfIcon{size:24;icon:'notch/copy.svg'}
    ColumnLayout{Layout.fillWidth:true;spacing:2
     Text{text:qsTr('Transform');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:17;font.weight:Font.DemiBold}
     Text{Layout.fillWidth:true;text:root.entries.length===1 ? root.entries[0].name:qsTr('%1 files').arg(root.entries.length);elide:Text.ElideRight;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:11}
    }
    ShelfButton{icon:'notch/x.svg';onClicked:ShelfState.transformOpen=false}
   }
   ListView{Layout.fillWidth:true;Layout.preferredHeight:92;orientation:ListView.Horizontal;spacing:10;clip:true;model:root.entries
    delegate:Column{required property var modelData;width:80;spacing:4
     Image{width:76;height:60;source:modelData.preview || IconResolver.forFile(modelData.path);fillMode:Image.PreserveAspectFit;sourceSize:Qt.size(152,120);asynchronous:true}
     Text{width:80;text:modelData.name;elide:Text.ElideMiddle;font.family:ShelfStyle.textFamily;font.pixelSize:10;color:'white'}
    }
   }
   GridLayout{Layout.fillWidth:true;columns:4;rowSpacing:10;columnSpacing:8
    Repeater{model:root.operations
     delegate:ColumnLayout{required property var modelData;Layout.fillWidth:true;Layout.minimumWidth:0;Layout.preferredWidth:1;spacing:5
      ShelfButton{Layout.fillWidth:true;Layout.minimumWidth:0;implicitHeight:40;icon:'notch/'+modelData.icon+'.svg';selected:root.operation===modelData.key;onClicked:root.operation=modelData.key}
      Text{Layout.fillWidth:true;Layout.minimumWidth:0;text:modelData.label;color:ShelfStyle.primary;font.family:ShelfStyle.textFamily;font.pixelSize:10;horizontalAlignment:Text.AlignHCenter;wrapMode:Text.WordWrap}
     }
    }
   }
   Rectangle{Layout.fillWidth:true;implicitHeight:form.implicitHeight+24;radius:16;color:'#14ffffff'
    ColumnLayout{id:form;anchors.fill:parent;anchors.margins:12;spacing:12
     RowLayout{Layout.fillWidth:true;visible:!['pdf','zip'].includes(root.operation)
      Text{Layout.fillWidth:true;text:qsTr('Image quality');font.family:ShelfStyle.textFamily;font.pixelSize:12;color:'white'}
      ShelfSlider{Layout.preferredWidth:110;from:1;to:100;stepSize:1;value:root.quality;onMoved:root.quality=value}
      Text{text:root.quality+'%';color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:11}
     }
     RowLayout{Layout.fillWidth:true;visible:!['pdf','zip'].includes(root.operation)
      Text{Layout.fillWidth:true;text:qsTr('Image format');font.family:ShelfStyle.textFamily;font.pixelSize:12;color:'white'}
      ShelfChoice{Layout.preferredWidth:140;model:[qsTr('Automatic'),'PNG','JPEG','WebP'];currentIndex:['automatic','png','jpeg','webp'].indexOf(root.format);onActivated:i=>root.format=['automatic','png','jpeg','webp'][i]}
     }
     RowLayout{Layout.fillWidth:true;visible:!['pdf','zip'].includes(root.operation)
      Text{Layout.fillWidth:true;text:qsTr('Largest side');font.family:ShelfStyle.textFamily;font.pixelSize:12;color:'white'}
      ShelfChoice{Layout.preferredWidth:140;model:[qsTr('Keep'),'640 px','1280 px','1920 px','2560 px','3840 px'];currentIndex:[0,640,1280,1920,2560,3840].indexOf(root.largestSide);onActivated:i=>root.largestSide=[0,640,1280,1920,2560,3840][i]}
     }
     RowLayout{Layout.fillWidth:true;visible:!['pdf','zip'].includes(root.operation)
      Text{Layout.fillWidth:true;text:qsTr('Remove metadata');font.family:ShelfStyle.textFamily;font.pixelSize:12;color:'white'}
      Switch{checked:root.stripMetadata;onToggled:root.stripMetadata=checked}
     }
     RowLayout{Layout.fillWidth:true
      Text{Layout.fillWidth:true;text:qsTr('Save to');font.family:ShelfStyle.textFamily;font.pixelSize:12;color:'white'}
      ShelfChoice{Layout.preferredWidth:140;model:[qsTr('Downloads'),qsTr('Next to original')];currentIndex:root.destination==='beside' ? 1:0;onActivated:i=>root.destination=i ? 'beside':'downloads'}
     }
    }
   }
   Text{Layout.fillWidth:true;text:ShelfState.notice || qsTr('Originals stay unchanged. Results are added to Files.');wrapMode:Text.WordWrap;color:ShelfState.notice ? '#ff9f8f':ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:11}
   RowLayout{Layout.fillWidth:true
    ShelfButton{Layout.fillWidth:true;text:qsTr('Web ready');onClicked:{root.quality=72;root.largestSide=1920;root.format='webp'}}
    ShelfButton{Layout.fillWidth:true;text:qsTr('Full resolution');onClicked:{root.quality=92;root.largestSide=0;root.format='automatic'}}
   }
   }
  }
   ShelfButton{anchors.left:parent.left;anchors.right:parent.right;anchors.bottom:parent.bottom;anchors.margins:18;implicitHeight:38;selected:true;text:ShelfState.busy ? qsTr('Processing…'):root.operations.find(item=>item.key===root.operation)?.label || qsTr('Transform');enabled:root.entries.length>0 && !ShelfState.busy
    onClicked:ShelfState.send({action:'transform',paths:ShelfState.transformPaths,operation:root.operation,format:root.format,quality:root.quality,side:root.largestSide,stripMetadata:root.stripMetadata,destination:root.destination})
   }
 }
 Shortcut{sequence:'Escape';onActivated:ShelfState.transformOpen=false}
}
