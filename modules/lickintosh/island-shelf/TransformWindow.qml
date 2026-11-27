import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Dialogs
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
 property string renamePattern:'{name}-{index}{ext}'
 property string backgroundModel:'u2netp'
 property string selectedPreset:''
 function addInputs(urls){const paths=Array.from(urls).map(u=>decodeURIComponent(String(u).replace(/^file:\/\//,'')));ShelfState.add(urls);ShelfState.transformPaths=Array.from(new Set(ShelfState.transformPaths.concat(paths)))}
 property int targetBytes:0
 property int fps:0
 property string pageRange:''
 readonly property bool video:entries.some(e=>String(e.mime).startsWith('video/'))
 readonly property bool pdf:entries.length>0 && entries.every(e=>e.mime==='application/pdf')
 readonly property var formats:video ? ['automatic','mp4','webm','mkv','gif']:['automatic','png','jpeg','webp']
 function settings(){return {backgroundModel:backgroundModel,targetBytes:targetBytes,operation:operation,format:format,quality:quality,side:largestSide,fps:fps,pages:pageRange,stripMetadata:stripMetadata,destination:destination}}
 function applyPreset(p){selectedPreset=p.name;const s=p.settings;backgroundModel=s.backgroundModel || 'u2netp';targetBytes=s.targetBytes || 0;operation=s.operation || 'compress';format=s.format || 'automatic';quality=s.quality || 72;largestSide=s.side || 0;fps=s.fps || 0;stripMetadata=s.stripMetadata!==false;destination=s.destination || 'downloads'}

 readonly property var operations:[{key:'compress',label:qsTr('Compress'),icon:'minimize-2'},{key:'convert',label:qsTr('Convert'),icon:'refresh-cw'},{key:'resize',label:qsTr('Resize'),icon:'maximize-2'},{key:'rotate',label:qsTr('Rotate'),icon:'rotate-cw'},{key:'metadata',label:qsTr('Remove metadata'),icon:'eye-off'},{key:'pdf',label:qsTr('Combine into PDF'),icon:'file-text'},{key:'zip',label:qsTr('ZIP'),icon:'package'},{key:'background',label:qsTr('Remove background'),icon:'background'},{key:'split',label:qsTr('Extract pages'),icon:'copy'},{key:'rename',label:qsTr('Rename'),icon:'type'}]
 readonly property var entries:ShelfState.items.filter(item=>ShelfState.transformPaths.includes(item.path))
 property int placementAttempts:0
 onVisibleChanged:{if(visible){operation=ShelfState.transformOperation;placementAttempts=0;sizeSoon.restart();ShelfState.send({action:'presets'})}else sizeSoon.stop()}
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
   ShelfButton{text:qsTr('Add files…');icon:'notch/plus.svg';onClicked:inputFiles.open()}
   ListView{Layout.fillWidth:true;Layout.preferredHeight:92;orientation:ListView.Horizontal;spacing:10;clip:true;model:root.entries
    delegate:Column{required property var modelData;width:80;spacing:4
     Image{width:76;height:60;source:ShelfState.filePreviews[modelData.path] || modelData.preview || IconResolver.forFile(modelData.path);fillMode:Image.PreserveAspectFit;sourceSize:Qt.size(152,120);asynchronous:true}
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
     TextField{Layout.fillWidth:true;visible:root.operation==='rename';text:root.renamePattern;placeholderText:'{name}-{index}{ext}';onTextChanged:root.renamePattern=text;color:'white';font.family:ShelfStyle.textFamily;background:Rectangle{radius:9;color:'#18ffffff'}}
     Text{Layout.fillWidth:true;visible:root.operation==='rename';text:qsTr('Use {name}, {index} and {ext}. Existing files are never overwritten.');wrapMode:Text.WordWrap;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:11}
     RowLayout{Layout.fillWidth:true;visible:root.operation==='background'
      Text{Layout.fillWidth:true;text:qsTr('Background removal');color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:12}
      ShelfChoice{Layout.preferredWidth:140;model:[qsTr('Fast · local'),qsTr('Detailed · local')];currentIndex:root.backgroundModel==='u2netp' ? 0:1;onActivated:i=>root.backgroundModel=i ? 'u2net':'u2netp'}
     }
     Text{Layout.fillWidth:true;visible:root.operation==='background';text:qsTr('Processed on this computer. The detailed model downloads once on first use.');wrapMode:Text.WordWrap;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:11}
     RowLayout{Layout.fillWidth:true;visible:root.operation==='compress' && !root.pdf
      ShelfButton{Layout.fillWidth:true;text:qsTr('Quality');selected:root.targetBytes===0;onClicked:root.targetBytes=0}
      ShelfButton{Layout.fillWidth:true;text:qsTr('File size');selected:root.targetBytes>0;onClicked:root.targetBytes=10*1024*1024}
     }
     RowLayout{Layout.fillWidth:true;visible:root.targetBytes>0 && root.operation==='compress'
      Text{Layout.fillWidth:true;text:qsTr('Maximum size');color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:12}
      ShelfChoice{Layout.preferredWidth:140;model:['1 MB','5 MB','10 MB','25 MB'];currentIndex:[1048576,5242880,10485760,26214400].indexOf(root.targetBytes);onActivated:i=>root.targetBytes=[1048576,5242880,10485760,26214400][i]}
     }
     RowLayout{Layout.fillWidth:true;visible:!['pdf','zip','background','split','rename'].includes(root.operation)
      Text{Layout.fillWidth:true;text:root.video ? qsTr('Video quality'):qsTr('Image quality');font.family:ShelfStyle.textFamily;font.pixelSize:12;color:'white'}
      ShelfSlider{Layout.preferredWidth:110;from:1;to:100;stepSize:1;value:root.quality;onMoved:root.quality=value}
      Text{text:root.quality+'%';color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:11}
     }
     RowLayout{Layout.fillWidth:true;visible:!['pdf','zip','background','split','rename'].includes(root.operation)
      Text{Layout.fillWidth:true;text:root.video ? qsTr('Video format'):qsTr('Image format');font.family:ShelfStyle.textFamily;font.pixelSize:12;color:'white'}
      ShelfChoice{Layout.preferredWidth:140;model:root.formats.map(f=>f==='automatic' ? qsTr('Automatic'):f.toUpperCase());currentIndex:Math.max(0,root.formats.indexOf(root.format));onActivated:i=>root.format=root.formats[i]}
     }
     RowLayout{Layout.fillWidth:true;visible:!['pdf','zip','background','split','rename'].includes(root.operation)
      Text{Layout.fillWidth:true;text:qsTr('Largest side');font.family:ShelfStyle.textFamily;font.pixelSize:12;color:'white'}
      ShelfChoice{Layout.preferredWidth:140;model:[qsTr('Keep'),'640 px','1280 px','1920 px','2560 px','3840 px'];currentIndex:[0,640,1280,1920,2560,3840].indexOf(root.largestSide);onActivated:i=>root.largestSide=[0,640,1280,1920,2560,3840][i]}
     }
     RowLayout{Layout.fillWidth:true;visible:!['pdf','zip','background','split','rename'].includes(root.operation)
      Text{Layout.fillWidth:true;text:qsTr('Remove metadata');font.family:ShelfStyle.textFamily;font.pixelSize:12;color:'white'}
      Switch{checked:root.stripMetadata;onToggled:root.stripMetadata=checked}
     }
     RowLayout{Layout.fillWidth:true;visible:root.video
      Text{Layout.fillWidth:true;text:qsTr('Frame rate');font.family:ShelfStyle.textFamily;font.pixelSize:12;color:'white'}
      ShelfChoice{Layout.preferredWidth:140;model:[qsTr('Original'),'24 fps','30 fps','60 fps'];currentIndex:[0,24,30,60].indexOf(root.fps);onActivated:i=>root.fps=[0,24,30,60][i]}
     }
     RowLayout{Layout.fillWidth:true;visible:root.pdf && ['split','convert'].includes(root.operation)
      Text{Layout.fillWidth:true;text:qsTr('Pages');font.family:ShelfStyle.textFamily;font.pixelSize:12;color:'white'}
      TextField{Layout.preferredWidth:140;text:root.pageRange;placeholderText:qsTr('All · e.g. 1–3,5');onTextChanged:root.pageRange=text;color:'white';font.family:ShelfStyle.textFamily;background:Rectangle{radius:9;color:'#18ffffff'}}
     }
     RowLayout{Layout.fillWidth:true
      Text{Layout.fillWidth:true;text:qsTr('Save to');font.family:ShelfStyle.textFamily;font.pixelSize:12;color:'white'}
      ShelfChoice{Layout.preferredWidth:140;model:[qsTr('Downloads'),qsTr('Next to original')];currentIndex:root.destination==='beside' ? 1:0;onActivated:i=>root.destination=i ? 'beside':'downloads'}
     }
    }
   }
   Text{Layout.fillWidth:true;text:ShelfState.notice || qsTr('Originals stay unchanged. Results are added to Files.');wrapMode:Text.WordWrap;color:ShelfState.notice ? '#ff9f8f':ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:11}
   RowLayout{Layout.fillWidth:true
    ShelfChoice{Layout.fillWidth:true;model:[qsTr('Saved presets')].concat(ShelfState.transformPresets.map(p=>p.name));onActivated:i=>{if(i>0)root.applyPreset(ShelfState.transformPresets[i-1])}}
    ShelfButton{icon:'notch/trash-2.svg';accessibleLabel:qsTr('Remove selected preset');enabled:!!root.selectedPreset;onClicked:{ShelfState.send({action:'removePreset',name:root.selectedPreset});root.selectedPreset=''}}
    ShelfButton{icon:'notch/plus.svg';accessibleLabel:qsTr('Save preset');onClicked:presetName.open()}
   }
   RowLayout{Layout.fillWidth:true
    ShelfButton{Layout.fillWidth:true;text:qsTr('Web ready');onClicked:{root.quality=72;root.largestSide=1920;root.format='webp'}}
    ShelfButton{Layout.fillWidth:true;text:qsTr('Full resolution');onClicked:{root.quality=92;root.largestSide=0;root.format='automatic'}}
   }
   }
  }
   ShelfButton{visible:ShelfState.busy;anchors.right:parent.right;anchors.bottom:parent.bottom;anchors.margins:18;implicitWidth:76;implicitHeight:38;text:qsTr('Cancel');onClicked:ShelfState.cancelTransform()}
   ShelfButton{anchors.left:parent.left;anchors.right:parent.right;anchors.bottom:parent.bottom;anchors.margins:18;anchors.rightMargin:ShelfState.busy ? 104:18;implicitHeight:38;selected:true;text:ShelfState.busy ? qsTr('Processing…'):root.operations.find(item=>item.key===root.operation)?.label || qsTr('Transform');enabled:root.entries.length>0 && !ShelfState.busy
    onClicked:root.operation==='rename' ? ShelfState.send({action:'renameMany',paths:ShelfState.transformPaths,pattern:root.renamePattern}):ShelfState.send(Object.assign({action:'transform',paths:ShelfState.transformPaths},root.settings()))
   }
 }
 FileDialog{id:inputFiles;title:qsTr('Add files to Transform');fileMode:FileDialog.OpenFiles;onAccepted:root.addInputs(selectedFiles)}
 DropArea{anchors.fill:parent;keys:['text/uri-list'];onDropped:drop=>{root.addInputs(drop.urls);drop.acceptProposedAction()}}
 Popup{id:presetName;anchors.centerIn:parent;width:300;padding:16;modal:true
  background:Rectangle{radius:16;color:'#f0222226';border.color:ShelfStyle.outline}
  contentItem:ColumnLayout{spacing:12
   TextField{id:nameInput;Layout.fillWidth:true;placeholderText:qsTr('Preset name');color:'white';font.family:ShelfStyle.textFamily;background:Rectangle{radius:9;color:'#18ffffff'}}
   ShelfButton{text:qsTr('Save preset');enabled:nameInput.text.trim().length>0;onClicked:{ShelfState.send({action:'savePreset',name:nameInput.text,settings:root.settings()});presetName.close()}}
  }
 }
 Shortcut{sequence:'Escape';onActivated:ShelfState.transformOpen=false}
}
