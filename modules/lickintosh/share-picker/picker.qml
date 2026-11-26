import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
ShellRoot {
 id:root
 property var data:({groups:[[],[],[]],remember:false})
 property int tab:0
 property var chosen:null
 property bool remember:false
 readonly property var items:data.groups[Math.min(tab,2)] || []
 function tr(en,pt){return data.portuguese ? pt:en}
 function selected(item){return chosen && chosen.kind===item.kind && chosen.key===item.key}
 function finish(item){if(!item)return;writer.command=['python3','-c','import json,sys;from pathlib import Path;Path(sys.argv[1]).write_text(sys.argv[2])',Quickshell.env('QI_SHARE_RESPONSE'),JSON.stringify({kind:item.kind,key:item.key,remember:root.remember})];writer.running=true}
 function windowSource(item){
  const list=Hyprland.toplevels.values
  for(const w of list)if(String(w.address).toLowerCase().replace(/^0x/,'')===String(item.address || '').toLowerCase().replace(/^0x/,''))return w.wayland
  const matches=ToplevelManager.toplevels.values.filter(w=>w.appId===item.app && w.title===item.title)
  return matches.length===1 ? matches[0]:null
 }
 function icon(item){const entry=DesktopEntries.heuristicLookup(item.app || '');return entry && entry.icon ? Quickshell.iconPath(entry.icon):''}
 function changeTab(index){tab=index;chosen=items.length===1 ? items[0]:null;grid.currentIndex=chosen ? 0:-1}
 FileView{path:Quickshell.env('QI_SHARE_DATA');onLoaded:{root.data=JSON.parse(text());root.remember=root.data.remember;root.changeTab(0)}}
 Process{id:writer;onExited:Qt.quit()}
 Process{id:region;command:['slurp','-f','%x,%y,%w,%h'];stdout:StdioCollector{id:area}
 onExited:code=>{if(code===0 && area.text.trim())root.finish({kind:'region',key:area.text.trim()});else win.visible=true}}
 FloatingWindow {
  id:win;title:'Quickintosh Screen Sharing';color:'transparent';visible:true
  implicitWidth:740;implicitHeight:600;minimumSize:Qt.size(600,500)
  Rectangle {
   anchors.fill:parent;radius:24;color:'#b5242426';border.width:1;border.color:'#50ffffff'
   focus:true;Keys.onEscapePressed:Qt.quit()
   Keys.onReturnPressed:root.finish(root.chosen)
   ColumnLayout {
    anchors.fill:parent;anchors.margins:24;spacing:18
    RowLayout{spacing:14;Layout.fillWidth:true
     Rectangle{Layout.preferredWidth:44;Layout.preferredHeight:44;radius:14;color:'#805bd6'
      Image{anchors.centerIn:parent;width:26;height:26;source:'display.svg';sourceSize:Qt.size(78,78)}
     }
     ColumnLayout{spacing:4;Layout.fillWidth:true
      Text{Layout.fillWidth:true;text:root.tr('Choose what to share','Escolha o que compartilhar');font.family:'SF Pro Display';font.pixelSize:22;font.weight:Font.DemiBold;color:'white';elide:Text.ElideRight}
      Text{Layout.fillWidth:true;text:root.tr('Only the selected source will be shared.','Somente a fonte selecionada será compartilhada.');font.family:'SF Pro Text';font.pixelSize:13;color:'#bfffffff';elide:Text.ElideRight}
     }
    }
    Rectangle{Layout.fillWidth:true;implicitHeight:36;radius:11;color:'#30000000'
     RowLayout{anchors.fill:parent;anchors.margins:3;spacing:3
      Repeater{model:[root.tr('Display','Tela'),root.tr('Window','Janela'),root.tr('Space','Mesa'),root.tr('Region','Região')]
       delegate:Rectangle{required property int index;required property string modelData;Layout.fillWidth:true;Layout.fillHeight:true;radius:8;color:root.tab===index ? '#38ffffff':'transparent'
        Text{anchors.centerIn:parent;text:parent.modelData;font.family:'SF Pro Text';font.pixelSize:13;font.weight:root.tab===parent.index ? Font.DemiBold:Font.Normal;color:'white'}
        MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:root.changeTab(parent.index)}
       }
      }
     }
    }
    Item{Layout.fillWidth:true;Layout.fillHeight:true
     GridView{
      id:grid;anchors.fill:parent;visible:root.tab<3;clip:true;model:root.items
      readonly property bool single:count===1
      cellWidth:single ? width:width/2;cellHeight:single ? Math.min(height,308):218
      boundsBehavior:Flickable.StopAtBounds;keyNavigationEnabled:true;focus:true
      ScrollBar.vertical:ScrollBar{policy:ScrollBar.AsNeeded}
      onCurrentIndexChanged:if(currentIndex>=0 && currentIndex<count)root.chosen=root.items[currentIndex]
      delegate:Item{
       required property var modelData;required property int index
       width:grid.cellWidth;height:grid.cellHeight
       Rectangle{
        id:card;anchors.fill:parent;anchors.rightMargin:grid.single ? 0:6;anchors.leftMargin:grid.single ? 0:6;anchors.bottomMargin:12
        radius:16;color:root.selected(modelData) ? '#205f4b95':'#18000000';border.width:root.selected(modelData) ? 2:1;border.color:root.selected(modelData) ? '#ae8cf4':'#25ffffff'
        ColumnLayout{anchors.fill:parent;anchors.margins:12;spacing:8
         Rectangle{Layout.fillWidth:true;Layout.fillHeight:true;Layout.minimumHeight:80;radius:10;color:'#24000000';clip:true
          Image{anchors.fill:parent;source:modelData.preview || '';fillMode:Image.PreserveAspectFit;asynchronous:true;sourceSize:Qt.size(900,520)}
          ScreencopyView{
           id:windowPreview;anchors.fill:parent;visible:root.tab===1 && hasContent
           captureSource:root.tab===1 ? root.windowSource(modelData):null
           live:false
          }
          Column{anchors.centerIn:parent;spacing:10;visible:!modelData.preview && !windowPreview.hasContent
           Image{anchors.horizontalCenter:parent.horizontalCenter;width:40;height:40;source:root.tab===1 ? root.icon(modelData):'display.svg';sourceSize:Qt.size(120,120);fillMode:Image.PreserveAspectFit}
           Text{anchors.horizontalCenter:parent.horizontalCenter;text:root.tab===2 ? root.tr('Workspace','Mesa')+' '+modelData.title:root.tr('Window','Janela');font.family:'SF Pro Text';font.pixelSize:12;color:'#90ffffff'}
          }
         }
         Text{Layout.fillWidth:true;Layout.preferredHeight:18;text:modelData.title;color:'white';font.family:'SF Pro Text';font.pixelSize:13;font.weight:Font.DemiBold;horizontalAlignment:Text.AlignHCenter;elide:Text.ElideRight}
         Text{Layout.fillWidth:true;Layout.preferredHeight:14;text:modelData.subtitle || '';visible:!!text;color:'#aaffffff';font.family:'SF Pro Text';font.pixelSize:11;horizontalAlignment:Text.AlignHCenter;elide:Text.ElideRight}
        }
        MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:{grid.currentIndex=index;root.chosen=modelData}
        onDoubleClicked:root.finish(modelData)}
       }
      }
     }
     Column{anchors.centerIn:parent;spacing:12;visible:root.tab<3 && root.items.length===0
      Image{anchors.horizontalCenter:parent.horizontalCenter;width:44;height:44;source:'display.svg';opacity:.6}
      Text{anchors.horizontalCenter:parent.horizontalCenter;text:root.tab===1 ? root.tr('No windows available','Nenhuma janela disponível'):root.tr('No workspaces available','Nenhuma mesa disponível');color:'white';font.family:'SF Pro Display';font.pixelSize:17}
     }
     Column{anchors.centerIn:parent;spacing:18;visible:root.tab===3
      Image{anchors.horizontalCenter:parent.horizontalCenter;width:64;height:64;source:'display.svg';opacity:.75}
      Text{anchors.horizontalCenter:parent.horizontalCenter;text:root.tr('Select an area of your screen','Selecione uma área da tela');font.family:'SF Pro Display';font.pixelSize:19;color:'white'}
      PickerButton{anchors.horizontalCenter:parent.horizontalCenter;text:root.tr('Choose Region…','Escolher região…');accent:true;onClicked:{win.visible=false;region.running=true}}
     }
    }
    Rectangle{Layout.fillWidth:true;implicitHeight:1;color:'#16ffffff'}
    RowLayout{Layout.fillWidth:true;spacing:10
     RowLayout{spacing:9
      Rectangle{implicitWidth:18;implicitHeight:18;radius:5;color:root.remember ? '#9871e1':'#18ffffff';border.color:'#50ffffff'
       Text{anchors.centerIn:parent;text:root.remember ? '✓':'';color:'white';font.family:'SF Pro Text';font.pixelSize:13;font.weight:Font.DemiBold}
      }
      Text{text:root.tr('Remember selection','Lembrar seleção');font.family:'SF Pro Text';font.pixelSize:12;color:'#cfffffff'}
      TapHandler{onTapped:root.remember=!root.remember}
     }
     Item{Layout.fillWidth:true}
     PickerButton{text:root.tr('Cancel','Cancelar');onClicked:Qt.quit()}
     PickerButton{text:root.tr('Share','Compartilhar');accent:true;enabled:!!root.chosen && root.tab<3;onClicked:root.finish(root.chosen)}
    }
   }
  }
 }
 component PickerButton:Rectangle{
  id:button;property string text:'';property bool accent:false;signal clicked()
  implicitWidth:Math.max(84,caption.implicitWidth+32);implicitHeight:34;radius:10
  opacity:enabled ? 1:.4;color:accent ? '#9366df':mouse.pressed ? '#40ffffff':'#25ffffff'
  Text{id:caption;anchors.centerIn:parent;text:button.text;font.family:'SF Pro Text';font.pixelSize:13;font.weight:Font.Medium;color:'white'}
  MouseArea{id:mouse;anchors.fill:parent;enabled:button.enabled;cursorShape:Qt.PointingHandCursor;onClicked:button.clicked()}
 }
}
