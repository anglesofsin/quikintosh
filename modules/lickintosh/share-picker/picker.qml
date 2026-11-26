import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
ShellRoot {
 id:root
 property var data:({groups:[[],[],[]],remember:false})
 property int tab:0
 property var chosen:null
 property bool remember:data.remember
 function tr(en,pt){return data.portuguese ? pt:en}
 function finish(item){if(!item)return;writer.command=['python3','-c','import json,sys;from pathlib import Path;Path(sys.argv[1]).write_text(sys.argv[2])',Quickshell.env('QI_SHARE_RESPONSE'),JSON.stringify({kind:item.kind,key:item.key,remember:root.remember})];writer.running=true}
 FileView{path:Quickshell.env('QI_SHARE_DATA');onLoaded:root.data=JSON.parse(text())}
 Process{id:writer;onExited:Qt.quit()}
 Process{id:region;command:['slurp','-f','%x,%y,%w,%h'];stdout:StdioCollector{id:area}
 onExited:code=>{if(code===0 && area.text.trim())root.finish({kind:'region',key:area.text.trim()});else win.visible=true}}
 FloatingWindow {
  id:win;title:'Quickintosh Screen Sharing';color:'transparent';visible:true
  implicitWidth:720;implicitHeight:570
  minimumSize:Qt.size(560,460)
  Rectangle {
   anchors.fill:parent;radius:24;color:'#a3232325';border.width:1;border.color:'#40ffffff'
   focus:true;Keys.onEscapePressed:Qt.quit()
   ColumnLayout {
    anchors.fill:parent;anchors.margins:24;spacing:18
    RowLayout{
     spacing:14
     Rectangle{width:42;height:42;radius:13;color:'#805bd6'
      Image{anchors.centerIn:parent;width:25;height:25;source:'display.svg';sourceSize:Qt.size(50,50)}
     }
     ColumnLayout{spacing:4;Layout.fillWidth:true
      Text{text:root.tr('Choose what to share','Escolha o que compartilhar');font.family:'SF Pro Display';font.pixelSize:21;font.weight:Font.DemiBold;color:'white'}
      Text{text:root.tr('Only the selected source will be shared.','Somente a fonte selecionada será compartilhada.');font.family:'SF Pro Text';font.pixelSize:13;color:'#c0ffffff'}
     }
    }
    Rectangle{Layout.fillWidth:true;implicitHeight:36;radius:11;color:'#28000000'
     RowLayout{anchors.fill:parent;anchors.margins:3;spacing:3
      Repeater{model:[root.tr('Display','Tela'),root.tr('Window','Janela'),root.tr('Space','Mesa'),root.tr('Region','Região')]
       delegate:Rectangle{required property int index;required property string modelData;Layout.fillWidth:true;Layout.fillHeight:true;radius:8;color:root.tab===index ? '#38ffffff':'transparent'
        Text{anchors.centerIn:parent;text:parent.modelData;font.family:'SF Pro Text';font.pixelSize:13;font.weight:root.tab===parent.index ? Font.DemiBold:Font.Normal;color:'white'}
        MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:{root.tab=parent.index;root.chosen=null}}
       }
      }
     }
    }
    ScrollView{Layout.fillWidth:true;Layout.fillHeight:true;clip:true;visible:root.tab<3;ScrollBar.horizontal.policy:ScrollBar.AlwaysOff
     GridLayout{width:parent.width;columns:root.tab===0 && root.data.groups[0].length===1 ? 1:2;columnSpacing:12;rowSpacing:12
      Repeater{model:root.data.groups[Math.min(root.tab,2)]
       delegate:Rectangle{
        id:card;required property var modelData;Layout.fillWidth:true;implicitHeight:root.tab===0 && root.data.groups[0].length===1 ? 284:190
        radius:16;color:root.chosen===modelData ? '#285f4b95':'#18000000';border.width:root.chosen===modelData ? 2:1;border.color:root.chosen===modelData ? '#aa87ed':'#20ffffff'
        ColumnLayout{anchors.fill:parent;anchors.margins:12;spacing:8
         Rectangle{Layout.fillWidth:true;Layout.fillHeight:true;radius:10;color:'#20000000';clip:true
          Image{anchors.fill:parent;source:card.modelData.preview;fillMode:Image.PreserveAspectFit;asynchronous:true;sourceSize:Qt.size(760,420)}
          Text{anchors.centerIn:parent;visible:!card.modelData.preview;text:root.tab===2 ? '▦':'▣';color:'#80ffffff';font.pixelSize:44}
         }
         Text{Layout.fillWidth:true;text:card.modelData.title;color:'white';font.family:'SF Pro Text';font.pixelSize:13;font.weight:Font.DemiBold;horizontalAlignment:Text.AlignHCenter;elide:Text.ElideRight}
         Text{Layout.fillWidth:true;text:card.modelData.subtitle || '';visible:!!text;color:'#aaffffff';font.family:'SF Pro Text';font.pixelSize:11;horizontalAlignment:Text.AlignHCenter;elide:Text.ElideRight}
        }
        MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:root.chosen=card.modelData;onDoubleClicked:root.finish(card.modelData)}
       }
      }
     }
    }
    Item{Layout.fillWidth:true;Layout.fillHeight:true;visible:root.tab===3
     Column{anchors.centerIn:parent;spacing:14
      Text{anchors.horizontalCenter:parent.horizontalCenter;text:root.tr('Select an area of your screen','Selecione uma área da tela');font.family:'SF Pro Display';font.pixelSize:19;color:'white'}
      Button{anchors.horizontalCenter:parent.horizontalCenter;text:root.tr('Choose Region…','Escolher região…');onClicked:{win.visible=false;region.running=true}}
     }
    }
    RowLayout{Layout.fillWidth:true;spacing:10
     CheckBox{checked:root.remember;onToggled:root.remember=checked;indicator:Rectangle{implicitWidth:18;implicitHeight:18;radius:5;color:parent.checked ? '#9871e1':'#20ffffff';border.color:'#50ffffff';Text{anchors.centerIn:parent;text:parent.parent.checked ? '✓':'';color:'white';font.pixelSize:13}}}
     Text{Layout.fillWidth:true;text:root.tr('Remember selection','Lembrar seleção');font.family:'SF Pro Text';font.pixelSize:12;color:'#cfffffff'}
     Repeater{model:[root.tr('Cancel','Cancelar'),root.tr('Share','Compartilhar')]
      delegate:Rectangle{required property int index;required property string modelData;implicitWidth:Math.max(82,caption.implicitWidth+28);implicitHeight:32;radius:10;color:index===1 ? '#9366df':'#25ffffff';opacity:index===1 && !root.chosen ? .45:1
       Text{id:caption;anchors.centerIn:parent;text:parent.modelData;font.family:'SF Pro Text';font.pixelSize:13;font.weight:Font.Medium;color:'white'}
       MouseArea{anchors.fill:parent;enabled:parent.index===0 || !!root.chosen;cursorShape:Qt.PointingHandCursor;onClicked:parent.index===0 ? Qt.quit():root.finish(root.chosen)}
      }
     }
    }
   }
  }
 }
}
