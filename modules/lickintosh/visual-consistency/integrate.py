from pathlib import Path
import sys,re
root=Path(sys.argv[1])
def write(name,s):
 p=root/name;p.chmod(p.stat().st_mode|0o200);p.write_text(s)
p=root/'ui/settings/pages/TopBarPage.qml';s=p.read_text();a=s.rfind('    ContentSection {',0,s.index('title:"Menu bar logo"'));z=s.index('\n    }',a)+6
s=s[:a]+'''    SettingsCard{title:"Menu bar logo"
        SettingsRow{label:"Show logo";kind:"switch";checked:ShellConfig.options.topbar.logoVisible;onToggled:value=>ShellConfig.options.topbar.logoVisible=value}
        SettingsRow{label:"Logo";kind:"choice";choices:["Linux","Apple","Text or symbol","Custom image"];selection:["linux","apple","text","image"].indexOf(ShellConfig.options.topbar.logoType);onPicked:index=>ShellConfig.options.topbar.logoType=["linux","apple","text","image"][index]}
        SettingsRow{visible:ShellConfig.options.topbar.logoType==="text";label:"Text or symbol";kind:"field";value:ShellConfig.options.topbar.logoText;onEdited:value=>ShellConfig.options.topbar.logoText=value}
        SettingsRow{visible:ShellConfig.options.topbar.logoType==="image";label:"Image path";kind:"field";value:ShellConfig.options.topbar.logoSource;onEdited:value=>ShellConfig.options.topbar.logoSource=value}
        SettingsRow{label:"Logo color";kind:"choice";choices:["Follow text and icons","Custom color","Original image colors"];selection:["follow","custom","original"].indexOf(ShellConfig.options.topbar.logoColorMode);separator:false;onPicked:index=>ShellConfig.options.topbar.logoColorMode=["follow","custom","original"][index]}
        ColorSetting{visible:ShellConfig.options.topbar.logoColorMode==="custom";label:"Custom color";value:ShellConfig.options.topbar.logoColor;onPicked:value=>ShellConfig.options.topbar.logoColor=String(value)}
        ConfigSlider{Layout.topMargin:10;Layout.bottomMargin:10;text:"Logo size";from:12;to:28;value:ShellConfig.options.topbar.logoSize;onMoved:value=>ShellConfig.options.topbar.logoSize=Math.round(value)}
    }'''+s[z:]
if 'import qs.settingsapp' not in s:s='import qs.settingsapp\n'+s
write('ui/settings/pages/TopBarPage.qml',s)
# Fixed purple was independent of the configured accent/matugen palette.
for name in ['components/GalleryFrame.qml','ui/topbar/statusarea/controlcenter/ControlGallery.qml']:
 s=(root/name).read_text().replace('"#a35cf0"','Theme.accent');write(name,s)
s=(root/'components/GalleryFrame.qml').read_text().replace('color: "#0d0d0d"','color: Theme.isLight ? "#f4f4f7":"#1d1d1f"');write('components/GalleryFrame.qml',s)
s=(root/'ui/topbar/statusarea/controlcenter/ControlCenter.qml').read_text().replace('color: root.focusOn ? "#8E44AD" : "#fff"','color: root.focusOn ? Theme.accent : "#fff"').replace('color: root.focusOn ? "#000" : "#fff"','color: "#fff"').replace('icon: "dnd.svg"','icon: "notch/moon.svg"').replace('icon: "screenshot/region.svg"','icon: "notch/crop.svg"').replace('icon: "screenshare.svg"','icon: "notch/monitor.svg"').replace('width: 26\n                                    height: 20','width: 26\n                                    height: 26').replace('width: 24\n                                    height: 20','width: 24\n                                    height: 24')
# Explicit foreground avoids inherited state heuristics making controls black.
for m in reversed(list(re.finditer(r'\bCFVI\s*\{',s))):
 depth=1;i=m.end()
 while depth and i<len(s):
  if s[i]=='{':depth+=1
  elif s[i]=='}':depth-=1
  i+=1
 body=s[m.end():i-1]
 if not re.search(r'\bcolor\s*:',body):s=s[:m.end()]+'\n                                    color:"#fff"'+s[m.end():]
write('ui/topbar/statusarea/controlcenter/ControlCenter.qml',s)
s=(root/'services/ControlCatalog.qml').read_text().replace('"screenshot/region.svg"','"notch/crop.svg"').replace('"screenshare.svg"','"notch/monitor.svg"').replace('"dnd.svg"','"notch/moon.svg"');write('services/ControlCatalog.qml',s)
# Search must reclaim the page loader's layout space and provide an empty state.
s=(root/'settings.qml').read_text().replace('active:!window.query;asynchronous:false','active:!window.query;visible:!window.query;asynchronous:false')
s=s.replace('      model:SettingsCatalog.search(window.query)','''      id:searchResults
      model:SettingsCatalog.search(window.query)
      Text{anchors.centerIn:parent;visible:searchResults.count===0;text:"No settings found";color:Theme.textSecondary;font.pixelSize:14}''');write('settings.qml',s)
for name in ['components/GalleryFrame.qml','ui/topbar/statusarea/controlcenter/ControlGallery.qml','ui/topbar/statusarea/controlcenter/ControlPreview.qml']:
 s=(root/name).read_text().replace('Theme.ink(parent, false)','Theme.textPrimary')
 if name.endswith('ControlGallery.qml'):s=s.replace('opacity: tile.added ? 0.55 : 1','opacity: 1')
 if name.endswith('GalleryFrame.qml'):s=s.replace('text: I18n.tr("Done")\n                        color: "#ffffff"','text: I18n.tr("Done")\n                        color: Theme.onAccent')
 write(name,s)
