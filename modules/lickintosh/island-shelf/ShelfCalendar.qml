import QtQuick
import QtQuick.Layouts
import qs.services
Item {
 id:root
 property date today:new Date()
 readonly property bool monthView:width>440
 readonly property var upcoming:CalendarState.available ? CalendarState.events:[]
 function week(){const d=new Date(Date.UTC(today.getFullYear(),today.getMonth(),today.getDate()));d.setUTCDate(d.getUTCDate()+4-(d.getUTCDay() || 7));return Math.ceil(((d-new Date(Date.UTC(d.getUTCFullYear(),0,1)))/86400000+1)/7)}
 Timer{interval:60000;repeat:true;running:root.visible;onTriggered:root.today=new Date()}
 ColumnLayout{anchors.fill:parent;spacing:10
  RowLayout{Layout.fillWidth:true;spacing:5
   Item{visible:!root.monthView;Layout.fillWidth:true}
   Text{text:Qt.formatDate(root.today,'ddd').toUpperCase();font.family:ShelfStyle.textFamily;font.pixelSize:18;font.weight:Font.DemiBold;color:'#ff5d69'}
   Text{text:root.today.getDate();font.family:ShelfStyle.textFamily;font.pixelSize:18;font.weight:Font.DemiBold;color:'white'}
   Text{text:'W'+root.week();font.family:ShelfStyle.textFamily;font.pixelSize:14;font.weight:Font.DemiBold;color:'#89444b'}
   Item{visible:root.monthView;Layout.fillWidth:true}
   Text{visible:root.monthView;text:Qt.formatDate(root.today,'MMM').toUpperCase();font.family:ShelfStyle.textFamily;font.pixelSize:18;font.weight:Font.DemiBold;color:'#ff453a'}
  }
  Item{id:calendarBody;Layout.fillWidth:true;Layout.fillHeight:true
  readonly property real monthWidth:Math.min(240,width*.46)
  ListView{id:events;anchors.left:parent.left;anchors.top:parent.top;anchors.bottom:parent.bottom;width:calendarBody.width-(root.monthView ? calendarBody.monthWidth+18:0);spacing:6;clip:true;reuseItems:true;boundsBehavior:Flickable.StopAtBounds;model:root.upcoming
   delegate:Rectangle{required property var modelData;required property int index;width:events.width;height:49;radius:7;color:['#66102d49','#663b2909','#66241b49'][index%3]
    readonly property color labelColor:['#5dadff','#ffc16a','#b49bff'][index%3]
    Rectangle{anchors.left:parent.left;anchors.top:parent.top;anchors.bottom:parent.bottom;anchors.margins:4;width:3;radius:2;color:['#168fff','#ffb23e','#9a79ff'][index%3]}
    ColumnLayout{anchors.fill:parent;anchors.leftMargin:12;anchors.rightMargin:8;anchors.topMargin:4;anchors.bottomMargin:4;spacing:1
     Text{Layout.fillWidth:true;text:modelData.title || '';textFormat:Text.PlainText;elide:Text.ElideRight;color:parent.parent.labelColor;font.family:ShelfStyle.textFamily;font.pixelSize:18;font.weight:Font.DemiBold}
     Text{Layout.fillWidth:true;text:modelData.time || '';textFormat:Text.PlainText;elide:Text.ElideRight;color:parent.parent.labelColor;opacity:.8;font.family:ShelfStyle.textFamily;font.pixelSize:16}
    }
   }
   Text{anchors.centerIn:parent;width:parent.width;visible:!root.upcoming.length;text:qsTr('Nothing planned today');color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:13;wrapMode:Text.WordWrap}
  }
  GridLayout{visible:root.monthView;anchors.right:parent.right;anchors.top:parent.top;anchors.bottom:parent.bottom;width:calendarBody.monthWidth;columns:7;columnSpacing:8;rowSpacing:3
   Repeater{model:['M','T','W','T','F','S','S'];delegate:Text{required property string modelData;Layout.fillWidth:true;text:modelData;horizontalAlignment:Text.AlignHCenter;color:'#86868d';font.family:ShelfStyle.textFamily;font.pixelSize:10}}
   Repeater{model:42
    delegate:Rectangle{required property int index;readonly property int number:index-((new Date(root.today.getFullYear(),root.today.getMonth(),1).getDay()+6)%7)+1;readonly property bool valid:number>0 && number<=new Date(root.today.getFullYear(),root.today.getMonth()+1,0).getDate();Layout.fillWidth:true;Layout.fillHeight:true;implicitHeight:22;radius:Math.min(width,height)/2;color:valid && number===root.today.getDate() ? '#ff5d69':'transparent'
     Text{anchors.centerIn:parent;text:parent.valid ? parent.number:'';font.family:ShelfStyle.textFamily;font.pixelSize:11;color:'white'}
    }
   }
  }
  }
 }
}
