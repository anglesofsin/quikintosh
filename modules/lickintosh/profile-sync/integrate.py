from pathlib import Path
import sys
root=Path(sys.argv[1]);here=Path(__file__).parent
for p in root.rglob('*'):
 if not p.is_symlink():p.chmod(p.stat().st_mode|0o200)
(root/'services/ProfileState.qml').write_text((here/'ProfileState.qml').read_text())
p=root/'services/qmldir';p.write_text(p.read_text()+'\nsingleton ProfileState ProfileState.qml\n')
(root/'tools/user-profile.py').write_text((here/'user-profile.py').read_text())
p=root/'ui/lockscreen/LockContext.qml';s=p.read_text();a=s.index('    property string avatarSource:');z=s.index('    property string currentText:',a)
s=s[:a]+'''    readonly property string displayName:ProfileState.displayName
    readonly property string avatarSource:ProfileState.avatarPath
    readonly property url avatarUrl:ProfileState.avatarUrl
    readonly property bool avatarDetectionDone:ProfileState.ready

'''+s[z:];p.write_text(s)
p=root/'ui/lockscreen/LockSurface.qml';s=p.read_text().replace('(Quickshell.env("USER") || "?").charAt(0).toUpperCase()','ProfileState.initial').replace('text: Quickshell.env("USER") || ""','text: ProfileState.displayName').replace('readonly property bool reduceMotion: ShellConfig.options.appearance.reduceMotion','readonly property bool reduceMotion: ShellConfig.options.appearance.reduceMotion || SettingsPreferences.accessibility.reduceMotion')
# Informational owner text is independent of authentication failures/status.
end=s.rfind('\n    }\n}')
s=s[:end]+'''
        Text{
            anchors.horizontalCenter:parent.horizontalCenter
            anchors.bottom:parent.bottom;anchors.bottomMargin:20
            width:Math.min(parent.width-64,640)
            visible:ShellConfig.options.lockscreen.showOwnerMessage && text.length>0
            text:ShellConfig.options.lockscreen.ownerMessage
            textFormat:Text.PlainText;wrapMode:Text.WordWrap;maximumLineCount:2;elide:Text.ElideRight
            horizontalAlignment:Text.AlignHCenter;color:'#ddffffff';font.family:'SF Pro Text';font.pixelSize:13
        }
'''+s[end:];p.write_text(s)
p=root/'services/ShellConfig.qml';s=p.read_text().replace('            property JsonObject lockscreen: JsonObject {','''            property JsonObject lockscreen: JsonObject {
                property bool showOwnerMessage:false
                property string ownerMessage:""''');p.write_text(s)
p=root/'ui/settings/pages/LockScreenPage.qml';s=p.read_text().replace('    readonly property var cfg:', '''    ContentSection{title:"Lock Screen Message"
        ConfigSwitch{text:"Show a message when locked";checked:root.cfg.showOwnerMessage;onToggled:value=>root.cfg.showOwnerMessage=value}
        TahoeField{visible:root.cfg.showOwnerMessage;Layout.fillWidth:true;text:root.cfg.ownerMessage;maximumLength:160;placeholderText:"Message";onEditingFinished:root.cfg.ownerMessage=text}
    }
    readonly property var cfg:''');p.write_text(s)
p=root/'services/AppearanceState.qml';s=p.read_text().replace("readonly property bool tinted:options.iconStyle==='tinted'","readonly property bool tinted:WidgetState.widgetStyle==='tinted'");p.write_text(s)
# Account page and sidebar share lock-screen normalization and system fallbacks.
p=root/'settings.qml';s=p.read_text().replace("SettingsPreferences.profile.avatar ? QuickLookState.urlFor(SettingsPreferences.profile.avatar):Quickshell.shellDir+'/assets/icons/settings/user.svg'", "ProfileState.avatarUrl || Quickshell.shellDir+'/assets/icons/settings/user.svg'").replace("SettingsPreferences.profile.displayName || SettingsState.data.system?.fullName || 'Your Account'","ProfileState.displayName || 'Your Account'");p.write_text(s)
p=root/'settingsapp/SettingsContent.qml';s=p.read_text().replace("(SettingsPreferences.profile.avatar || root.stateData.system?.avatar) ? QuickLookState.urlFor(SettingsPreferences.profile.avatar || root.stateData.system.avatar):IconResolver.byName('avatar-default')","ProfileState.avatarUrl || IconResolver.byName('avatar-default')").replace("SettingsPreferences.profile.displayName || root.stateData.system?.fullName || 'Your Account'","ProfileState.displayName || 'Your Account'");p.write_text(s)
