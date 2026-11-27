import QtQuick
import QtQuick.Layouts
import qs.services
Item {
 id:root
 property date today:new Date()
 readonly property bool monthView:width>440
 readonly property var upcoming:CalendarState.available ? CalendarState.events.slice(0,2):[]
 function week(){const d=new Date(Date.UTC(today.getFullYear(),today.getMonth(),today.getDate()));d.setUTCDate(d.getUTCDate()+4-(d.getUTCDay() || 7));return Math.ceil(((d-new Date(Date.UTC(d.getUTCFullYear(),0,1)))/86400000+1)/7)}
 Timer{interval:60000;repeat:true;running:root.visible;onTriggered:root.today=new Date()}
 ColumnLayout{anchors.fill:parent;spacing:10
  RowLayout{Layout.fillWidth:true;spacing:5
   Text{text:Qt.formatDate(root.today,'ddd d').toUpperCase();font.family:'SF Pro Text';font.pixelSize:13;font.weight:Font.DemiBold;color:'#ff5d69'}
   Text{text:'W'+root.week();font.family:'SF Pro Text';font.pixelSize:12;font.weight:Font.DemiBold;color:'#89444b'}
   Item{Layout.fillWidth:true}
   Text{visible:root.monthView;text:Qt.formatDate(root.today,'MMMM');font.family:'SF Pro Text';font.pixelSize:13;font.weight:Font.DemiBold;color:'#d0d0d4'}
  }
  ColumnLayout{Layout.fillWidth:true;Layout.fillHeight:true;visible:!root.monthView;spacing:6
   Repeater{model:root.upcoming
    delegate:Rectangle{required property var modelData;required property int index;Layout.fillWidth:true;implicitHeight:49;radius:7;color:index%2===0 ? '#66102d49':'#663b2909'
     Rectangle{anchors.left:parent.left;anchors.top:parent.top;anchors.bottom:parent.bottom;anchors.margins:4;width:3;radius:2;color:index%2===0 ? '#168fff':'#ffb23e'}
     ColumnLayout{anchors.fill:parent;anchors.leftMargin:12;anchors.rightMargin:8;anchors.topMargin:4;anchors.bottomMargin:4;spacing:1
      Text{Layout.fillWidth:true;text:modelData.title;textFormat:Text.PlainText;elide:Text.ElideRight;color:index%2===0 ? '#5dadff':'#ffc16a';font.family:'SF Pro Text';font.pixelSize:14;font.weight:Font.DemiBold}
      Text{text:modelData.time;textFormat:Text.PlainText;color:index%2===0 ? '#418bd5':'#d59c4e';font.family:'SF Pro Text';font.pixelSize:12}
     }
    }
   }
   Text{Layout.fillWidth:true;visible:!root.upcoming.length;text:qsTr('Nothing planned today');color:'#a0a0a7';font.family:'SF Pro Text';font.pixelSize:13;wrapMode:Text.WordWrap}
   Item{Layout.fillHeight:true}
  }
  GridLayout{visible:root.monthView;Layout.fillWidth:true;Layout.fillHeight:true;columns:7;columnSpacing:8;rowSpacing:3
   Repeater{model:['M','T','W','T','F','S','S'];delegate:Text{required property string modelData;Layout.fillWidth:true;text:modelData;horizontalAlignment:Text.AlignHCenter;color:'#86868d';font.family:'SF Pro Text';font.pixelSize:10}}
   Repeater{model:42
    delegate:Rectangle{required property int index;readonly property int number:index-((new Date(root.today.getFullYear(),root.today.getMonth(),1).getDay()+6)%7)+1;readonly property bool valid:number>0 && number<=new Date(root.today.getFullYear(),root.today.getMonth()+1,0).getDate();Layout.fillWidth:true;Layout.fillHeight:true;implicitHeight:17;radius:8;color:valid && number===root.today.getDate() ? '#ff5d69':'transparent'
     Text{anchors.centerIn:parent;text:parent.valid ? parent.number:'';font.family:'SF Pro Text';font.pixelSize:11;color:'white'}
    }
   }
  }
 }
}
