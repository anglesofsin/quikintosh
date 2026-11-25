"""Clock color regions and weather atmosphere, built on shared widget policy."""
from pathlib import Path
import sys
r=Path(sys.argv[1]);here=Path(__file__).parent
def write(name,text):
 p=r/name
 if p.exists():p.chmod(p.stat().st_mode|0o200)
 p.write_text(text)
p='ui/widgets/types/PersonalClock.qml';s=(r/p).read_text()
anchor=" readonly property string effect:widgetData?.clockEffect || 'solid'"
assert anchor in s
s=s.replace(anchor,anchor+'''
 readonly property string colorLayout:widgetData?.clockColorLayout || 'single'
 readonly property bool colorParts:colorLayout!=='single'
 readonly property var colorPalette:AppearanceState.palette[Theme.isLight ? 'light':'dark'] || ({})
 readonly property color partFirst:widgetData?.clockPartPalette!==false ? colorPalette.primary || Theme.accent:widgetData?.clockPartFirst || '#ffb6ce'
 readonly property color partSecond:widgetData?.clockPartPalette!==false ? colorPalette.tertiary || Theme.textPrimary:widgetData?.clockPartSecond || '#89cfff'
 readonly property color partThird:widgetData?.clockPartPalette!==false ? colorPalette.secondary || Theme.accent:widgetData?.clockPartThird || '#e6caff'
''',1)
s=s.replace("hideSource:root.glassReady || root.effect==='gradient'", "hideSource:root.glassReady || root.effect==='gradient' || root.colorParts",1)
s=s.replace("visible:root.effect==='gradient'", "visible:root.effect==='gradient' && !root.colorParts",1)
anchor='   ShaderEffect{\n    id:glyphGlass;'
assert anchor in s
s=s.replace(anchor,'''   ShaderEffectSource{id:glassMaterial;sourceItem:glyphGlass;hideSource:root.colorParts && root.glassReady;live:root.colorParts && root.glassReady && root.visible && !root.interactionPaused;visible:false}
   ShaderEffect{
    anchors.fill:parent;visible:root.colorParts;blending:true
    property variant maskTex:mask
    property variant glassTex:root.glassReady ? glassMaterial:mask
    property color firstColor:root.partFirst
    property color secondColor:root.partSecond
    property color thirdColor:root.partThird
    property real mode:Math.max(1,['single','horizontal','vertical','diagonal','stripes','trio'].indexOf(root.colorLayout))
    property real split:root.widgetData?.clockPartSplit ?? .5
    property real softness:root.widgetData?.clockPartSoftness ?? 0
    property real glass:root.glassReady ? 1:0
    fragmentShader:Qt.resolvedUrl(Quickshell.shellDir+'/assets/shaders/liquidglass/ClockColors.frag.qsb')
   }
'''+anchor,1)
# Color masks stay live for Solid/Shadow composition too.
s=s.replace("(root.glassReady || root.effect==='gradient')", "(root.glassReady || root.effect==='gradient' || root.colorParts)")
write(p,s)
p='ui/widgets/WidgetSettings.qml';s=(r/p).read_text();needle="ConfigSwitch{text:'Animate changing digits'";i=s.index(needle);s=s[:i]+(here/'ClockColorControls.inc').read_text()+'\n'+s[i:];write(p,s)
write('ui/widgets/types/WeatherAtmosphere.qml',(here/'WeatherAtmosphere.qml').read_text())
p='ui/widgets/types/qmldir';write(p,(r/p).read_text()+'\nWeatherAtmosphere WeatherAtmosphere.qml\n')
p='ui/widgets/types/WeatherWidget.qml';s=(r/p).read_text();needle='    id: w';assert needle in s
s=s.replace('readonly property bool dark: w.look ? !w.look.light : true',
            'readonly property bool dark: w.hasData || (w.look ? !w.look.light : true)')
s=s.replace(needle,needle+'''
    WeatherAtmosphere{
        anchors.fill:parent;z:0
        kind:w.hasData ? w.kind:''
        active:w.widgetData?.weatherAnimated!==false && !w.isSnapshot
        intensity:w.widgetData?.weatherIntensity ?? 1
        speed:w.widgetData?.weatherSpeed ?? 1
        lightning:w.widgetData?.weatherLightning!==false
        dropColor:w.widgetData?.weatherDropColor || '#9cd9ff'
    }
''',1)
if 'property bool isSnapshot:' not in s:s=s.replace('    id: w','    id: w\n    property bool isSnapshot:false',1)
write(p,s)
write('assets/shaders/liquidglass/ClockColors.frag',(here/'ClockColors.frag').read_text())
