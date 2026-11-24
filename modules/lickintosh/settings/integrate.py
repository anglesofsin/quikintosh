"""Install the Tahoe Settings application while preserving shell-specific pages."""
from pathlib import Path
import json
import re
import sys

root = Path(sys.argv[1])
python = sys.argv[2]
here = Path(__file__).parent
destination = root/'settingsapp'
destination.mkdir(exist_ok=True)


def edit(name, before, after, count=1):
    path = root/name
    text = path.read_text()
    if text.count(before) != count:
        raise ValueError(f'Settings integration anchor {name}: {before[:75]} ({text.count(before)})')
    path.write_text(text.replace(before, after))


for path in here.iterdir():
    if path.name in {'SettingsRoot.qml', 'integrate.py', 'test_backend.py', 'README.md', 'capture-classifier.js', 'MediaCaptureState.qml'} or path.is_dir():
        continue
    if path.name=='TahoeSlider.qml':
        (root/'components'/path.name).write_text(path.read_text());continue
    target = root/'services'/path.name if path.name in {'SettingsPreferences.qml', 'SettingsCatalog.qml', 'SettingsState.qml','AudioFeedback.qml'} else destination/path.name
    target.write_text(path.read_text().replace('@PYTHON@', python))

(destination/'qmldir').write_text('\n'.join(path.stem+' '+path.name for path in destination.glob('*.qml'))+'\n')
p = root/'services/qmldir'
p.write_text(p.read_text()+'\n'+ '\n'.join('singleton '+name+' '+name+'.qml' for name in ['SettingsPreferences', 'SettingsCatalog', 'SettingsState','AudioFeedback'])+'\n')
(root/'settings.qml').write_text((here/'SettingsRoot.qml').read_text())
p=root/'ui/settings/pages/AppearancePage.qml'
(p.parent/'LegacyAppearancePage.qml').write_text(p.read_text())
p=p.parent/'qmldir'
if p.exists():
    p.write_text(p.read_text()+'\nLegacyAppearancePage LegacyAppearancePage.qml\n')

# A single source of truth for the lock-screen notification preference.
content=destination/'SettingsContent.qml'
s=content.read_text().replace("pref('Show Notifications on Lock Screen','notifications','showOnLock','switch')", "toggle('Show Notifications on Lock Screen',ShellConfig.options.lockscreen.showNotifications,'lock-notifications')")
s=s.replace("if(name==='preview')", "if(name==='lock-notifications'){ShellConfig.options.lockscreen.showNotifications=value;return}\n  if(name==='preview')")
content.write_text(s)

edit('shell.qml', '    id: appRoot', '''    id: appRoot
    SettingsRuntime{enabled:appRoot.interfaceShown;locked:lockScreen.locked;onLockRequested:lockScreen.lock()}''')
p=root/'shell.qml'
s=p.read_text()
if 'import qs.settingsapp' not in s:
    s='import qs.settingsapp\n'+s
p.write_text(s)

edit('services/ShellMotion.qml', 'GameMode.enabled ? 0 : root.speed', 'GameMode.enabled || SettingsPreferences.accessibility.reduceMotion ? 0 : root.speed')

# Render previews consistently in the native notification center, the island
# and the lock screen, without changing the original Notification objects.
preferences=root/'services/SettingsPreferences.qml'
s=preferences.read_text().replace(' function appRule(name)', ''' function canPreview(){return root.notifications.previews!=='never' && (root.notifications.previews!=='unlocked' || !root.locked)}
 function appRule(name)''')
preferences.write_text(s)
service='ui/topbar/statusarea/notifcenter/NotifService.qml'
edit(service, '    function pushPopup(notification) {', '''    function pushPopup(notification) {
        const prefs=SettingsPreferences,rule=prefs.appRule(notification.appName || '')
        if(!prefs.notifications.appNames.includes(notification.appName) && notification.appName)
            prefs.notifications.appNames=prefs.notifications.appNames.concat([notification.appName]).slice(-100)
        if(!ShellConfig.options.notifications.enable || rule.allowed===false){notification.dismiss();return}
        const critical=notification.urgency===NotificationUrgency.Critical && prefs.focus.allowCritical
        const present=(!root.dndEnabled || critical) && prefs.notifications.banners && rule.banners!==false
''')
edit(service, 'if (!root.dndEnabled) Rosa.LickNotifications.receive(notification)', 'if (present && !prefs.locked) Rosa.LickNotifications.receive(notification)')
edit(service, 'if (!root.centerOpened && !root.dndEnabled)', 'if (!root.centerOpened && present && !prefs.locked)')
edit(service, '        interval: 5000', '        interval: SettingsPreferences.notifications.duration')
edit(service, '    property bool dndEnabled:   false', '''    property bool dndEnabled:   false
    Connections{target:ShellConfig.options.session;function onFocusChanged(){root.dndEnabled=ShellConfig.options.session.focus}}''')

p=root/'ui/topbar/statusarea/notifcenter/NotifItem.qml'
s=p.read_text()
s=s.replace('root.notification ? root.notification.body : ""', 'root.notification && SettingsPreferences.canPreview() ? root.notification.body : ""')
s=s.replace('root.notification ? root.notification.summary : ""', 'root.notification && SettingsPreferences.canPreview() ? root.notification.summary : "Notification"')
p.write_text(s)
p=root/'rosa/services/NotifHistory.qml'
s=p.read_text()
if 'import qs.services\n' not in s:
    s='import qs.services\n'+s
s=s.replace('summary: n.summary || ""', 'summary: SettingsPreferences.canPreview() ? n.summary || "":"Notification"')
s=s.replace('body: (n.body || "").replace', 'body: (SettingsPreferences.canPreview() ? n.body || "":"").replace')
p.write_text(s)
p=root/'ui/lockscreen/LockNotifications.qml'
s=p.read_text().replace('root.cfg.showNotificationPreviews', '(root.cfg.showNotificationPreviews && SettingsPreferences.canPreview())')
p.write_text(s)

# Keep advanced glass controls and automatic-lock configuration reachable from
# their conventional parent pages, with one canonical control for each option.
page='ui/settings/pages/LockScreenPage.qml'
edit(page, '    id: root', '''    id: root
    signal navigate(string page)
    ContentSection{title:"Automatic Locking";TahoeButton{text:"Automatic Locking…";onClicked:root.navigate("auto-lock")}}''')
edit(page, 'import qs.services', 'import qs.services\nimport qs.components') if 'import qs.components\n' not in (root/page).read_text() else None

# The profile name used by the shell follows the same rice-local preference.
p=root/'ui/topbar/menubar/applemenu/AppleMenu.qml'
s=p.read_text()
if 'import qs.services' not in s:
    s='import qs.services\n'+s
p.write_text(s)

# Notification cards return directly to the normal island after the configured dwell.
p=root/'rosa/overlays/Island.qml'
s=p.read_text()
if 'import qs.services\n' not in s:s='import qs.services\n'+s
s=s.replace('interval: IslandConfig.s("dwellMs")', 'interval: root.flashKind === "notif" ? SettingsPreferences.notifications.duration : IslandConfig.s("dwellMs")')
p.write_text(s)

# Reuse the supplied caret asset instead of referencing a missing icon.
for p in (root/'ui/settings/pages').glob('*.qml'):
    s=p.read_text().replace('"chevron-down.svg"', '"notch/chevron-down.svg"')
    p.write_text(s)

p=root/'ui/settings/pages/SpotlightPage.qml'
s=p.read_text()
s=re.sub(r'        ConfigSwitch \{\n            Layout.fillWidth: true\n            text: I18n.tr\("Calculatrice"\).*?\n        \}\n', '', s, flags=re.S)
p.write_text(s)
p=root/'ui/settings/pages/MonitorsPage.qml'
s=p.read_text().replace('visible: _monSection.menuMirrorOpen','visible: !!_monSection.menuMirrorOpen')
p.write_text(s)

# Existing pages retain their real controls, but share the Settings visual system.
(root/'ui/settings/widgets/ContentSection.qml').write_text('''import QtQuick
import QtQuick.Layouts
import qs.settingsapp
SettingsCard{id:root;default property alias content:root.rows}
''')
for relative in ['ui/settings/widgets/ConfigSwitch.qml','ui/settings/pages/ConfigSwitch.qml']:
    (root/relative).write_text('''import QtQuick
import QtQuick.Layouts
import qs.settingsapp
Item{
 id:root
 property alias text:control.label
 property alias description:control.description
 property alias checked:control.checked
 signal toggled(bool value)
 Layout.fillWidth:true;implicitHeight:control.implicitHeight
 SettingsRow{id:control;anchors.fill:parent;kind:'switch';separator:false;onToggled:value=>root.toggled(value)}
}
''')
(root/'ui/settings/widgets/ConfigSlider.qml').write_text('''import QtQuick
import QtQuick.Layouts
import qs.settingsapp
Item{
 id:root
 property string text:''
 property real value:0
 property real from:0
 property real to:1
 property string valueSuffix:''
 property int decimals:0
 signal moved(real value)
 Layout.fillWidth:true;implicitHeight:control.implicitHeight
 SettingsRow{
  id:control;anchors.fill:parent;label:root.text;kind:'slider';separator:false
  value:root.value.toFixed(root.decimals)+root.valueSuffix
  number:root.value;minimum:root.from;maximum:root.to;step:Math.pow(10,-root.decimals)
  onCommitted:value=>{root.value=value;root.moved(value)}
 }
}
''')
for p in (root/'ui/settings/pages').glob('*.qml'):
    s=p.read_text()
    changed=re.sub(r'\bComboBox\s*\{', 'TahoeCombo {', s)
    changed=re.sub(r'\bButton\s*\{', 'TahoeButton {', changed)
    changed=re.sub(r'\bTextField\s*\{', 'TahoeField {', changed)
    if changed!=s and 'import qs.components\n' not in changed:changed='import qs.components\n'+changed
    p.write_text(changed)

p=root/'components/qmldir'
p.write_text(p.read_text()+'\nTahoeSlider TahoeSlider.qml\n')
(root/'components/CFSlider.qml').write_text('import QtQuick\nimport qs.components\nTahoeSlider{}\n')

# All feedback listeners share one gate: a manual volume panel is already the
# feedback, and late PipeWire events must not summon another popup on close.
edit('shell.qml','    id: appRoot','''    id: appRoot
    Binding{target:AudioFeedback;property:"panelOpen";value:appRoot.volumeOpened || appRoot.ccOpened}
    Binding{target:AudioFeedback;property:"nativeVisible";value:_osd._visible}''')
osd=root/'ui/osd/OSD.qml'
s=osd.read_text().replace('if (!root._ready || root.blocked || root.batteryShowing) return','if (!root._ready || root.blocked || root.batteryShowing || AudioFeedback.suppressed) return')
s=s.replace('    function _showVolume() {','''    onBlockedChanged:if(blocked){root._visible=false;_hideTimer.stop()}
    Connections{target:AudioFeedback;function onSuppressedChanged(){if(AudioFeedback.suppressed && root._currentType==="volume"){root._visible=false;_hideTimer.stop()}}}
    function _showVolume() {
        if(AudioFeedback.suppressed)return''')
osd.write_text(s)
p=root/'rosa/services/Feedback.qml'
s=p.read_text()
if 'import qs.services\n' not in s:s='import qs.services\n'+s
s=s.replace('    function flash(icon, value, withBar, label, isFlat, channel) {','''    Connections{target:AudioFeedback;function onSuppressedChanged(){if(AudioFeedback.suppressed && ["sink","source"].includes(root.channel)){root.shown=false;life.stop()}}}
    function flash(icon, value, withBar, label, isFlat, channel) {
        if(["sink","source"].includes(channel || "sink") && AudioFeedback.suppressed)return''')
p.write_text(s)

p=root/'ui/settings/pages/DockPage.qml'
s=p.read_text()
s=re.sub(r'        Text \{[^\n]*text:"Drag pinned apps to reorder them[^\n]*\}\n', '', s)
p.write_text(s)

# qs.* imports require module descriptors in the installed source as well as QA.
# Preserve upstream descriptors, including singleton declarations.
for directory in [root, *sorted({path.parent for path in root.rglob('*.qml')})]:
    descriptor = directory/'qmldir'
    if descriptor.exists():
        continue
    files = sorted(directory.glob('*.qml'))
    if files:
        directory.chmod(directory.stat().st_mode | 0o200)
        descriptor.write_text('\n'.join(
            ('singleton ' if re.search(r'^\s*pragma\s+Singleton\b', path.read_text(), re.M) else '')
            + path.stem+' '+path.name for path in files)+'\n')

# Desktop keyboard selection stays inside the desktop focus scope, so text
# editing in rename fields and widgets retains its native Ctrl+A behavior.
p=root/'ui/desktop/DesktopLayer.qml'
s=p.read_text()
anchor='            Keys.onSpacePressed: function(event) {'
if s.count(anchor)!=1:
    raise ValueError('Desktop keyboard selection anchor changed')
s=s.replace(anchor,'''            Keys.onPressed: function(event) {
                if(event.matches(StandardKey.SelectAll) && DesktopFiles.renaming==="" && !WidgetState.typing){
                    const paths=[]
                    for(let i=0;i<DesktopFiles.model.count;i++)paths.push(DesktopFiles.model.get(i,"filePath"))
                    DesktopFiles.selectMany(paths);event.accepted=true
                }
            }
'''+anchor)
p.write_text(s)

# Keep monitor modes compact and preserve the native apply/persist backend.
p=root/'ui/settings/pages/MonitorsPage.qml'
s=p.read_text()
a=s.index('                Column {',s.index('property bool menuTransformOpen'))
z=s.index('                ConfigSlider {',a)
s=s[:a]+'''                RowLayout {
                    Layout.fillWidth:true;spacing:14
                    CFText{text:"Resolution";Layout.fillWidth:true;font.pixelSize:13;color:Theme.textPrimary}
                    TahoeCombo{
                        Layout.preferredWidth:200
                        model:Array.from(new Set((_monSection.modelData.availableModes || []).map(mode=>mode.split("@")[0])))
                        currentIndex:model.indexOf(_monSection.modelData.width+"x"+_monSection.modelData.height)
                        onActivated:index=>{
                            const resolution=model[index]
                            const modes=(_monSection.modelData.availableModes || []).filter(mode=>mode.split("@")[0]===resolution)
                            if(modes.length)_monSection.applyMode(modes.reduce((best,mode)=>parseFloat(mode.split("@")[1])>parseFloat(best.split("@")[1]) ? mode:best))
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth:true;spacing:14
                    CFText{text:"Refresh Rate";Layout.fillWidth:true;font.pixelSize:13;color:Theme.textPrimary}
                    TahoeCombo{
                        Layout.preferredWidth:200
                        property var modes:(_monSection.modelData.availableModes || []).filter(mode=>mode.split("@")[0]===_monSection.modelData.width+"x"+_monSection.modelData.height)
                        model:modes.map(mode=>parseFloat(mode.split("@")[1]).toFixed(2)+" Hz")
                        currentIndex:modes.findIndex(mode=>Math.abs(parseFloat(mode.split("@")[1])-_monSection.modelData.refreshRate)<.1)
                        onActivated:index=>_monSection.applyMode(modes[index])
                    }
                }

'''+s[z:]
s=s.replace('            property bool menuTransformOpen: false','''            function applyMode(mode){
                if(!mode)return
                MonitorState.applyAndPersist({output:modelData.name,mode:mode.replace("Hz",""),position:modelData.x+"x"+modelData.y,scale:modelData.scale})
            }
            property bool menuTransformOpen: false''')
# The compact selectors already display the current resolution.
a=s.index('                RowLayout {',s.index('property bool menuCmOpen'))
z=s.index('                RowLayout {',a+1)
s=s[:a]+s[z:]
p.write_text(s)

p=root/'ui/settings/pages/ControlCenterPage.qml'
s=p.read_text();a=s.index('    readonly property var _widgets:');z=s.index('    ContentSection {',a)
widgets=s[a:z]
p.write_text('''import QtQuick
import QtQuick.Layouts
import qs.services
import qs.components
import qs.settingsapp
import qs.ui.settings.widgets
ContentPage {
 id:root
'''+widgets+'''
 readonly property var groups:[
  {title:"Connectivity",ids:["wifiWidget","btWidget","adWidget","shareWidget"]},
  {title:"Sound & Display",ids:["musicWidget","volumeWidget","displayWidget","darkWidget","focusWidget"]},
  {title:"Tools",ids:["stageWidget","calcWidget","gameModeWidget","timerWidget","alarmWidget","stopwatchWidget"]}
 ]
 Repeater{
  model:root.groups
  delegate:SettingsCard{
   id:group;required property var modelData;title:modelData.title
   Repeater{
    model:group.modelData.ids.map(id=>root._widgets.find(widget=>widget.id===id)).filter(Boolean)
    delegate:RowLayout{
     id:entry;required property var modelData;required property int index
     Layout.fillWidth:true;spacing:12
     Item{Layout.preferredWidth:24;Layout.preferredHeight:24
      CFVI{anchors.fill:parent;visible:!!entry.modelData.icon;icon:entry.modelData.icon;gray:true}
      Text{anchors.centerIn:parent;visible:!entry.modelData.icon;text:entry.modelData.id==='calcWidget' ? '⌗':'◇';color:Theme.textPrimary;font.pixelSize:20}
     }
     SettingsRow{
      Layout.fillWidth:true;label:entry.modelData.name;kind:'switch'
      separator:entry.index<group.modelData.ids.length-1
      checked:ShellConfig.ccWidgetVisible(entry.modelData.id)
      available:!entry.modelData.locked
      onToggled:value=>ShellConfig.setCcWidgetVisible(entry.modelData.id,value)
     }
    }
   }
  }
 }
}
''')

# MouseArea consumes wheel events before an ancestor WheelHandler.
wheel_handler='''onWheel: function(event) {
            if(!(event.modifiers & Qt.ControlModifier)){event.accepted=false;return}
            const delta=event.angleDelta.y || event.pixelDelta.y
            if(delta){WidgetState.iconSize=Math.max(32,Math.min(128,WidgetState.iconSize+(delta>0 ? 4:-4)));event.accepted=true}
        }
        '''
for filename,anchor in [('ui/desktop/DesktopLayer.qml','                onPressed: function(mouse) {'),('ui/desktop/DesktopIcon.qml','        onPressed: function(mouse) {')]:
    p=root/filename;s=p.read_text();s=s.replace(anchor,wheel_handler+anchor,1);p.write_text(s)

(root/'services/MediaCaptureState.qml').write_text((here/'MediaCaptureState.qml').read_text())
(root/'services/capture-classifier.js').write_text((here/'capture-classifier.js').read_text())
p=root/'rosa/services/Privacy.qml';s=p.read_text().replace('import Quickshell', 'import QtQuick\nimport Quickshell',1).replace(' readonly property bool mic:', ' readonly property bool audio: Native.MediaCaptureState.audioActive\n readonly property bool screen: Native.MediaCaptureState.screenActive\n readonly property color indicatorColor: Native.MediaCaptureState.indicatorColor\n readonly property bool active: Native.MediaCaptureState.active\n readonly property bool mic:');p.write_text(s)
p=root/'rosa/overlays/IslandWindow.qml';s=p.read_text().replace('(Privacy.mic || Privacy.camera)','Privacy.active')
a=s.index('            readonly property color hue: privacy.cam');z=s.index('\n\n',a);s=s[:a]+'            readonly property color hue: Privacy.indicatorColor'+s[z:];p.write_text(s)
p=root/'ui/topbar/statusarea/systemtray/SystemTray.qml';s=p.read_text().replace('readonly property var allItems: SystemTray.items.values',"readonly property var allItems: SystemTray.items.values.filter(item=>!/kde.?connect/i.test([item.id,item.title,item.iconName].join(' ')))");p.write_text(s)
p=root/'ui/topbar/statusarea/controlcenter/ControlCenter.qml';s=p.read_text().replace('icon: "devices/smartphone.svg"\n                                    color: Theme.accent','icon: "devices/smartphone.svg"\n                                    color: Theme.ink(parent, false)')
s=s.replace('anchors.topMargin: 30','anchors.topMargin: MediaCaptureState.active ? 88:30',1)
anchor='                    property real showProgress: 0'
s=s.replace(anchor,'''                    BoxGlass {
                        visible:MediaCaptureState.active;backdrop:ccBackdrop;radius:20
                        x:0;y:-52;width:parent.width;height:44
                        RowLayout{anchors.fill:parent;anchors.leftMargin:16;anchors.rightMargin:16;spacing:10
                            Rectangle{Layout.preferredWidth:7;Layout.preferredHeight:7;radius:4;color:MediaCaptureState.indicatorColor}
                            Text{Layout.fillWidth:true;text:MediaCaptureState.summary;color:Theme.textPrimary;font.pixelSize:12;elide:Text.ElideRight}
                        }
                        MouseArea{anchors.fill:parent;onClicked:SettingsLauncher.open('privacy')}
                    }
'''+anchor,1);p.write_text(s)

# Position tweens must not trail behind the immediate geometry changes of zoom.
p=root/'services/WidgetState.qml'
s=p.read_text().replace('    property alias iconSize:','''    property bool desktopResizing:false
    Timer{id:desktopResizeIdle;interval:180;onTriggered:root.desktopResizing=false}
    function resizeDesktopIcons(size){
        root.desktopResizing=true;desktopResizeIdle.restart()
        root.iconSize=Math.max(32,Math.min(128,Math.round(size)))
    }
    property alias iconSize:''',1)
p.write_text(s)
for filename in ['ui/desktop/DesktopLayer.qml','ui/desktop/DesktopIcon.qml']:
    p=root/filename;s=p.read_text().replace('WidgetState.iconSize=Math.max(32,Math.min(128,WidgetState.iconSize+(delta>0 ? 4:-4)))','WidgetState.resizeDesktopIcons(WidgetState.iconSize+(delta>0 ? 4:-4))')
    if filename.endswith('DesktopLayer.qml'):
        s=s.replace('animate: stage.settled','animate: stage.settled && !WidgetState.desktopResizing')
    p.write_text(s)
p=root/'ui/settings/pages/DockPage.qml';s=p.read_text().replace('WidgetState.iconSize=Math.round(v)','WidgetState.resizeDesktopIcons(v)');p.write_text(s)
