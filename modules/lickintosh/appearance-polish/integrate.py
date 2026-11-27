from pathlib import Path
import sys,json,re
root=Path(sys.argv[1]);here=Path(__file__).parent
# Earlier integrations copy some files with read-only store permissions.
for candidate in root.rglob('*'):
 if not candidate.is_symlink():
  candidate.chmod(candidate.stat().st_mode | 0o200)

def edit(name,before,after):
 p=root/name;s=p.read_text()
 if s.count(before)!=1:raise ValueError(f'Appearance anchor {name}: {before[:70]} ({s.count(before)})')
 p.write_text(s.replace(before,after,1))
for name,directory in [('ColorSetting.qml','components'),('AppearanceState.qml','services'),('WeatherPage.qml','settingsapp'),('AiSettingsPage.qml','ui/settings/pages')]:
 (root/directory/name).write_text((here/name).read_text())
 if name!='AiSettingsPage.qml':
  p=root/directory/'qmldir';p.write_text(p.read_text()+'\n'+('singleton ' if name=='AppearanceState.qml' else '')+Path(name).stem+' '+name+'\n')
edit('services/ShellConfig.qml','            property JsonObject appearance: JsonObject {','''            property JsonObject appearance: JsonObject {
                property string accentMode:"manual"
                property string iconStyle:"color"
                property string iconTintMode:"auto"
                property string iconTintColor:"#0a84ff"''')
edit('services/ShellConfig.qml','            property JsonObject topbar: JsonObject {','''            property JsonObject topbar: JsonObject {
                property bool backgroundEnabled:false
                property string backgroundColor:"#242428"
                property real backgroundOpacity:0.65''')
# Keep the clock hit target inside its own slot, and do not reserve an empty badge.
edit('ui/topbar/statusarea/StatusArea.qml','_clock.implicitWidth + (ShellConfig.options.topbar.clockBadgeVisible ? 34 : 0)','_clock.implicitWidth')
edit('ui/topbar/statusarea/StatusArea.qml','                anchors.left:           _clock.right','                anchors.right:          _clock.right')
edit('ui/topbar/statusarea/StatusArea.qml','                anchors.leftMargin:     4','                anchors.top:            _clock.bottom')
# Clock implicit dimensions must be available to the outer click target.
edit('ui/topbar/statusarea/StatusArea.qml','            implicitHeight: _clock.implicitHeight','            implicitHeight: Math.max(24,_clock.implicitHeight)')
# AI retains its branded color, and the platform logo follows the menu foreground.
p=root/'components/BarLogo.qml';s=p.read_text().replace("options.logoType==='text'","options.logoType==='text' || options.logoType==='apple'").replace('text:root.options.logoText',"text:root.options.logoType==='apple' ? '\uf179':root.options.logoText");p.write_text(s)
p=root/'ui/settings/pages/TopBarPage.qml';s=p.read_text().replace('["Linux","Text or symbol","Custom image"]','["Linux","Apple","Text or symbol","Custom image"]').replace('["linux","text","image"]','["linux","apple","text","image"]')
# Replace raw hexadecimal fields with the same reusable picker.
for prop,label in [('foregroundColor','Text and icons'),('logoColor','Logo color')]:
 pattern=r'        TahoeField\s*\{[^{}]*(?:validator:RegularExpressionValidator\s*\{[^{}]*\}[^{}]*)?\n?\s*onEditingFinished:[^\n]+\}'
 # Locate the field by its ShellConfig property, then balance braces.
 start=s.find('        TahoeField',s.find('title: "Menu bar colors"'))
 candidates=list(re.finditer(r'\bTahoeField\s*\{',s))
 for m in reversed(candidates):
  depth=0;end=m.end()-1
  for i in range(end,len(s)):
   if s[i]=='{':depth+=1
   elif s[i]=='}':
    depth-=1
    if depth==0:end=i+1;break
  body=s[m.start():end]
  if 'text:ShellConfig.options.topbar.'+prop not in body:continue
  condition='ShellConfig.options.topbar.foregroundMode==="custom"' if prop=='foregroundColor' else 'ShellConfig.options.topbar.logoColorMode==="custom"'
  s=s[:m.start()]+f'ColorSetting{{visible:{condition};label:"{label}";value:ShellConfig.options.topbar.{prop};onPicked:value=>ShellConfig.options.topbar.{prop}=String(value)}}'+s[end:]
s=s.replace('    id: root','''    id: root
    ContentSection{title:"Menu bar background"
        ConfigSwitch{text:"Show background";checked:ShellConfig.options.topbar.backgroundEnabled;onToggled:value=>ShellConfig.options.topbar.backgroundEnabled=value}
        ColorSetting{visible:ShellConfig.options.topbar.backgroundEnabled;label:"Background color";value:ShellConfig.options.topbar.backgroundColor;onPicked:value=>ShellConfig.options.topbar.backgroundColor=String(value)}
        ConfigSlider{visible:ShellConfig.options.topbar.backgroundEnabled;text:"Opacity";from:0.1;to:1;decimals:2;value:ShellConfig.options.topbar.backgroundOpacity;onMoved:value=>ShellConfig.options.topbar.backgroundOpacity=value}
    }''',1);p.write_text(s)
# Transparent is the default; background is painted only in the actual bar.
edit('shell.qml','            TopBar {\n                id: _topBarItem','''            Rectangle {
                anchors.fill:_topBarItem
                visible:ShellConfig.options.topbar.backgroundEnabled
                color:ShellConfig.options.topbar.backgroundColor
                opacity:ShellConfig.options.topbar.backgroundOpacity
            }
            TopBar {
                id: _topBarItem''')
# Tint app/folder glyphs, never photographs or media previews.
p=root/'tahoedock/DockTile.qml';s=p.read_text().replace('layer.enabled:ShellConfig.options.dockAppearance.monochromeIcons || ShellConfig.options.dockAppearance.iconTint','layer.enabled:AppearanceState.tinted || ShellConfig.options.dockAppearance.monochromeIcons || ShellConfig.options.dockAppearance.iconTint').replace("saturation:ShellConfig.options.dockAppearance.monochromeIcons ? -1 : 0","saturation:AppearanceState.tinted || ShellConfig.options.dockAppearance.monochromeIcons ? -1 : 0").replace('colorization:ShellConfig.options.dockAppearance.iconTint ? ShellConfig.options.dockAppearance.iconTintStrength : 0','colorization:AppearanceState.tinted ? 1:ShellConfig.options.dockAppearance.iconTint ? ShellConfig.options.dockAppearance.iconTintStrength : 0').replace('colorizationColor:ShellConfig.options.dockAppearance.iconTintColor','colorizationColor:AppearanceState.tinted ? AppearanceState.iconColor:ShellConfig.options.dockAppearance.iconTintColor');p.write_text(s)
p=root/'ui/desktop/DesktopIcon.qml';s=p.read_text();s='import QtQuick.Effects\n'+s;s=s.replace('        id: glyph','''        id: glyph
        layer.enabled:AppearanceState.tinted && !root.thumbnail
        layer.effect:MultiEffect{saturation:-1;colorization:1;colorizationColor:AppearanceState.iconColor}''');p.write_text(s)
# Automatic widget tint uses the same matugen palette as icons.
p=root/'services/WidgetState.qml';s=p.read_text().replace('    property alias widgetTint: widgetsAdapter.widgetTint','''    readonly property color effectiveWidgetTint:AppearanceState.iconColor
    property alias widgetTint: widgetsAdapter.widgetTint''');p.write_text(s)
for p in (root/'ui/widgets').rglob('*.qml'):
 s=p.read_text().replace('WidgetState.widgetTint','WidgetState.effectiveWidgetTint');p.write_text(s)
# Shared appearance settings replace the previous partial dock-only toggle.
p=root/'settingsapp/SettingsContent.qml';s=p.read_text().replace("row('Accent Color','field',{value:String(Theme.accent),action:'accent',description:'A hexadecimal color, for example #0a84ff.'})", "choice('Accent Color',['Wallpaper','Custom'],ShellConfig.options.appearance.accentMode==='auto' ? 0:1,'accent-source')")
s=s.replace("toggle('Tint Dock Icons',ShellConfig.options.dockAppearance.iconTint,'dock-tint'),nav('glass')", "choice('Tint Color',['Wallpaper','Custom'],ShellConfig.options.appearance.iconTintMode==='auto' ? 0:1,'icon-source'),nav('glass')")
s=s.replace("  if(name==='accent'){", "  if(name==='accent-source'){ShellConfig.options.appearance.accentMode=value===0 ? 'auto':'manual';return}\n  if(name==='icon-style'){ShellConfig.options.appearance.iconStyle=value===1 ? 'tinted':'color';return}\n  if(name==='icon-source'){ShellConfig.options.appearance.iconTintMode=value===0 ? 'auto':'manual';return}\n  if(name==='accent'){")
s=s.replace('  BusyIndicator{Layout.alignment:', '''  ColorSetting{visible:root.pageId==='appearance' && ShellConfig.options.appearance.accentMode==='manual';label:'Accent color';value:Theme.accent;onPicked:value=>Theme.setAccent(String(value))}
  ColorSetting{visible:root.pageId==='appearance' && ShellConfig.options.appearance.iconStyle==='tinted' && ShellConfig.options.appearance.iconTintMode==='manual';label:'Icon tint';value:ShellConfig.options.appearance.iconTintColor;onPicked:value=>ShellConfig.options.appearance.iconTintColor=String(value)}
  BusyIndicator{Layout.alignment:''');p.write_text(s)
# Weather has one saved location, owned by a general Settings page. No city is
# printed in status messages or diagnostics.
p=root/'ui/settings/pages/RosaPage.qml';s=p.read_text();start=s.index('        RowLayout {\n            Layout.fillWidth:true\n            CFText{Layout.fillWidth:true;text:"Weather location"');end=s.index('\n    }',start);s=s[:start]+'''        TahoeButton{text:"Weather Settings…";onClicked:SettingsLauncher.open('weather')}
'''+s[end:];p.write_text(s)
p=root/'settingsapp/catalog.json';pages=json.loads(p.read_text());pages.append({'id':'weather','title':'Weather','icon':'display.svg','parent':'general','group':2,'keywords':'weather location city forecast alerts','legacy':'__Weather'})
for page in pages:
 if page['id']=='weather':page.pop('legacy',None)
p.write_text(json.dumps(pages,indent=2))
p=root/'settings.qml';s=p.read_text().replace("window.page.legacy ?", "window.route==='weather' ? Quickshell.shellDir+'/settingsapp/WeatherPage.qml':window.page.legacy ?");p.write_text(s)
p=root/'services/WeatherState.qml';s=p.read_text().replace('import QtQuick','import qs.rosa.services as Rosa\nimport QtQuick',1);a=s.index('    function reload() {');z=s.index('    function _fetchWeather()',a)
s=s[:a]+'''    readonly property string configuredPlace:Rosa.Prefs.weatherPlace.trim()
    property string resolvedPlace:''
    property int requestGeneration:0
    onConfiguredPlaceChanged:{requestGeneration++;loc='';available=false;reload()}
    function reload() {
        if(root.loc && root.resolvedPlace===root.configuredPlace){root._fetchWeather();return}
        if(!root.configuredPlace){root.available=false;return}
        const token=++root.requestGeneration,parts=root.configuredPlace.split(',')
        if(parts.length===2 && !isNaN(Number(parts[0])) && !isNaN(Number(parts[1]))){root.loc=root.configuredPlace;root.resolvedPlace=root.configuredPlace;root.city='';root._fetchWeather();return}
        const name=parts[0].trim(),suffix=parts.length>1 ? parts[parts.length-1].trim():''
        function find(country){
            root._get('https://geocoding-api.open-meteo.com/v1/search?name='+encodeURIComponent(name)+'&count=10&language=en'+country,function(text){
                if(token!==root.requestGeneration)return
                let response;try{response=JSON.parse(text)}catch(error){return}
                const matches=response.results || []
                if(!matches.length && country){find('');return}
                const found=matches.find(item=>String(item.country_code).toLowerCase()===suffix.toLowerCase() || String(item.admin1).toLowerCase()===suffix.toLowerCase()) || matches[0]
                if(!found){root.available=false;return}
                root.city=found.name;root.loc=found.latitude+','+found.longitude;root.resolvedPlace=root.configuredPlace;root._fetchWeather()
            })
        }
        find(/^[a-z]{2}$/i.test(suffix) ? '&countryCode='+encodeURIComponent(suffix):'')
    }

'''+s[z:];p.write_text(s)
# Remove an old environment override that otherwise diverges from Settings.
p=root/'rosa/services/Weather.qml';s=p.read_text();a=s.index('        const env = Quickshell.env("WEATHER_PLACE");');z=s.index('        return Prefs.weatherPlace',a);s=s[:a]+s[z:];p.write_text(s)
# A warmed notification panel used an imperative copy of `opened`. Bind the
# transition to the actual state so async loading cannot leave it off-screen.
p=root/'ui/topbar/statusarea/notifcenter/NotifCenter.qml';s=p.read_text();a=s.index('                    property bool vis: false');z=s.index('                    transform: Translate {',a);s=s[:a]+'                    readonly property bool vis: root.opened\n\n'+s[z:];p.write_text(s)
# Notification content is composed of independently gated widget/card surfaces.
# Gating the entire input window waits on an empty capture region and leaves
# a fully transparent overlay consuming every click.
edit('ui/topbar/statusarea/notifcenter/NotifCenter.qml','GlassBackdrop { element: "notifcenter" }','GlassBackdrop { element: "notifcenter"; gateEnabled:false }')
p=root/'ui/topbar/statusarea/spotlight/SpotlightCategoryGrid.qml';s=p.read_text()
if 'import QtQuick.Effects' not in s:s='import QtQuick.Effects\n'+s
s=s.replace('                                            id: ico','''                                            id: ico
                                            layer.enabled:AppearanceState.tinted && !tile.modelData.isImage && !tile.modelData.isWallpaper && !tile.modelData.clipImage
                                            layer.effect:MultiEffect{saturation:-1;colorization:1;colorizationColor:AppearanceState.iconColor}''',1);p.write_text(s)
# Unread feedback is an overlaid dot, not an expanding counter that shifts the
# entire right-hand cluster. It stays inside the bar's existing click region.
p=root/'ui/topbar/statusarea/StatusArea.qml';s=p.read_text();a=s.index('                id: _badge');z=s.index('            MouseArea {',a)
block=s[a:z].replace('anchors.top:            _clock.bottom','anchors.top:            _clock.top').replace('width: 30','width: 6').replace('height:  16','height:  6').replace('radius:  8','radius:  3').replace('                    id: _badgeTxt','                    id: _badgeTxt\n                    visible:false');s=s[:a]+block+s[z:];p.write_text(s)

p=root/'settingsapp/SettingsContent.qml';s=p.read_text().replace("if(name==='widget-style'){WidgetState.widgetStyle=['auto','color','clear','tinted'][value];return}","if(name==='widget-style'){WidgetState.widgetStyle=['auto','color','clear','tinted'][value];ShellConfig.options.appearance.iconStyle=value===3 ? 'tinted':'color';return}")
p.write_text(s)
p=root/'components/BarLogo.qml';s=p.read_text().replace("font.family:'Symbols Nerd Font Mono'","font.family:root.options.logoType==='apple' ? 'JetBrainsMono Nerd Font':'Symbols Nerd Font Mono'");p.write_text(s)
p=root/'services/TopBarStyle.qml';s=p.read_text().replace("    property var samples:({})", "    readonly property color menuBackground:ShellConfig.options.topbar.backgroundColor\n    property var samples:({})");s=s.replace("        const name=screen ?", "        if(ShellConfig.options.topbar.backgroundEnabled && ShellConfig.options.topbar.backgroundOpacity>=0.5){const c=root.menuBackground;return (0.2126*c.r+0.7152*c.g+0.0722*c.b)>0.55 ? '#17171a':'#fafafa'}\n        const name=screen ?");p.write_text(s)

# Colorization already computes luminance; desaturating afterwards erases its hue.
for name in ['tahoedock/DockTile.qml','ui/desktop/DesktopIcon.qml','ui/topbar/statusarea/spotlight/SpotlightCategoryGrid.qml']:
 p=root/name;s=p.read_text().replace('saturation:-1;colorization:1','saturation:0;colorization:1').replace('saturation:AppearanceState.tinted || ShellConfig.options.dockAppearance.monochromeIcons ? -1 : 0','saturation:!AppearanceState.tinted && ShellConfig.options.dockAppearance.monochromeIcons ? -1 : 0');p.write_text(s)
p=root/'ui/desktop/DesktopLayer.qml';s=p.read_text().replace('color: "#30ffffff"','color: Qt.rgba(Theme.accent.r,Theme.accent.g,Theme.accent.b,0.18)').replace('border.color: "#80ffffff"','border.color: Qt.rgba(Theme.accent.r,Theme.accent.g,Theme.accent.b,0.75)');p.write_text(s)
# One Appearance page, with its detailed optical controls folded below the basics.
p=root/'ui/settings/pages/AppearancePage.qml';s=p.read_text();start=s.index('    ContentSection {')
# Preserve existing per-surface and compositor controls without the duplicate
# style/color editor or a second navigation destination.
advanced=s.rfind('    ContentSection {',0,s.index('Liquid Glass par élément'))
custom=s.rfind('    ContentSection {',0,s.index('Personnalisation du style'));customEnd=s.index('        Column {',custom)
uniqueGlass=s[custom:customEnd]+'    }\n'
s=s[:start]+'''    AppearanceControls{}
    TahoeButton{text:root.advanced ? "Hide advanced settings":"Advanced settings…";onClicked:root.advanced=!root.advanced}
    ColumnLayout{Layout.fillWidth:true;visible:root.advanced;spacing:24
'''+uniqueGlass+s[advanced:s.rfind('}')]+ '\n    }\n}\n'
s=s.replace('    property string glassTarget: "*"','    property string glassTarget: "*"\n    property bool advanced:false')
p.write_text(s)
(root/'ui/settings/pages/LegacyAppearancePage.qml').write_text(s)
p=root/'settingsapp/catalog.json';pages=json.loads(p.read_text());pages=[page for page in pages if page['id']!='glass']
for page in pages:
 if page['id']=='appearance':page['legacy']='LegacyAppearancePage'
p.write_text(json.dumps(pages,indent=2))
p=root/'services/SettingsCatalog.qml';s=p.read_text().replace("function resolve(id){", "function resolve(id){if(id==='glass')id='appearance';");p.write_text(s)
for name,directory in [('AppearanceControls.qml','ui/settings/pages'),('BrightnessController.qml','services')]:
 (root/directory/name).write_text((here/name).read_text());p=root/directory/'qmldir';p.write_text(p.read_text()+'\n'+('singleton ' if name=='BrightnessController.qml' else '')+Path(name).stem+' '+name+'\n')
(root/'tools/brightness.py').write_text((here/'brightness.py').read_text())
# All panels use the same serialized hardware backend, including DDC monitors.
p=root/'ui/topbar/statusarea/controlcenter/ControlCenter.qml';s=p.read_text();a=s.index('    property string brtPath:');z=s.index('    readonly property bool focusOn:',a)
s=s[:a]+'''    property real brtValue:BrightnessController.value
    Timer{id:_brtT;interval:120;onTriggered:BrightnessController.set(root.brtValue)}
'''+s[z:];p.write_text(s)
p=root/'ui/lockscreen/LockControlCenter.qml';s=p.read_text().replace('property real brtValue: 0.5','property real brtValue: BrightnessController.value').replace('property bool hasBacklight: false','property bool hasBacklight: BrightnessController.available');a=s.index('    Process {\n        id: _brtProbe');z=s.index('    component BoxButton:',a);s=s[:a]+'''    Timer{id:_brtT;interval:120;onTriggered:BrightnessController.set(root.brtValue)}
    onOpenChanged:if(root.open)BrightnessController.refresh()

'''+s[z:];p.write_text(s)
p=root/'ui/osd/OSD.qml';s=p.read_text().replace('property real brtValue:    0.65','property real brtValue:    BrightnessController.value');a=s.index('    Process {\n        id: _brtFindDev');z=s.index('    Process {\n        id: _kbdInitProc',a);s=s[:a]+s[z:];s=s.replace('        _brtFindDev.running  = true','        BrightnessController.refresh()');p.write_text(s)
p=root/'rosa/services/Brightness.qml';p.write_text('''pragma Singleton
import QtQuick
import Quickshell
import qs.services
Singleton{
 readonly property bool available:BrightnessController.available
 readonly property real value:BrightnessController.value
 readonly property string device:'display'
 function set(fraction){BrightnessController.set(fraction)}
 function change(delta){BrightnessController.change(delta)}
}
''')
for name in ['ui/topbar/statusarea/controlcenter/ControlCenter.qml','ui/lockscreen/LockControlCenter.qml']:
 p=root/name;s=p.read_text();s=re.sub(r'root\.brtValue = value\s+_brtT\.restart\(\)','BrightnessController.set(value)',s);p.write_text(s)
