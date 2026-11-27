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
 ColumnLayout{anchors.fill:parent;spacing:12
  RowLayout{Layout.fillWidth:true
   ShelfButton{text:qsTr('Focus');selected:root.focusPhase;onClicked:root.choosePhase(true)}
   Item{Layout.fillWidth:true}
   ShelfButton{text:qsTr('Break');selected:!root.focusPhase;onClicked:root.choosePhase(false)}
  }
  Item{Layout.fillWidth:true;Layout.fillHeight:true;Layout.minimumHeight:50
   Row{anchors.centerIn:parent;spacing:5
    Repeater{model:Math.max(10,Math.floor((root.width-20)/7))
     delegate:Rectangle{required property int index;width:2;height:index%5===0 ? 28:17;radius:1;color:root.accent;opacity:Math.max(.12,1-Math.abs(index-(parent.children.length-1)/2)/(parent.children.length/2))}
    }
   }
   Slider{anchors.fill:parent;from:5;to:60;stepSize:5;enabled:!PomodoroState.running;value:root.focusPhase ? PomodoroState.workMinutes:PomodoroState.breakMinutes
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
   ShelfButton{icon:PomodoroState.running ? 'pause.png':'play.png';accessibleLabel:PomodoroState.running ? qsTr('Pause timer'):qsTr('Start timer');onClicked:PomodoroState.running ? PomodoroState.pause():PomodoroState.start()}
   ShelfButton{flat:true;icon:'notch/rotate-ccw.svg';accessibleLabel:qsTr('Reset timer');onClicked:PomodoroState.reset()}
   Item{Layout.fillWidth:true}
   Text{text:root.time(PomodoroState.remainingMs);color:root.accent;font.family:ShelfStyle.displayFamily;font.pixelSize:30;font.weight:Font.DemiBold}
  }
 }
}
