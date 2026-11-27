"""Keep menu geometry stable while fading the complete glass surface to zero."""
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
paths=['ui/topbar/menubar/applemenu/AppleMenuWindow.qml','ui/topbar/statusarea/StatusSubMenuWindow.qml','ui/topbar/menubar/globalmenu/PopupMenu.qml']
for name in paths:
 p=root/name;s=p.read_text();assert 'Presence { id: presence; wanted: root.opened }' in s,name
 s=s.replace('    property bool opened: false','''    property bool animating:false
    property bool closingAnimation:false
    Connections{target:root;function onOpenedChanged(){
        if(root.opened){root.closingAnimation=false;return}
        root.closingAnimation=presence.present && ShellMotion.duration(160)>0
        Qt.callLater(function(){if(!root.opened && !root.animating)root.closingAnimation=false})
    }}
    property bool opened: false''',1)
 s=s.replace('Presence { id: presence; wanted: root.opened }','Presence { id: presence; wanted: root.opened || root.closingAnimation; exitDuration:0 }')
 if name.endswith('AppleMenuWindow.qml'):
  s=s.replace('import qs.components\n','import qs.components\nimport qs.services\n',1)
  s=s.replace('id: appleMenu','id: appleMenu\n                    onTransitioningChanged:{root.animating=appleMenu.transitioning;if(!root.animating && !root.opened)root.closingAnimation=false}',1)
 else:
  s=re.sub(r'scale:\s*\(root.opened && panel.entered\) \? 1 : 0.95','scale:1',s)
  s=re.sub(r'Behavior on scale \{ NumberAnimation \{[^\n]+\} \}', '',s)
  s=re.sub(r'Behavior on opacity \{ NumberAnimation \{[^\n]+\} \}', 'Behavior on opacity { NumberAnimation { duration:ShellMotion.duration(160); easing.type:root.opened ? Easing.OutCubic:Easing.InQuad; onRunningChanged:{root.animating=running;if(!running && !root.opened)root.closingAnimation=false} } }',s)
 p.chmod(p.stat().st_mode|0o200);p.write_text(s)
p=root/'ui/topbar/menubar/applemenu/AppleMenu.qml';s=p.read_text();s=s.replace('scale:   opened ? 1 : 0.95','scale:1')
s=re.sub(r'    Behavior on scale \{\n        NumberAnimation \{[^\n]+\}\n    \}', '',s)
s=s.replace('duration: Math.min(120, ShellMotion.fade()); easing.type: Easing.BezierSpline; easing.bezierCurve: ShellMotion.effectsCurve','duration:ShellMotion.duration(160); easing.type:root.opened ? Easing.OutCubic:Easing.InQuad')
p.chmod(p.stat().st_mode|0o200);p.write_text(s)

# The layer lifetime follows actual animation completion, not a wall-clock timer.
p=root/'ui/topbar/menubar/applemenu/AppleMenu.qml';s=p.read_text().replace('    id: root','    id: root\n    readonly property bool transitioning:menuFade.running',1)
a=s.rfind('    Behavior on opacity {');assert a>=0
s=s[:a]+s[a:].replace('NumberAnimation { duration:', 'NumberAnimation { id:menuFade; duration:',1)
p.write_text(s)
