from pathlib import Path
import sys
r=Path(sys.argv[1]);h=Path(__file__).parent
def save(n,s):
 p=r/n;p.chmod(p.stat().st_mode|0o200);p.write_text(s)
for n in ['IconTreatment.qml','icon-style.frag']:(r/'components'/n).write_text((h/n).read_text())
p=r/'components/qmldir';save('components/qmldir',p.read_text()+'\nIconTreatment IconTreatment.qml\n')
p=r/'services/ShellConfig.qml';s=p.read_text().replace('property string iconTintMode:', '''property string iconAppearance:"auto"
                property string iconPaletteRole:"primary"
                property string iconLightColor:"#0061a4"
                property string iconDarkColor:"#9ecaff"
                property real iconTreatmentStrength:1.0
                property string iconTintMode:''',1);save('services/ShellConfig.qml',s)
p=r/'services/AppearanceState.qml';s=p.read_text();a=s.index(' readonly property color iconColor:');z=s.index(' function syncAccent',a)
s=s[:a]+''' readonly property string iconStyle:WidgetState.widgetStyle
 readonly property bool iconDark:iconStyle==='dark' || options.iconAppearance==='dark' || (options.iconAppearance==='auto' && Theme.isDark)
 readonly property var iconPalette:palette[iconDark ? 'dark':'light'] || ({})
 readonly property string paletteRole:options.iconPaletteRole || 'primary'
 readonly property color iconColor:options.iconTintMode==='auto' ? (iconPalette[paletteRole] || wallpaperAccent):(iconDark ? options.iconDarkColor:options.iconLightColor)
 readonly property bool tinted:iconStyle==='tinted'
 readonly property real treatment:tinted ? 3:iconStyle==='clear' ? 2:(iconStyle==='dark' || (['auto','color'].includes(iconStyle) && iconDark)) ? 1:0
 readonly property real strength:options.iconTreatmentStrength
 readonly property color iconLow:tinted ? (options.iconTintMode==='auto' ? (iconPalette['on_'+paletteRole+'_container'] || iconColor):(iconDark ? iconColor:Qt.darker(iconColor,2.5))):(iconPalette.surface_container_high || (iconDark ? '#242428':'#e4e4e9'))
 readonly property color iconHigh:tinted ? (options.iconTintMode==='auto' ? (iconPalette[paletteRole+'_container'] || iconColor):(iconDark ? Qt.darker(iconColor,3.5):Qt.lighter(iconColor,2.5))):(iconPalette.on_surface || (iconDark ? '#eeeeef':'#202024'))
'''+s[z:];s=s.replace('Theme.isDark','!Theme.isLight');save('services/AppearanceState.qml',s)
p=r/'tahoedock/DockTile.qml';s=p.read_text();a=s.index('   layer.enabled:AppearanceState.');z=s.index('\n  }',a);s=s[:a]+'''   layer.enabled:AppearanceState.treatment>0
   layer.effect:IconTreatment{}'''+s[z:];save('tahoedock/DockTile.qml',('import qs.components\n' if 'import qs.components\n' not in s else '')+s)
p=r/'ui/desktop/DesktopIcon.qml';s=p.read_text();a=s.index('        layer.enabled:AppearanceState.tinted');z=s.index('\n',s.index('layer.effect:',a));s=s[:a]+'''        layer.enabled:AppearanceState.treatment>0 && !root.thumbnail
        layer.effect:IconTreatment{}'''+s[z:];
if 'import qs.components\n' not in s:s='import qs.components\n'+s
save('ui/desktop/DesktopIcon.qml',s)
# App launcher and Spotlight use the identical treatment, excluding media.
p=r/'ui/dock/Dock.qml';s=p.read_text();a=s.index('            Image {',s.index('            Image {'))
start=s.index('                layer.enabled:',a);end=s.index('\n                }',start)+len('\n                }');s=s[:start]+'                layer.enabled:AppearanceState.treatment>0\n                layer.effect:IconTreatment{}'+s[end:]
if 'import qs.components\n' not in s:s='import qs.components\n'+s
save('ui/dock/Dock.qml',s)
p=r/'ui/topbar/statusarea/spotlight/SpotlightResults.qml';s=p.read_text().replace('            Image {','''            Image {
                layer.enabled:AppearanceState.treatment>0 && row.isApp && !row.modelData.isImage && !row.modelData.clipImage && !row.modelData.isWallpaper
                layer.effect:IconTreatment{}''',1)
if 'import qs.components\n' not in s:s='import qs.components\n'+s
save('ui/topbar/statusarea/spotlight/SpotlightResults.qml',s)
p=r/'ui/settings/pages/AppearanceControls.qml';s=p.read_text();a=s.index("  SettingsRow{label:'Style'");z=s.index("\n }\n SettingsCard{title:'Liquid Glass'",a)
s=s[:a]+'''  SettingsRow{label:'Style';kind:'choice';choices:['Automatic','Default','Dark','Clear','Tinted','Transparent widgets'];selection:['auto','color','dark','clear','tinted','transparent'].indexOf(WidgetState.widgetStyle);onPicked:index=>WidgetState.widgetStyle=['auto','color','dark','clear','tinted','transparent'][index]}
  SettingsRow{label:'Icon appearance';kind:'choice';choices:['Automatic','Light','Dark'];selection:['auto','light','dark'].indexOf(ShellConfig.options.appearance.iconAppearance);onPicked:index=>ShellConfig.options.appearance.iconAppearance=['auto','light','dark'][index]}
  SettingsRow{visible:AppearanceState.tinted;label:'Tint color';kind:'choice';choices:['Matugen palette','Custom'];selection:ShellConfig.options.appearance.iconTintMode==='auto' ? 0:1;onPicked:index=>ShellConfig.options.appearance.iconTintMode=index===0 ? 'auto':'manual'}
  SettingsRow{visible:AppearanceState.tinted && ShellConfig.options.appearance.iconTintMode==='auto';label:'Palette color';kind:'choice';choices:['Primary','Secondary','Tertiary'];selection:['primary','secondary','tertiary'].indexOf(ShellConfig.options.appearance.iconPaletteRole);onPicked:index=>ShellConfig.options.appearance.iconPaletteRole=['primary','secondary','tertiary'][index]}
  ColorSetting{visible:AppearanceState.tinted && ShellConfig.options.appearance.iconTintMode==='manual';label:'Light tint';value:ShellConfig.options.appearance.iconLightColor;onPicked:value=>ShellConfig.options.appearance.iconLightColor=String(value)}
  ColorSetting{visible:AppearanceState.tinted && ShellConfig.options.appearance.iconTintMode==='manual';label:'Dark tint';value:ShellConfig.options.appearance.iconDarkColor;onPicked:value=>ShellConfig.options.appearance.iconDarkColor=String(value)}
  SettingsRow{label:'Style intensity';kind:'slider';number:ShellConfig.options.appearance.iconTreatmentStrength;minimum:0;maximum:1;step:.05;value:Math.round(ShellConfig.options.appearance.iconTreatmentStrength*100)+'%';separator:false;onCommitted:value=>ShellConfig.options.appearance.iconTreatmentStrength=value}
'''+s[z:];save('ui/settings/pages/AppearanceControls.qml',s)
# Widget contrast follows independently selected light/dark icon appearance.
p=r/'ui/widgets/WidgetPalette.qml';s=p.read_text();a=s.index('    readonly property bool light:');z=s.index('    readonly property color primary:',a);s=s[:a]+'''    readonly property bool light:root.theme==='light' || (!['light','dark'].includes(root.theme) && !AppearanceState.iconDark)
    readonly property bool dark:!light
    readonly property bool glass:root.theme==='glass' || root.theme==='clear'

'''+s[z:];save('ui/widgets/WidgetPalette.qml',s)
# Screenshot controls use system accent; annotation paint colors remain user colors.
for p in (r/'capture').glob('*.qml') if (r/'capture').exists() else []:pass
for p in r.rglob('ToolButton.qml'):
 if 'capture' not in str(p).lower():continue
# Actual capture module is installed under ui/capture.
for p in r.rglob('*.qml'):
 if '/capture/' not in str(p):continue
 s=p.read_text();original=s
 for color in ['#ff8252','#ff6b35','#ff9a70','#ff855a','#eeff6b35','#ffa888']:s=s.replace("'"+color+"'",'Theme.accent').replace('"'+color+'"','Theme.accent')
 s=s.replace("'#66b8542e'",'Qt.rgba(Theme.accent.r,Theme.accent.g,Theme.accent.b,.3)')
 if s!=original:
  if 'import qs.services\n' not in s:s='import qs.services\n'+s
  save(str(p.relative_to(r)),s)
p=r/'ui/widgets/WidgetPalette.qml';s=p.read_text().replace('readonly property color primary: root.light ?', 'readonly property color primary: root.theme==="tinted" ? AppearanceState.iconLow:root.light ?').replace('readonly property color background: root.light ?', 'readonly property color background: root.theme==="tinted" ? AppearanceState.iconHigh:root.light ?');save('ui/widgets/WidgetPalette.qml',s)
