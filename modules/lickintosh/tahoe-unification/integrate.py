from pathlib import Path
import sys
root=Path(sys.argv[1])
def save(name,s):
 p=root/name;p.chmod(p.stat().st_mode|0o200);p.write_text(s)
p=root/'services/ShellConfig.qml';s=p.read_text().replace('property JsonObject appearance: JsonObject {','''property JsonObject appearance: JsonObject {
                property string highlightMode:"accent"
                property string highlightColor:"#0a84ff"
                property string scrollbarVisibility:"automatic"
                property string sidebarSize:"medium"''',1);save('services/ShellConfig.qml',s)
p=root/'services/AppearanceState.qml';s=p.read_text().replace(' property var palette:', ''' readonly property color highlight:options.highlightMode==='custom' ? options.highlightColor:Theme.accent
 readonly property int sidebarIconSize:options.sidebarSize==='small' ? 19:options.sidebarSize==='large' ? 27:23
 readonly property int sidebarFontSize:options.sidebarSize==='small' ? 12:options.sidebarSize==='large' ? 15:13
 property var palette:''');save('services/AppearanceState.qml',s)
p=root/'ui/settings/pages/AppearanceControls.qml';s=p.read_text();z=s.rfind('}');s=s[:z]+'''
 SettingsCard{title:'Interface'
  SettingsRow{label:'Text highlight color';kind:'choice';choices:['Accent','Custom'];selection:ShellConfig.options.appearance.highlightMode==='custom' ? 1:0;onPicked:index=>ShellConfig.options.appearance.highlightMode=index ? 'custom':'accent'}
  ColorSetting{visible:ShellConfig.options.appearance.highlightMode==='custom';label:'Highlight color';value:ShellConfig.options.appearance.highlightColor;onPicked:value=>ShellConfig.options.appearance.highlightColor=String(value)}
  SettingsRow{label:'Sidebar size';kind:'choice';choices:['Small','Medium','Large'];selection:['small','medium','large'].indexOf(ShellConfig.options.appearance.sidebarSize);onPicked:index=>ShellConfig.options.appearance.sidebarSize=['small','medium','large'][index]}
  SettingsRow{label:'Show scroll bars';kind:'choice';choices:['Automatically','When scrolling','Always'];selection:['automatic','scrolling','always'].indexOf(ShellConfig.options.appearance.scrollbarVisibility);separator:false;onPicked:index=>ShellConfig.options.appearance.scrollbarVisibility=['automatic','scrolling','always'][index]}
 }
'''+s[z:];save('ui/settings/pages/AppearanceControls.qml',s)
for name in ['components/TahoeField.qml','components/TahoeTextArea.qml']:
 p=root/name
 if not p.exists():continue
 s=p.read_text().replace('selectionColor:Theme.accent','selectionColor:AppearanceState.highlight').replace("selectedTextColor:'white'","selectedTextColor:Theme.luma(AppearanceState.highlight)>.5 ? '#17171a':'#ffffff'");save(name,s)
p=root/'settings.qml';s=p.read_text().replace("? 40:23","? 40:AppearanceState.sidebarIconSize").replace("font.pixelSize:13;font.weight:modelData.id==='account'","font.pixelSize:AppearanceState.sidebarFontSize;font.weight:modelData.id==='account'");save('settings.qml',s)
for name in ['ui/settings/widgets/ContentPage.qml','settings.qml']:
 p=root/name;s=p.read_text().replace('policy: ScrollBar.AsNeeded',"policy: ShellConfig.options.appearance.scrollbarVisibility==='always' ? ScrollBar.AlwaysOn:ScrollBar.AsNeeded").replace('policy:ScrollBar.AsNeeded',"policy:ShellConfig.options.appearance.scrollbarVisibility==='always' ? ScrollBar.AlwaysOn:ScrollBar.AsNeeded")
 if name.endswith('ContentPage.qml'):s=s.replace('opacity: _vbar.pressed ? 0.9 : (_vbar.hovered ? 0.7 : 0.0)',"opacity: ShellConfig.options.appearance.scrollbarVisibility==='always' ? 0.7 : _vbar.pressed || root.contentItem.moving ? 0.9 : ShellConfig.options.appearance.scrollbarVisibility!=='scrolling' && _vbar.hovered ? 0.7:0.0")
 save(name,s)
