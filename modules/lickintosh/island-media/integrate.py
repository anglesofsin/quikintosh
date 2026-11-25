"""One compact music silhouette: round spinning cover, clock space and bars."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
def edit(name,old,new,count=1):
 p=root/name;s=p.read_text()
 if s.count(old)!=count:raise ValueError(f'Media island anchor {name}: {old[:70]!r} ({s.count(old)})')
 p.chmod(p.stat().st_mode|0o200);p.write_text(s.replace(old,new))
name='rosa/overlays/IslandPill.qml'
edit(name,'import qs.rosa.services','import qs.rosa.services\nimport qs.services as Native')
edit(name,'    readonly property int inner: Math.max(12, pill.height - 8)','    readonly property bool compactMedia: pill.miniMedia && !pill.flashing && pill.kind !== "voice"\n    readonly property int inner: Math.max(12, pill.height - (pill.miniMedia ? 10 : 8))')
edit(name,'pill.miniMedia ? Math.round(pill.inner + 14) : 0','pill.miniMedia ? Math.round(pill.inner + 8) : 0')
edit(name,'pill.coreW + pill.sideRoom * 2 + 24','pill.coreW + pill.sideRoom * 2 + (pill.compactMedia ? 14 : 24)')
p=root/name;s=p.read_text();a=s.index('        Item {\n            id: miniArt');b=s.index('        IslandBars {\n            id: miniBars',a)
s=s[:a]+'''        Item {
            id: miniArt
            anchors.left: parent.left
            anchors.leftMargin: pill.compactMedia ? 7 : 6
            anchors.verticalCenter: parent.verticalCenter
            width: pill.inner
            height: width
            opacity: pill.miniMedia ? 1 : 0
            visible: opacity > 0.01
            Behavior on opacity { NumberAnimation { duration:Motion.isleHideMs } }
            ClippingRectangle {
                id: record
                anchors.fill:parent
                opacity:pill.artVeil
                radius:width/2
                color:Colors.alpha(pill.mediaTint,0.28)
                RotationAnimator on rotation {
                    from:0;to:360;duration:14000;loops:Animation.Infinite
                    running:miniArt.visible && pill.miniMedia && !Native.SettingsPreferences.accessibility.reduceMotion
                    paused:running && (!Media.playing || Stage.gaming)
                }
                Image {
                    anchors.fill:parent
                    visible:Media.art!==""
                    source:Media.art
                    fillMode:Image.PreserveAspectCrop
                    asynchronous:true;cache:true;smooth:true;mipmap:true
                    sourceSize:Qt.size(96,96)
                }
                Text {
                    anchors.centerIn:parent;visible:Media.art===""
                    text:"󰎈";color:pill.mediaTint;font.family:Fonts.glyph
                    font.pixelSize:Math.max(8,parent.width*.6)
                }
                Rectangle {
                    anchors.centerIn:parent;width:3;height:width;radius:width/2
                    color:"#c0000000";border.width:.5;border.color:"#70ffffff"
                }
            }
        }

'''+s[b:];p.write_text(s)
a=s.index('        IslandBars {\n            id: miniBars');tail=s[a:].replace('anchors.rightMargin: 8','anchors.rightMargin: pill.compactMedia ? 7 : 8',1).replace('width: Math.round(pill.inner * 1.1)','width: pill.inner',1).replace('height: Math.round(pill.inner * 0.8)','height: Math.round(pill.inner * 0.8)',1);p.write_text(s[:a]+tail)
name='rosa/overlays/IslandWindow.qml'
edit(name,'target: win.hub.kind === "voice" ? pill.implicitWidth : Math.max(IslandConfig.s("pillMin"), pill.implicitWidth + 26)','target: win.hub.kind === "voice" || pill.compactMedia ? pill.implicitWidth : Math.max(IslandConfig.s("pillMin"), pill.implicitWidth + 26)')
edit(name,'win.hub.kind === "voice" ? pill.implicitWidth : Math.max(IslandConfig.s("pillMin"),pill.implicitWidth+26)','win.hub.kind === "voice" || pill.compactMedia ? pill.implicitWidth : Math.max(IslandConfig.s("pillMin"),pill.implicitWidth+26)')
# A single music capsule uses the same rectangle and height as the call state.
# Goo is only useful when joining separate activity bubbles.
edit(name,'visible: IslandConfig.s("goo") && count > 0 && !win.hub.voiceSide','visible: IslandConfig.s("goo") && count > 0 && !win.hub.voiceSide && !pill.compactMedia')
edit(name,'visible: !IslandConfig.s("goo") || goo.count <= 0 || win.hub.voiceSide','visible: !IslandConfig.s("goo") || goo.count <= 0 || win.hub.voiceSide || pill.compactMedia',count=3)

# The outside silhouette is stable. Only the bars respond to audio levels;
# border pulse and jelly must not make the black capsule look compressed.
edit(name,'readonly property int pillH: IslandConfig.s("pillHeight")','readonly property int pillH: pill.compactMedia ? Math.max(30, IslandConfig.s("pillHeight") + 4) : IslandConfig.s("pillHeight")')
edit(name,'IslandConfig.s("pulse") && win.hub.miniMedia && win.visible','IslandConfig.s("pulse") && win.hub.miniMedia && !pill.compactMedia && win.visible')
edit(name,'readonly property real jelly: IslandConfig.s("jelly")','readonly property real jelly: IslandConfig.s("jelly") && !pill.compactMedia')
edit(name,'visible: IslandConfig.s("glow") && aura.power > 0.005 && !win.hub.voiceSide','visible: IslandConfig.s("glow") && aura.power > 0.005 && !win.hub.voiceSide && !pill.compactMedia')
