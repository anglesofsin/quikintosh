"""One clock gallery, shared fonts, audio arbitration and reviewed widget options."""
from pathlib import Path
import re,sys,shutil,json
r=Path(sys.argv[1]);here=Path(__file__).parent;python=sys.argv[2]
def write(name,s):
 p=r/name
 if p.exists():p.chmod(p.stat().st_mode|0o200)
 p.write_text(s)
def edit(name,old,new,count=1):
 s=(r/name).read_text();assert s.count(old)==count,(name,old[:70],s.count(old));write(name,s.replace(old,new))
for name,target in [('AudioActivity.qml','services'),('WidgetFonts.qml','services'),('WidgetFontPicker.qml','ui/widgets'),('WidgetDetailsEditor.qml','ui/widgets')]:
 write(target+'/'+name,(here/name).read_text());write(target+'/qmldir',(r/target/'qmldir').read_text()+'\n'+('singleton ' if target=='services' else '')+name[:-4]+' '+name+'\n')
write('services/audio-policy.js',(here/'audio-policy.js').read_text())
write('tools/widget-zones.py',(here/'zones.py').read_text().replace('@TZ_DATABASE@',sys.argv[3] if len(sys.argv)>3 else '/usr/share/zoneinfo'))
shutil.copytree(here/'fonts',r/'assets/fonts/creative',dirs_exist_ok=True)
# Reuse the existing capture inventory instead of spawning another pw-dump loop.
edit('services/MediaCaptureState.qml','const result=Capture.classify(data)','AudioActivity.observe(data)\n  const result=Capture.classify(data)')
# Gallery grouping preserves both internal widget types and every stored ID.
p='services/WidgetRegistry.qml';s=(r/p).read_text().replace('Horloge mondiale','World Clock');s=s.replace("title:'Personal Clock'","title:'Clock'").replace("title:I18n.tr('Personal Clock')","title:I18n.tr('Clock')")
s=s.replace('    readonly property var sizeLabels:',"    readonly property var galleryTypes:types.filter(t=>t.type!=='personalclock')\n    readonly property var sizeLabels:")
s=s.replace('    function tilesOf(type) {',"    function tilesOf(type) {\n        if(type==='clock')return [{type:'clock',size:'s',variant:'analog',label:'Analog'},{type:'clock',size:'m',variant:'digital',label:'Digital'}].concat(root.tilesOf('personalclock').map(tile=>Object.assign({type:'personalclock'},tile)))")
write(p,s)
p='ui/widgets/WidgetGallery.qml';s=(r/p).read_text().replace('WidgetRegistry.types','WidgetRegistry.galleryTypes').replace('section.modelData.type','(tile.modelData.type || section.modelData.type)')
# The Repeater model itself has no tile yet.
s=s.replace("WidgetRegistry.tilesOf((tile.modelData.type || section.modelData.type))","WidgetRegistry.tilesOf(section.modelData.type)")
write(p,s)
# Include actual open font files in the shell-only Fontconfig directory.
p='services/LockClockStyle.qml';s=(r/p).read_text().replace('SF Pro Italique','SF Pro Italic').replace('Arrondi espacé','Spaced Rounded');a=s.index('    readonly property var styles: [');b=s.index('\n    function styleAt',a);segment=s[a:b];end=segment.rfind(']');segment=segment[:end+1]+".concat(WidgetFonts.families.slice(4).map((family,i)=>({name:WidgetFonts.names[i+4],family:family,italic:false,spacing:0})))"+segment[end+1:];s=s[:a]+segment+s[b:];write(p,s)
# Dedicated font pickers keep controls in the existing relevant editor page.
p='ui/widgets/TypographyEditor.qml';s=(r/p).read_text();a=s.index(" TahoeField{Layout.fillWidth:true;placeholderText:'Custom font family'");b=s.index('\n',a);s=s[:a]+" WidgetFontPicker{entry:root.entry;fontKey:'textFont'}"+s[b:];write(p,s)
p='ui/widgets/CreativeWidgetEditor.qml';s=(r/p).read_text();a=s.index("  TahoeField{Layout.fillWidth:true;placeholderText:'Title font family'");b=s.index('\n',a);s=s[:a]+"  WidgetFontPicker{entry:root.entry;fontKey:'musicFont';label:'Title font'}"+s[b:];write(p,s)
# Expose optional fonts in existing widgets without altering default typography.
for p in (r/'ui/widgets/types').glob('*.qml'):
 if p.name in ['CreativeText.qml','TextSticker.qml','LyricsSticker.qml','MusicSticker.qml','PersonalClock.qml','MediaFrame.qml','MediaPlaylist.qml','MediaLibraryWidget.qml','ImageWidget.qml']:continue
 s=p.read_text();m=re.search(r'\bid:\s*(\w+)',s)
 if not m or 'font.family:' not in s:continue
 ident=m[1]
 if 'property var widgetData:' not in s:s=s[:m.end()]+ '\n    property var widgetData:null'+s[m.end():]
 s=re.sub(r'font\.family:\s*([^;\n}]+)',lambda m:'font.family:'+ident+'.widgetData?.widgetFont || '+m[1],s)
 write(str(p.relative_to(r)),s)
# New content pages only where there is a meaningful per-widget option.
p='ui/widgets/WidgetSettings.qml';s=(r/p).read_text();s=s.replace("'lyricssticker','clock'].includes", "'lyricssticker','clock','worldclock','calendar','tasks','timer','quote','weather'].includes")
a="EditorGroup{title:'Widget appearance';visible:win.editorPage==='appearance'\n";assert a in s;s=s.replace(a,a+"WidgetFontPicker{visible:!['personalclock','musicsticker','textsticker','lyricssticker','image'].includes(root.entry.type);entry:root.entry}\n")
a='CreativeWidgetEditor{';assert a in s;s=s.replace(a,"     WidgetDetailsEditor{visible:win.editorPage==='content';entry:root.entry}\n"+a)
write(p,s)
# Calendar/reminders/timer/quote follow real data and keep existing actions.
edit('ui/widgets/types/CalendarWidget.qml','readonly property int firstDay: root.loc.firstDayOfWeek % 7','readonly property int firstDay:widgetData?.calendarFirstDay>=0 ? widgetData.calendarFirstDay:root.loc.firstDayOfWeek % 7')
edit('ui/widgets/types/CalendarWidget.qml','root.isMedium && root.events.length > 0','root.isMedium && root.events.length > 0 && widgetData?.calendarEvents!==false')
edit('ui/widgets/types/TasksWidget.qml','TasksState.pending.concat(TasksState.done)',"widgetData?.tasksCompleted===false ? TasksState.pending:TasksState.pending.concat(TasksState.done)")
edit('ui/widgets/types/TimerWidget.qml','root.isSmall ? [5] : [1, 5, 10, 25]',"widgetData?.timerPresets?.length ? widgetData.timerPresets.slice(0,root.isSmall ? 1:6):root.isSmall ? [5]:[1,5,10,25]")
edit('ui/widgets/types/TimerWidget.qml','required property int modelData','required property real modelData')
edit('ui/widgets/types/QuoteWidget.qml','text: QuoteState.today',"text:root.widgetData?.quoteText || QuoteState.today")
edit('ui/widgets/types/QuoteWidget.qml','visible: QuoteState.author !== ""',"visible:(root.widgetData?.quoteText ? root.widgetData?.quoteAuthor || '':QuoteState.author)!==''")
p='ui/widgets/types/QuoteWidget.qml';s=(r/p).read_text();s=re.sub(r'text:\s*(?:I18n\.tr\()?"— "\)? \+ QuoteState.author',"text:'— '+(root.widgetData?.quoteText ? root.widgetData?.quoteAuthor || '':QuoteState.author)",s);write(p,s)
# Location text can be hidden without changing the shared weather location.
p='ui/widgets/types/WeatherWidget.qml';s=(r/p).read_text();s=s.replace('id: cityText','id: cityText;visible:w.widgetData?.weatherLocation!==false').replace('visible: WeatherState.city !== \"\"','visible:w.widgetData?.weatherLocation!==false && WeatherState.city !== \"\"');write(p,s)
# Validate IANA zones in Python and avoid per-widget shell command construction.
p='ui/widgets/types/WorldClockWidget.qml';s=(r/p).read_text().replace('readonly property var cities: [','readonly property var defaultCities: [').replace('readonly property var shown: root.cities.slice(0, root.isLarge ? 6 : 3)',"readonly property var cities:widgetData?.worldCities?.length ? widgetData.worldCities:defaultCities\n    readonly property var shown:root.cities.slice(0,root.isLarge ? 6:3)\n    onShownChanged:if(!refresh.running)refresh.running=true\n    Connections{target:root;function onWidgetDataChanged(){if(!refresh.running)refresh.running=true}}")
a=s.index('        command: ["sh", "-c",');b=s.index('        stdout:',a);s=s[:a]+"        command:['"+python+"',Quickshell.shellDir+'/tools/widget-zones.py',JSON.stringify(root.shown),String(!!root.widgetData?.world12Hour)]\n"+s[b:]
a=s.index('            var map = {}');b=s.index('            root.times = map',a);s=s[:a]+"            var map={};try{map=JSON.parse(out.text)}catch(error){}\n"+s[b:];write(p,s)
