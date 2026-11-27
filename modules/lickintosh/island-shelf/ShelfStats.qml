import QtQuick
import QtQuick.Layouts
import QtQuick.Shapes
import Quickshell
import qs.services
import qs.ui.topbar.notch.dashboard
Item{
 id:root
 objectName:'shelf-stats'
 property bool held:false
 readonly property bool watching:visible && !!QsWindow.window && QsWindow.window.visible
 function syncWatch(){if(held!==watching){held=watching;ResourcesState.watch(held)}}
 onWatchingChanged:syncWatch()
 Component.onCompleted:syncWatch()
 Component.onDestruction:if(held)ResourcesState.watch(false)
 RowLayout{anchors.fill:parent;spacing:24
  Repeater{model:[{title:qsTr('CPU'),value:ResourcesState.cpuPercent,values:ResourcesState.cpuHistory,color:'#9d9aff',icon:'notch/cpu.svg',detail:ResourcesState.cpuTempAvailable ? Math.round(ResourcesState.cpuTempC)+'°C':''},{title:qsTr('RAM'),value:ResourcesState.memoryPercent,values:ResourcesState.memoryHistory,color:'#8ce5c5',icon:'notch/server.svg',detail:ResourcesState.memoryUsedGb.toFixed(1)+' / '+ResourcesState.memoryTotalGb.toFixed(1)+' GB'}]
   delegate:ColumnLayout{required property var modelData;Layout.fillWidth:true;Layout.fillHeight:true;spacing:12
    RowLayout{Layout.fillWidth:true;spacing:10
     Item{Layout.preferredWidth:54;Layout.preferredHeight:54
      Shape{anchors.fill:parent;preferredRendererType:Shape.CurveRenderer
       ShapePath{strokeWidth:5;strokeColor:'#303038';fillColor:'transparent';PathAngleArc{centerX:27;centerY:27;radiusX:24;radiusY:24;startAngle:-90;sweepAngle:360}}
       ShapePath{strokeWidth:5;strokeColor:modelData.color;capStyle:ShapePath.RoundCap;fillColor:'transparent';PathAngleArc{centerX:27;centerY:27;radiusX:24;radiusY:24;startAngle:-90;sweepAngle:Math.max(0,Math.min(100,modelData.value))*3.6}}
      }
      ShelfIcon{anchors.centerIn:parent;size:20;icon:modelData.icon;color:modelData.color}
     }
     ColumnLayout{Layout.fillWidth:true;spacing:2
      Text{text:modelData.title;font.family:ShelfStyle.textFamily;font.pixelSize:13;font.weight:Font.DemiBold;color:modelData.color}
      Text{text:Math.round(modelData.value)+'%';font.family:ShelfStyle.displayFamily;font.pixelSize:24;font.weight:Font.DemiBold;color:ShelfStyle.primary}
     }
    }
    Item{Layout.fillHeight:true}
    Sparkline{Layout.fillWidth:true;Layout.preferredHeight:48;values:modelData.values;lineColor:modelData.color;backgroundColor:'transparent'}
    Text{Layout.fillWidth:true;text:modelData.detail;font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.caption;color:ShelfStyle.secondary;elide:Text.ElideRight}
   }
  }
 }
}
