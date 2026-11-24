"""Explicit popup focus ownership and one contrast/color policy for the menu bar."""
from pathlib import Path
import sys,re,shutil
root=Path(sys.argv[1]);here=Path(__file__).parent

def edit(name,old,new):
 p=root/name;s=p.read_text()
 if s.count(old)!=1:raise ValueError(f'Interface anchor {name}: {old[:80]} ({s.count(old)})')
 p.write_text(s.replace(old,new,1))
spot='ui/topbar/statusarea/spotlight/SpotlightWindow.qml'
edit(spot,'root.opened ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None','root.opened && !win.closing ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None')
edit(spot,'root.opened || hideAnim.running ? win.contentItem : null','root.opened && !win.closing ? win.contentItem : null')
edit(spot,'                    searchField.forceActiveFocus()\n                }\n\n                function refreshClipboard','                    searchField.forceActiveFocus()\n                    Qt.callLater(function(){if(root.opened && !win.closing)searchField.forceActiveFocus()})\n                }\n\n                function refreshClipboard')
edit(spot,'                                            if (win.showingShellOutput) { win.showingShellOutput = false; event.accepted = true; return }\n','')
edit(spot,'                function refreshClipboard(query) {','''                Shortcut { sequence:"Escape";context:Qt.WindowShortcut;enabled:root.opened && !win.closing;onActivated:win.closeGracefully() }
                function refreshClipboard(query) {''')
# Text-entry popups claim focus only while logically open; exit animations cannot trap it.
edit('ui/topbar/statusarea/ai/AiWindow.qml','WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand','WlrLayershell.keyboardFocus: root.opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None')
edit('ui/topbar/statusarea/StatusSubMenuWindow.qml','WlrLayershell.keyboardFocus: root.needsKeyboard\n                                             ? WlrKeyboardFocus.OnDemand','WlrLayershell.keyboardFocus: root.opened && root.needsKeyboard\n                                             ? WlrKeyboardFocus.Exclusive')
for src,target in [('TopBarStyle.qml','services/TopBarStyle.qml'),('BarLogo.qml','components/BarLogo.qml'),('bar-sample.py','tools/bar-sample.py'),('bar-tint.frag','components/bar-tint.frag')]:
 shutil.copyfile(here/src,root/target)
for directory,line in [('services','singleton TopBarStyle TopBarStyle.qml'),('components','BarLogo BarLogo.qml')]:
 p=root/directory/'qmldir'
 if p.exists():p.write_text(p.read_text()+'\n'+line+'\n')
 else:p.write_text('\n'.join(('singleton ' if re.search(r'^pragma Singleton',file.read_text(),re.M) else '')+file.stem+' '+file.name for file in sorted((root/directory).glob('*.qml')))+'\n')
edit('services/ShellConfig.qml','            property JsonObject topbar: JsonObject {','''            property JsonObject topbar: JsonObject {
                property string foregroundMode:"auto"
                property string foregroundColor:"#fafafa"
                property bool logoVisible:true
                property string logoType:"linux"
                property string logoSource:""
                property string logoText:""
                property string logoColorMode:"follow"
                property string logoColor:"#fafafa"
                property int logoSize:18''')
edit('ui/settings/pages/TopBarPage.qml','import qs.services','import qs.services\nimport qs.components')
edit('ui/settings/pages/TopBarPage.qml','    id: root','    id: root\n'+(here/'settings.qml.inc').read_text())
menu=root/'ui/topbar/menubar/MenuBar.qml';s=menu.read_text();start=s.index('    Image {');end=s.index('\n    ActiveWindow {',start)
s=s[:start]+'''    Item {
        Layout.preferredHeight:logo.implicitHeight;Layout.preferredWidth:logo.implicitWidth
        Layout.alignment:Qt.AlignVCenter;visible:ShellConfig.options.topbar.logoVisible
        BarLogo {id:logo;anchors.fill:parent;opacity:menuBarRoot.appleActive ? 0.7 : 1}
        MouseArea {anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:menuBarRoot.appleClicked()}
    }
''' +s[end:];s='import qs.services\nimport qs.components\n'+s;menu.write_text(s)
# Only top-level bar components, never popup content or the island's dark surfaces.
files=['menubar/activewindows/ActiveWindow.qml','menubar/globalmenu/GlobalMenuBar.qml','statusarea/StatusArea.qml','statusarea/clock/Clock.qml','statusarea/volume/Volume.qml','statusarea/battery/Battery.qml','statusarea/wifi/Wifi.qml','statusarea/bluetooth/Bluetooth.qml','statusarea/systemtray/BTDeviceTray.qml']
for name in files:
 p=root/'ui/topbar'/name;s=p.read_text()
 for imp in ['import Quickshell','import qs.services']:
  if imp+'\n' not in s:s=imp+'\n'+s
 side='left' if name.startswith('menubar/') else 'right'
 color=f'TopBarStyle.colorFor(QsWindow.window ? QsWindow.window.screen : null,"{side}")'
 s=re.sub(r'"#(?:FFFFFF|ffffff|fff|FFF)"',color,s)
 s=s.replace('Qt.rgba(1, 1, 1, 0.70)',color)
 # Hover feedback uses opacity; the foreground must continue matching the wallpaper.
 s=s.replace('"#AAAAAA"',color)
 # Vector sources have hard-coded fills; tint their alpha, including black pixels.
 if name in ['statusarea/volume/Volume.qml','statusarea/battery/Battery.qml','statusarea/wifi/Wifi.qml','statusarea/bluetooth/Bluetooth.qml','statusarea/StatusArea.qml']:
  s=s.replace('preferredRendererType: VectorImage.CurveRenderer', 'preferredRendererType: VectorImage.CurveRenderer\n            layer.enabled:true\n            layer.effect:ShaderEffect {property var source;property color tint:'+color+';fragmentShader:Quickshell.shellDir+"/components/bar-tint.frag.qsb"}')
  # StatusArea already supplies effects on its vector icons. Replace those instead.
  if name=='statusarea/StatusArea.qml':
   # Avoid duplicate layer properties in blocks that previously had MultiEffect.
   s=re.sub(r'(preferredRendererType: VectorImage.CurveRenderer)\n            layer.enabled:true\n            layer.effect:ShaderEffect \{[^\n]+\}(\s+layer.enabled: true\s+layer.effect: MultiEffect \{\s+colorization: 1\s+colorizationColor: [^\n]+\n\s+\})',r'\1\2',s)
   s=re.sub(r'layer.effect: MultiEffect \{\s+colorization: 1\s+colorizationColor: [^\n]+\n\s+\}', 'layer.effect:ShaderEffect {property var source;property color tint:'+color+';fragmentShader:Quickshell.shellDir+"/components/bar-tint.frag.qsb"}',s)
 if name=='statusarea/StatusArea.qml':
  start=s.index('            id: aiBtn');end=s.index('            id: _clockWrap',start)
  block=re.sub(r'\n            layer.enabled:true\n            layer.effect:ShaderEffect \{[^\n]+\}','',s[start:end])
  s=s[:start]+block+s[end:]
  s=re.sub(r'onEntered:\s+_clock.color = [^\n]+','onEntered: _clock.opacity=0.7',s)
  s=re.sub(r'onExited:\s+_clock.color = [^\n]+','onExited: _clock.opacity=1',s)
  # Keep notification counters white on their semantic red badge.
  start=s.index('                    id: _badgeTxt');end=s.index('                    renderType:',start)
  s=s[:start]+s[start:end].replace(color,'"#ffffff"')+s[end:]
 p.write_text(s)
# Closing popups may keep painting their exit animation, but must stop swallowing
# clicks immediately; this is independent of keyboard focus and glass readiness.
for path,window_id in [('ui/topbar/menubar/applemenu/AppleMenuWindow.qml','panel'),('ui/topbar/statusarea/StatusSubMenuWindow.qml','panel'),('ui/topbar/statusarea/ai/AiWindow.qml','win')]:
 edit(path,'                id: '+window_id,'                id: '+window_id+'\n                mask: Region {item:root.opened ? '+window_id+'.contentItem : null}')
