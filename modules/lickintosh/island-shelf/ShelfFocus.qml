import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import qs.services
Item{
 id:root
 objectName:'shelf-focus'
 readonly property bool focusPhase:PomodoroState.phase==='work'
 readonly property color accent:focusPhase ? '#ffad22':'#8ce5c5'
 function choosePhase(work){PomodoroState.pause();PomodoroState.phase=work ? 'work':'break';PomodoroState.remainingAtPauseMs=PomodoroState._phaseDurationMs(PomodoroState.phase)}
 function time(ms){const total=Math.ceil(ms/1000);return String(Math.floor(total/60)).padStart(2,'0')+':'+String(total%60).padStart(2,'0')}
 ColumnLayout{anchors.fill:parent;spacing:8
  RowLayout{Layout.fillWidth:true
   ShelfButton{text:qsTr('Focus');selected:root.focusPhase;selectedColor:'#593a0a';foreground:root.focusPhase ? root.accent:'#a1a1a6';onClicked:root.choosePhase(true)}
   ShelfButton{text:qsTr('Break');selected:!root.focusPhase;selectedColor:'#234339';foreground:!root.focusPhase ? root.accent:'#a1a1a6';onClicked:root.choosePhase(false)}
  }
  Item{Layout.fillWidth:true;Layout.fillHeight:true;Layout.minimumHeight:50
   Row{anchors.horizontalCenter:parent.horizontalCenter;anchors.top:parent.top;anchors.topMargin:3;spacing:18
    Repeater{model:5
     delegate:Text{required property int index;readonly property int minutes:Math.max(1,(root.focusPhase ? PomodoroState.workMinutes:PomodoroState.breakMinutes)+(index-2)*5);text:minutes;color:index===2 ? '#ffffff':root.accent;opacity:index===2 ? 1:.6;font.family:ShelfStyle.textFamily;font.pixelSize:12;font.weight:Font.DemiBold;width:25;horizontalAlignment:Text.AlignHCenter}
    }
   }
   Row{anchors.horizontalCenter:parent.horizontalCenter;anchors.verticalCenter:parent.verticalCenter;anchors.verticalCenterOffset:7;spacing:5
    Repeater{model:Math.max(10,Math.floor((root.width-20)/7))
     delegate:Rectangle{required property int index;width:2;height:index%5===0 ? 28:17;radius:1;color:root.accent;opacity:Math.max(.12,1-Math.abs(index-(parent.children.length-1)/2)/(parent.children.length/2))}
    }
   }
   Text{anchors.horizontalCenter:parent.horizontalCenter;anchors.bottom:parent.bottom;text:'▴';color:root.accent;font.pixelSize:13}
   Slider{anchors.fill:parent;from:1;to:480;stepSize:1;enabled:!PomodoroState.running;value:root.focusPhase ? PomodoroState.workMinutes:PomodoroState.breakMinutes
    property bool held:false
    Accessible.name:qsTr('Session duration')
    onPressedChanged:{if(held!==pressed){held=pressed;ShelfState.interaction(held)}}
    Component.onDestruction:if(held)ShelfState.interaction(false)
    onMoved:{if(root.focusPhase)PomodoroState.workMinutes=value;else PomodoroState.breakMinutes=value;PomodoroState.remainingAtPauseMs=PomodoroState._phaseDurationMs(PomodoroState.phase)}
    background:Item{}
    handle:Item{}
   }
  }
  RowLayout{Layout.fillWidth:true;spacing:8
   ShelfButton{implicitWidth:36;implicitHeight:36;iconSize:18;selected:true;selectedColor:'#593a0a';foreground:root.accent;icon:PomodoroState.running ? 'pause.png':'play.png';accessibleLabel:PomodoroState.running ? qsTr('Pause timer'):qsTr('Start timer');onClicked:PomodoroState.running ? PomodoroState.pause():PomodoroState.start()}
   ShelfButton{implicitWidth:36;implicitHeight:36;iconSize:20;flat:true;icon:'notch/rotate-ccw.svg';accessibleLabel:qsTr('Reset timer');onClicked:PomodoroState.reset()}
   Item{Layout.fillWidth:true}
   Text{text:root.time(PomodoroState.remainingMs);color:root.accent;font.family:ShelfStyle.displayFamily;font.pixelSize:30;font.weight:Font.DemiBold}
  }
 }
}
