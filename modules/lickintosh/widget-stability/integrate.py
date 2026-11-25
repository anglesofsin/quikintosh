"""Keep presentation state alive through transitions; never filter island controls."""
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
def edit(name,old,new):
 p=root/name;s=p.read_text()
 if s.count(old)!=1:raise ValueError(f'{name}: expected one anchor {old[:65]!r}, found {s.count(old)}')
 p.chmod(p.stat().st_mode|0o200);p.write_text(s.replace(old,new))
edit('rosa/overlays/Island.qml','IslandConfig.s("enabled")\n        && IslandConfig.on("clock")','IslandConfig.s("enabled")')
edit('rosa/overlays/IslandPill.qml','readonly property bool hideClock: pill.kind === "voice"','readonly property bool hideClock: !IslandConfig.on("clock") || pill.kind === "voice"')
p=root/'ui/settings/pages/RosaPage.qml';s=p.read_text();a=s.index('    TahoeField {');b=s.index('    ContentSection {',a);s=s[:a]+s[b:];s=s.replace('    property string settingsFilter: ""\n','');s=re.sub(r'group\.modelData\.names\.filter\(function\(name\)\{[^\n]+\}\)', 'group.modelData.names',s);p.chmod(p.stat().st_mode|0o200);p.write_text(s)
edit('components/glass/LiquidGlassBackdrop.qml','readonly property Item blurSource: blurFinal','readonly property Item blurSource: blurFinal\n    // Glyph refraction needs the crisp scene, not the panel frosting pass.\n    readonly property Item glyphSource: fb')
# Keep the capture provider and material mounted throughout the exit. State
# changes must not remove glass a frame before the gallery itself disappears.
edit('ui/widgets/WidgetGallery.qml'," readonly property bool opened:WidgetState.galleryZone!==''", " readonly property bool opened:WidgetState.galleryZone!==''\n Presence{id:presence;wanted:root.opened;exitDuration:180}")
edit('ui/widgets/WidgetGallery.qml','  active:root.opened','  active:presence.present')
edit('ui/widgets/WidgetGallery.qml','id:panel;anchors.horizontalCenter:', 'id:panel;opacity:root.opened ? 1:0;scale:root.opened ? 1:.97\n    Behavior on opacity{NumberAnimation{duration:150}}\n    Behavior on scale{NumberAnimation{duration:150;easing.type:Easing.OutCubic}}\n    anchors.horizontalCenter:')
# Retain the selected preview style while the gallery fades out. Next opening
# can keep the user's last selection rather than flashing back to Automatic.
edit('services/WidgetState.qml','        root.galleryTheme = "auto"\n','')

# The clock preference is global; call layout preferences never override it.
edit('rosa/overlays/VoiceView.qml','visible:!view.expanded && !view.bubble && IslandConfig.s("voiceClock")','visible:!view.expanded && !view.bubble && IslandConfig.s("voiceClock") && IslandConfig.on("clock")')
edit('rosa/overlays/IslandBody.qml','case "clock":  return Qt.formatDateTime(clockTick.date, "HH:mm");','case "clock":  return IslandConfig.on("clock") ? Qt.formatDateTime(clockTick.date, "HH:mm") : "";')
edit('rosa/overlays/IslandBody.qml','case "clock":  return "󰥔";','case "clock":  return IslandConfig.on("clock") ? "󰥔" : "";')
import json
p=root/'rosa/lang/en.json';data=json.loads(p.read_text());data['isle.o.srcClock']='Show clock';p.chmod(p.stat().st_mode|0o200);p.write_text(json.dumps(data,ensure_ascii=False))

# New profiles start with a quiet island; stored user preferences still win.
edit('rosa/services/IslandConfig.qml','srcClock:    { type: "bool", def: true }','srcClock:    { type: "bool", def: false }')
