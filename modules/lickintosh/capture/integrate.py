"""Native Quickshot-style selection/editor, integrated with existing shell IPC."""
from pathlib import Path
import shutil,sys
root=Path(sys.argv[1]);here=Path(__file__).parent

def edit(name,old,new):
 p=root/name;s=p.read_text()
 if s.count(old)!=1:raise ValueError(f'Capture anchor {name}: {old[:70]} ({s.count(old)})')
 p.write_text(s.replace(old,new,1))
shutil.copytree(here,root/'capture',ignore=shutil.ignore_patterns('__pycache__','test_*','integrate.py'))
for directory in [root/'capture',root/'capture/assets']:directory.chmod(0o755)
s=(here/'CaptureState.qml').read_text().replace('@CAPTURE_PYTHON@',sys.argv[2]);(root/'services/CaptureState.qml').write_text(s)
(root/'capture/CaptureState.qml').unlink()
p=root/'services/qmldir';p.write_text(p.read_text()+'\nsingleton CaptureState CaptureState.qml\n')
(root/'capture/qmldir').write_text('\n'.join(p.stem+' '+p.name for p in (root/'capture').glob('*.qml'))+'\n')
shutil.copyfile(here/'CapturePage.qml',root/'ui/settings/pages/CapturePage.qml')
edit('services/ShellConfig.qml','            property JsonObject topbar: JsonObject {','''            property JsonObject capture: JsonObject {
                property bool recordSystemAudio:false
                property bool recordMic:false
                property bool recordCursor:true
                property int recordMaxSeconds:120
                property string videoDirectory:"~/Videos/Screencasts"
                property string translateLanguage:"pt"
                property bool autoSave:true
                property string directory:"~/Desktop"
                property string filenameTemplate:"Screenshot_{datetime}_{w}x{h}.png"
                property string feedback:"notification"
                property bool magnifier:true
                property string ocrLanguages:"eng+por"
                property string lastSaveDirectory:""
            }
            property JsonObject topbar: JsonObject {''')
edit('shell.qml','    id: appRoot','''    id: appRoot
    CaptureIntegration {
        enabled:appRoot.interfaceShown
        locked:lockScreen.locked
        onCaptured: {appRoot.spotlightOpened=false;appRoot.aiOpened=false;appRoot.ccOpened=false;appRoot.notifCenterOpened=false;appRoot.appleMenuOpened=false;appRoot.wifiOpened=false;appRoot.bluetoothOpened=false;appRoot.batteryOpened=false;appRoot.volumeOpened=false;NotchState.close()}
    }''')
p=root/'shell.qml';p.write_text('import qs.capture\n'+p.read_text())
edit('settings.qml','{ name: "Top Bar",','{ name: "Screenshots", icon: "settings/display.svg", component: "CapturePage", implemented: true },\n                { name: "Top Bar",')
edit('settings.qml','case "TopBarPage":    return _topbarComp','case "CapturePage": return _captureComp\n                                case "TopBarPage":    return _topbarComp')
edit('settings.qml','    Component { id: _topbarComp;','    Component { id: _captureComp; CapturePage {} }\n    Component { id: _topbarComp;')

# Requests arriving during the Spotlight exit animation must reopen and reclaim
# keyboard focus instead of applying a tab to a window that is already closing.
p=root/'ui/topbar/statusarea/spotlight/SpotlightWindow.qml';s=p.read_text().replace('else root.applyPending()', 'else {if(spotlightLoader.item)spotlightLoader.item.reopen();root.applyPending()}')
s=s.replace('if (action === "clipboard") { root.refreshClipHistory();', 'if (action === "clipboard") { searchField.text="";root.refreshClipHistory();')
s=s.replace('            root.clipHistory = out','            root.clipHistory = out\n            if(spotlightLoader.item && root.opened)spotlightLoader.item.refreshClipboardIfVisible()')
s=s.replace('                function refreshClipboard(query) {','                function refreshClipboardIfVisible(){if(selectedAction === "clipboard")refreshClipboard(searchField.text)}\n                function refreshClipboard(query) {')
p.write_text(s)

edit('shell.qml','    id: appRoot','''    id: appRoot
    GlobalShortcut {appid:"lickintosh";name:"clipboard";description:"Open clipboard history";onPressed:{LauncherState.pendingAction="clipboard";LauncherState.requested()}}''')

# Clipboard text is data, not styled HTML (which can make rich clipboard entries
# render invisibly or attempt to resolve embedded images).
p=root/'ui/topbar/statusarea/spotlight/SpotlightResults.qml';s=p.read_text().replace('text:           I18n.tr(row.modelData.name || row.modelData.title || "")','textFormat:Text.PlainText\n            text:           I18n.tr(row.modelData.name || row.modelData.title || "")');p.write_text(s)

import subprocess
subprocess.run([sys.executable,str(here/"island.py"),str(root)],check=True)
