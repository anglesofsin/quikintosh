"""Host-native Arch PAM, shell scaling and Portuguese language selection."""
from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1])
source = Path(__file__).parent
shutil.copy(Path(sys.argv[2]) if len(sys.argv)>2 else source / 'arch-pam.py', root / 'tools/arch-pam.py')
p = root / 'services/ShellConfig.qml'
s = p.read_text().replace('property string language: "auto"', 'property string language: "auto"\n                property real shellScale: 1.0')
p.write_text(s)
p = root / 'ui/lockscreen/LockContext.qml'
s = p.read_text().replace('    property bool unlockInProgress: false', '''    readonly property bool nativeArchPam: Quickshell.env("QUICKINTOSH_PLATFORM") === "arch"
    property bool unlockInProgress: false
    property bool authServiceError: false

    Process {
        id: nativeAuth
        stdinEnabled: true
        environment: ({LD_LIBRARY_PATH:null, LD_PRELOAD:null, PYTHONPATH:null, PYTHONHOME:null})
        command: ["/usr/bin/python3", "-I",
                  Quickshell.shellPath("tools/arch-pam.py")]
        property bool received: false
        onStarted: { received = false; write(JSON.stringify({password:root.currentText}) + "\\n") }
        stdout: SplitParser { onRead: line => {
            try {
                const result = JSON.parse(line)
                nativeAuth.received = true
                root.unlockInProgress = false
                root.currentText = ""
                if (result.success === true) {
                    root.failCount = 0; root.lockMessage = ""; root.unlocking()
                } else {
                    root.authServiceError = result.kind === "service-error"
                    root.lockMessage = root.authServiceError ? I18n.tr("Authentication service unavailable. Run Quickintosh Doctor.") : (result.message || "")
                    root.failCount += 1; root.showFailure = true; root.failed()
                }
            } catch (error) { console.warn("Invalid host PAM response") }
        } }
        onExited: code => {
            if (root.unlockInProgress && !received) {
                root.unlockInProgress = false; root.currentText = ""; root.authServiceError = true
                root.lockMessage = I18n.tr("Authentication service unavailable. Run Quickintosh Doctor.")
                root.showFailure = true; root.failed()
            }
        }
    }''')
s = s.replace('        pam.start()', '''        root.authServiceError = false
        root.lockMessage = ""
        if (root.nativeArchPam) nativeAuth.running = true
        else if (!pam.start()) {
            root.unlockInProgress = false; root.authServiceError = true
            root.lockMessage = I18n.tr("Authentication service unavailable. Run Quickintosh Doctor.")
        }''')
s = s.replace('        pam.abort()', '        nativeAuth.running = false\n        pam.abort()')
s = s.replace('        onMessageChanged: {', '''        onError: error => {
            root.authServiceError = true
            root.lockMessage = I18n.tr("Authentication service unavailable. Run Quickintosh Doctor.")
        }
        onMessageChanged: {''', 1)
s = s.replace('        && root.fprintAvailable', '        && !root.nativeArchPam\n        && root.fprintAvailable')
s = s.replace('            respond(root.currentText)', '            respond(responseVisible ? root._user : root.currentText)')
p.write_text(s)
p = root / 'settingsapp/SettingsContent.qml'
s = p.read_text().replace("['Automatic','English','Français','Español']", "['Automatic','English','Français','Español','Português (Brasil)']").replace("['auto','en','fr','es']", "['auto','en','fr','es','pt_BR']")
# This applies to the final Appearance body, including the unified glass page.
needle = "  return result\n }\n function apply(row,value)"
assert needle in s
s = s.replace(needle, '''  if(pageId==='appearance')result.push(card('Interface Scale',[
   choice('Shell Scale',['75%','90%','100%','110%','125%','150%','175%','200%'],[.75,.9,1,1.1,1.25,1.5,1.75,2].indexOf(ShellConfig.options.general.shellScale),'shell-scale'),
   button('Apply Shell Scale','Apply & Reload','apply-shell-scale')
  ],'Reloads only the shell. Application and monitor scaling are unchanged.'))
  return result
 }
 function apply(row,value)''')
s = s.replace('  const name=row.action', '''  const name=row.action
  if(name==='shell-scale'){ShellConfig.options.general.shellScale=[.75,.9,1,1.1,1.25,1.5,1.75,2][value];return}
  if(name==='apply-shell-scale'){
   if(SettingsPreferences.locked){return}
   Quickshell.execDetached(['systemd-run','--user','--collect','--unit=quickintosh-scale-'+Date.now(),'--','sh','-c','sleep 0.7; rice-shell restart']);return
  }''')
p.write_text(s)
p = root / 'services/I18n.qml'
s = p.read_text().replace('["fr", "en", "es"]', '["fr", "en", "es", "pt_BR"]')
s = s.replace('return root.supported.indexOf(code) !== -1 ? code : "en"', 'return code === "pt" ? "pt_BR" : root.supported.indexOf(code) !== -1 ? code : "en"')
s = s.replace('root.supported.indexOf(root.setting) !== -1 ? root.setting', '(root.setting === "pt" || root.setting === "pt-BR") ? "pt_BR" : root.supported.indexOf(root.setting) !== -1 ? root.setting')
p.write_text(s)

# Appearance is served by the unified legacy page in the exported desktop.
p = root / 'ui/settings/pages/LegacyAppearancePage.qml'
s = p.read_text()
scale_section = """
    ContentSection {
        title: I18n.tr("Interface Scale")
        RowLayout {
            Layout.fillWidth: true
            CFText { text: I18n.tr("Shell Scale"); color: Theme.textPrimary; Layout.fillWidth: true }
            TahoeCombo {
                model: ["75%", "90%", "100%", "110%", "125%", "150%", "175%", "200%"]
                currentIndex: [.75,.9,1,1.1,1.25,1.5,1.75,2].indexOf(ShellConfig.options.general.shellScale)
                onActivated: index => ShellConfig.options.general.shellScale=[.75,.9,1,1.1,1.25,1.5,1.75,2][index]
            }
            TahoeButton {
                text: I18n.tr("Apply & Reload")
                onClicked: Quickshell.execDetached(["systemd-run","--user","--collect","--unit=quickintosh-scale-"+Date.now(),"--","sh","-c","sleep 0.7; rice-shell restart"])
            }
        }
    }
"""
s = s.replace('    ColumnLayout{Layout.fillWidth:true;visible:root.advanced;', scale_section+'    ColumnLayout{Layout.fillWidth:true;visible:root.advanced;', 1)
if 'import Quickshell\n' not in s:
    s = s.replace('import QtQuick\n','import QtQuick\nimport Quickshell\n',1)
p.write_text(s)
