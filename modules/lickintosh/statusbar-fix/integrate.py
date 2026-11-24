from pathlib import Path
import sys
root=Path(sys.argv[1])
def edit(name,old,new):
 p=root/name;s=p.read_text();assert s.count(old)==1,(name,old[:80],s.count(old));p.chmod(p.stat().st_mode|0o200);p.write_text(s.replace(old,new,1))
p=root/'ui/topbar/statusarea/StatusArea.qml';s=p.read_text().replace('implicitHeight: Math.max(24,_clock.implicitHeight)','implicitHeight: 24').replace('                id: _clock\n','                id: _clock\n                anchors.verticalCenter:parent.verticalCenter\n',1)
a=s.index('            Rectangle {\n                id: _badge');z=s.index('            MouseArea {',a)
s=s[:a]+'''            Rectangle {
                id: _badge
                anchors.right:parent.right
                anchors.top:parent.top
                anchors.topMargin:1
                width:4;height:4;radius:2
                color:TopBarStyle.colorFor(QsWindow.window ? QsWindow.window.screen:null,"right")
                visible:root.notifUnreadCount>0 && ShellConfig.options.topbar.clockBadgeVisible
            }

'''+s[z:];p.chmod(p.stat().st_mode|0o200);p.write_text(s)
edit('shell.qml','notifUnreadCount: NotifService.trackedCount','notifUnreadCount: NotifService.unreadCount')
p=root/'ui/topbar/statusarea/notifcenter/NotifService.qml';s=p.read_text();s=s.replace('    property int  trackedCount:     0','''    property int  trackedCount:     0
    property var unread:[]
    readonly property int unreadCount:unread.length
    function markRead(){unread=[]}
    function forgetUnread(notification){unread=unread.filter(item=>item!==notification)}''')
s=s.replace('    function removeFromCenter(notifObj) {','    function removeFromCenter(notifObj) {\n        root.forgetUnread(notifObj)').replace('        if (root.centerOpened) {\n            _groupTimer.stop()','        if (root.centerOpened) {\n            root.markRead()\n            _groupTimer.stop()',1).replace('        _centerModel.append({ notifObj: notification })','        if(!root.centerOpened)root.unread=root.unread.concat([notification])\n        _centerModel.append({ notifObj: notification })',1)
p.chmod(p.stat().st_mode|0o200);p.write_text(s)
# Respect the configured date/time format; the previous clock hardcoded two
# labels and could disagree with the date/time settings page.
p=root/'ui/topbar/statusarea/clock/Clock.qml';p.chmod(p.stat().st_mode|0o200);p.write_text('''import Quickshell
import QtQuick
import qs.services
Item{
 id:root
 property color color:TopBarStyle.colorFor(QsWindow.window ? QsWindow.window.screen:null,"right")
 implicitWidth:label.implicitWidth
 implicitHeight:24
 SystemClock{id:clock;precision:SystemClock.Seconds}
 Text{
  id:label;anchors.verticalCenter:parent.verticalCenter
  text:Qt.formatDateTime(clock.date,ShellConfig.options.topbar.clockTextVisible ? ShellConfig.options.topbar.clockFormat:'HH:mm')
  color:root.color;font.family:'SF Pro Text';font.pixelSize:13;font.weight:Font.DemiBold
  renderType:Text.NativeRendering
 }
}
''')
