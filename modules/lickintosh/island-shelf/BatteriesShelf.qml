import QtQuick
import QtQuick.Shapes
import QtQuick.Layouts
import QtQuick.Controls.Basic
import Quickshell
import Quickshell.Io
import qs.services
Item{
 id:root;objectName:'shelf-batteries'
 property var devices:[]
 property var reviewDevices:null
 readonly property var shown:reviewDevices || devices
 property string error:''
 function refresh(){if(!worker.running)worker.running=true}
 Process{id:worker;command:[ShelfState.pythonExecutable,Quickshell.shellPath('island-shelf/battery_backend.py')]
  stdout:StdioCollector{onStreamFinished:{try{root.devices=JSON.parse(text).devices;root.error=''}catch(_){root.error=qsTr('Battery information unavailable')}}}
 }
 Timer{interval:30000;repeat:true;running:root.visible && root.reviewDevices===null;onTriggered:root.refresh()}
 onVisibleChanged:if(visible && reviewDevices===null)refresh()
 Component.onCompleted:if(visible && reviewDevices===null)refresh()
 ColumnLayout{anchors.fill:parent;spacing:10
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:qsTr('Batteries');font.family:ShelfStyle.displayFamily;font.pixelSize:18;font.weight:Font.DemiBold;color:ShelfStyle.primary}
   ShelfButton{flat:true;icon:'notch/refresh-cw.svg';accessibleLabel:qsTr('Refresh batteries');enabled:!worker.running;onClicked:root.refresh()}
  }
  Flickable{Layout.fillWidth:true;Layout.fillHeight:true;clip:true;contentWidth:Math.max(width,rings.implicitWidth);contentHeight:height;boundsBehavior:Flickable.StopAtBounds
   RowLayout{id:rings;anchors.verticalCenter:parent.verticalCenter;x:Math.max(0,(parent.width-implicitWidth)/2);spacing:22
    Repeater{model:root.shown
     ColumnLayout{required property var modelData;Layout.preferredWidth:112;spacing:8;opacity:modelData.connected===false ? .4:1
      Item{id:ringVisual;Layout.alignment:Qt.AlignHCenter;width:96;height:96
       readonly property real chargeAngle:360*modelData.percent/100
       readonly property bool charging:!!modelData.charging
       readonly property color level:modelData.percent<=15 ? '#ff453a':modelData.percent<=30 ? '#ff9f0a':'#30d158'
       Shape{anchors.fill:parent;preferredRendererType:Shape.CurveRenderer
        ShapePath{fillColor:'transparent';strokeColor:'#29292b';strokeWidth:9;capStyle:ShapePath.RoundCap;PathAngleArc{centerX:48;centerY:48;radiusX:42;radiusY:42;startAngle:ringVisual.charging ? 67:-90;sweepAngle:ringVisual.charging ? 316:360}}
        ShapePath{fillColor:'transparent';strokeColor:modelData.percent>0 ? ringVisual.level:"transparent";strokeWidth:9;capStyle:ShapePath.RoundCap;PathAngleArc{centerX:48;centerY:48;radiusX:42;radiusY:42;startAngle:-90;sweepAngle:Math.max(.01,ringVisual.charging ? Math.min(113,ringVisual.chargeAngle):ringVisual.chargeAngle)}}
        ShapePath{fillColor:'transparent';strokeColor:ringVisual.charging && ringVisual.chargeAngle>157 ? ringVisual.level:'transparent';strokeWidth:9;capStyle:ShapePath.RoundCap;PathAngleArc{centerX:48;centerY:48;radiusX:42;radiusY:42;startAngle:67;sweepAngle:Math.max(.01,ringVisual.chargeAngle-157)}}
       }
       ShelfIcon{anchors.centerIn:parent;size:38;icon:modelData.kind==='laptop' ? 'laptop.png':modelData.kind==='phone' ? 'notch/smartphone.svg':modelData.kind==='headphones' ? 'notch/headphones.svg':'notch/battery.svg'}
       ShelfIcon{visible:ringVisual.charging;x:48+42*Math.SQRT1_2-width/2;y:48+42*Math.SQRT1_2-height/2;icon:'notch/zap.svg';size:20;color:'#ffd60a'}
      }
      Text{Layout.fillWidth:true;text:modelData.percent+'%';horizontalAlignment:Text.AlignHCenter;font.family:ShelfStyle.displayFamily;font.pixelSize:24;font.weight:Font.Bold;font.features:({tnum:1});color:ShelfStyle.primary}
      Text{Layout.fillWidth:true;text:modelData.name;textFormat:Text.PlainText;elide:Text.ElideRight;horizontalAlignment:Text.AlignHCenter;font.family:ShelfStyle.textFamily;font.pixelSize:16;font.weight:Font.Medium;color:'#d1d1d6'}
     }
    }
   }
  }
  Text{Layout.fillWidth:true;visible:!root.shown.length;text:root.error || qsTr('No battery devices available');horizontalAlignment:Text.AlignHCenter;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:13}
 }
}
