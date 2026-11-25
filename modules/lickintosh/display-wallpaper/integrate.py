from pathlib import Path
import sys
r=Path(sys.argv[1]);here=Path(__file__).parent

def write(name,s):
 p=r/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():p.chmod(p.stat().st_mode|0o200)
 p.write_text(s.replace('};','}\n') if name.endswith('.qml') else s)
def edit(name,a,b):
 s=(r/name).read_text();assert a in s,(name,a[:70]);write(name,s.replace(a,b))
for a,b in [('MonitorState.qml','services/MonitorState.qml'),('MonitorsPage.qml','ui/settings/pages/MonitorsPage.qml'),('WallpaperSettings.qml','services/WallpaperSettings.qml'),('displays.py','tools/display-manager.py')]:write(b,(here/a).read_text().replace('@PYTHON@',sys.executable))
write('services/qmldir',(r/'services/qmldir').read_text()+'\nsingleton WallpaperSettings WallpaperSettings.qml\n')
edit('services/ShellConfig.qml','            property JsonObject wallpaper: JsonObject {','''            property JsonObject wallpaper: JsonObject {
                property var folders:[]
                property var favorites:[]
                property var perDisplay:({})
                property string fit:'fill'
                property string backgroundColor:'#000000'
                property real dim:0
                property bool pauseFullscreen:true
                property bool shuffleEnabled:false
                property int shuffleSeconds:900
                property bool shuffleRandom:true
                property bool shuffleFavorites:false
                property bool showNames:false
                property int thumbnailSize:166
                property int transitionMs:350''')
# Scan multiple folders once; thumbnails remain lazy and bounded.
edit('services/WallpaperLibrary.qml',"send({action:'scan',group:'personal',directory:userDir})","send({action:'scan',group:'personal',directory:userDir,directories:ShellConfig.options.wallpaper.folders})")
edit('services/WallpaperLibrary.qml',' onUserDirChanged:if(loaded)refresh()'," onUserDirChanged:if(loaded)refresh()\n Connections{target:ShellConfig.options.wallpaper;function onFoldersChanged(){root.refresh()}}")
edit('tools/wallpaper-library.py',"entries = inventory(request['directory'])", "entries = list({i['path']:i for directory in [request['directory']]+request.get('directories',[]) for i in inventory(directory)}.values())")
# Real wallpapers use the same fit and per-screen choices as their glass fallback.
p='ui/topbar/statusarea/spotlight/SpotlightWindow.qml'
edit(p,'property string source: root.currentWallpaper',"property string source: GlassWallpaper.preview || WallpaperSettings.pathFor(screen.name) || root.currentWallpaper\n            readonly property string screenVideo:WallpaperSettings.videoFor(screen.name) || (!WallpaperSettings.pathFor(screen.name) && GlassWallpaper.videoActive ? ShellConfig.options.wallpaper.videoPath:'')")
edit(p,'color: "#000000"','color: ShellConfig.options.wallpaper.backgroundColor')
edit(p,'active: GlassWallpaper.videoActive','active: bgWin.screenVideo!==""')
edit(p,'item.source = Qt.binding(function() { return ShellConfig.options.wallpaper.videoPath })','item.source = Qt.binding(function() { return bgWin.screenVideo })')
edit(p,'item.paused = Qt.binding(function() { return GameMode.enabled })',"item.paused = Qt.binding(function() { return GameMode.enabled || (ShellConfig.options.wallpaper.pauseFullscreen && GlassTracker.clientsSnapshot.some(c=>c.monitor===GlassTracker.monitorSnapshots.find(m=>m.name===bgWin.screen.name)?.id && c.fullscreen>0)) })")
edit(p,'fillMode: Image.PreserveAspectCrop',"fillMode: ShellConfig.options.wallpaper.fit==='fit' ? Image.PreserveAspectFit:ShellConfig.options.wallpaper.fit==='stretch' ? Image.Stretch:ShellConfig.options.wallpaper.fit==='center' ? Image.Pad:Image.PreserveAspectCrop")
edit(p,'duration: 350','duration: ShellConfig.options.wallpaper.transitionMs')
edit(p,'interval: 360','interval: ShellConfig.options.wallpaper.transitionMs+10')
edit(p,'            Column {\n                anchors.centerIn: parent','            Rectangle{anchors.fill:parent;color:"black";opacity:ShellConfig.options.wallpaper.dim;z:2}\n            Column {\n                anchors.centerIn: parent')
edit('components/glass/LiquidGlassBackdrop.qml','path: root.wallpaperPath','path: WallpaperSettings.pathFor(root.monitorName) || root.wallpaperPath')
p='components/glass/WallpaperSlot.qml';s=(r/p).read_text().replace('import QtQuick','import QtQuick\nimport qs.services',1).replace('fillMode: Image.PreserveAspectCrop',"fillMode: ShellConfig.options.wallpaper.fit==='fit' ? Image.PreserveAspectFit:ShellConfig.options.wallpaper.fit==='stretch' ? Image.Stretch:ShellConfig.options.wallpaper.fit==='center' ? Image.Pad:Image.PreserveAspectCrop");write(p,s)
# Page enhancements retain the virtualized, demand-loaded gallery.
p='ui/settings/pages/WallpaperPage.qml';s=(r/p).read_text().replace("text:I18n.tr('Wallpaper')","text:'Wallpaper'")
s=s.replace('import QtQuick.Controls','import QtQuick.Dialogs\nimport qs.ui.settings.widgets\nimport QtQuick.Controls',1)
s=s.replace(" property string query:''", """ property string query:''
 property string display:''
 property bool advanced:false
 property string sorting:'name'
 readonly property var prefs:ShellConfig.options.wallpaper
 FileDialog{id:file;title:'Choose Wallpaper';nameFilters:['Images and Videos (*.jpg *.jpeg *.png *.webp *.gif *.avif *.mp4 *.webm *.mkv *.mov)'];onAccepted:{const path=decodeURIComponent(selectedFile.toString().replace(/^file:\\/\\//,''));WallpaperSettings.apply(root.display,root.activeTarget,{path:path,video:/\\.(mp4|webm|mkv|mov)$/i.test(path)})}}
 FolderDialog{id:folder;title:'Add Wallpaper Folder';onAccepted:WallpaperSettings.addFolder(decodeURIComponent(selectedFolder.toString().replace(/^file:\\/\\//,'')))}""")
s=s.replace("if(group==='video')list=list.filter(item=>item.video)","if(group==='favorites')list=list.filter(item=>root.prefs.favorites.includes(item.path))\n  else if(group==='video')list=list.filter(item=>item.video)")
s=s.replace("const q=query.toLowerCase();return q ? list.filter(item=>item.name.toLowerCase().includes(q)):list","list=list.slice().sort((a,b)=>sorting==='recent' ? Number(b.version.split(':')[0])-Number(a.version.split(':')[0]):a.name.localeCompare(b.name));const q=query.toLowerCase();return q ? list.filter(item=>item.name.toLowerCase().includes(q)):list")
a=s.index(' function pathOf(');b=s.index(' ColumnLayout{',a)
s=s[:a]+''' function pathOf(target){const c=display ? WallpaperSettings.itemFor(display):prefs;const key=target==='lockscreen' ? 'lockscreenPath':target==='desktopLight' ? 'pathLight':target==='desktopDark' ? 'pathDark':'path';return (target==='lockscreen' ? prefs.lockscreenPath:c[key]) || prefs.path}
 readonly property string currentPath:root.pathOf(root.activeTarget)
 function apply(item){WallpaperSettings.apply(display,activeTarget,item)}
'''+s[b:]
s=s.replace("Text{text:'Wallpaper';font.family:'SF Pro Display';font.pixelSize:24;font.weight:Font.DemiBold;color:Theme.textPrimary;Layout.fillWidth:true}","TahoeCombo{Layout.fillWidth:true;model:['All Displays'].concat(Quickshell.screens.map(s=>s.name));onActivated:i=>root.display=i ? model[i]:''}\n   TahoeButton{text:'Add Photo…';onClicked:file.open()}\n   TahoeButton{text:'Add Folder…';onClicked:folder.open()}")
s=s.replace("{key:'video',label:'Videos'}","{key:'video',label:'Videos'},{key:'favorites',label:'Favorites'}")
s=s.replace("Math.floor(width/166)","Math.floor(width/root.prefs.thumbnailSize)")
s=s.replace('cellHeight:128','cellHeight:root.prefs.thumbnailSize*.65+(root.prefs.showNames ? 24:8)')
s=s.replace('height:99;radius:10','height:parent.height-(root.prefs.showNames ? 24:8);radius:10')
s=s.replace("onClicked:root.apply(modelData)","acceptedButtons:Qt.LeftButton|Qt.RightButton;onClicked:event=>{if(event.button===Qt.RightButton)WallpaperSettings.favorite(modelData.path);else root.apply(modelData)}")
s=s.replace("onClicked:event=>{if(event.button===Qt.RightButton)WallpaperSettings.favorite(modelData.path);else root.apply(modelData)}", "onClicked:event=>{if(event.button===Qt.RightButton)WallpaperSettings.favorite(modelData.path);else root.apply(modelData)}\n     Rectangle{anchors.right:parent.right;anchors.top:parent.top;anchors.margins:6;width:26;height:26;radius:13;visible:mouse.containsMouse || root.prefs.favorites.includes(modelData.path);color:'#90000000';Text{anchors.centerIn:parent;text:root.prefs.favorites.includes(modelData.path) ? '★':'☆';color:'white';font.pixelSize:18}MouseArea{anchors.fill:parent;onClicked:WallpaperSettings.favorite(modelData.path)}}")
s=s.replace("    Text{anchors.left:parent.left;anchors.right:parent.right;anchors.bottom:parent.bottom;", "    Text{visible:root.prefs.showNames;anchors.left:parent.left;anchors.right:parent.right;anchors.bottom:parent.bottom;")
a=s.index("  Text{Layout.fillWidth:true;text:root.shown.length+")
s=s[:a]+'''  RowLayout{Layout.fillWidth:true
   TahoeButton{text:'Options…';onClicked:root.advanced=!root.advanced}
   TahoeCombo{model:['Name','Newest'];onActivated:i=>root.sorting=i ? 'recent':'name'}
   Item{Layout.fillWidth:true}
   TahoeButton{visible:root.display!=='';text:'Use All Displays Settings';onClicked:WallpaperSettings.inherit(root.display)}
  }
  ScrollView{id:optionsScroll;visible:root.advanced;Layout.fillWidth:true;Layout.preferredHeight:240;clip:true
   ColumnLayout{width:optionsScroll.availableWidth;spacing:12
    RowLayout{Layout.fillWidth:true;Text{text:'Picture position';color:Theme.textPrimary;Layout.fillWidth:true}TahoeCombo{model:['Fill','Fit','Stretch','Center'];currentIndex:['fill','fit','stretch','center'].indexOf(root.prefs.fit);onActivated:i=>root.prefs.fit=['fill','fit','stretch','center'][i]}}
    RowLayout{Layout.fillWidth:true;Text{text:'Transition';color:Theme.textPrimary;Layout.fillWidth:true}TahoeCombo{model:['Instant','Fast','Smooth'];currentIndex:root.prefs.transitionMs===0 ? 0:root.prefs.transitionMs<400 ? 1:2;onActivated:i=>root.prefs.transitionMs=[0,350,700][i]}}
    ColorSetting{label:'Background Color';value:root.prefs.backgroundColor;onPicked:value=>root.prefs.backgroundColor=String(value)}
    RowLayout{Text{text:'Dim';color:Theme.textPrimary;Layout.fillWidth:true}TahoeSlider{from:0;to:.8;value:root.prefs.dim;onMoved:root.prefs.dim=value}}
    RowLayout{Text{text:'Thumbnail size';color:Theme.textPrimary;Layout.fillWidth:true}TahoeSlider{from:120;to:260;value:root.prefs.thumbnailSize;onMoved:root.prefs.thumbnailSize=Math.round(value)}}
    ConfigSwitch{text:'Show filenames';checked:root.prefs.showNames;onToggled:v=>root.prefs.showNames=v}
    ConfigSwitch{text:'Pause videos in full screen';checked:root.prefs.pauseFullscreen;onToggled:v=>root.prefs.pauseFullscreen=v}
    RowLayout{ConfigSwitch{text:'Change wallpaper';checked:root.prefs.shuffleEnabled;onToggled:v=>root.prefs.shuffleEnabled=v}TahoeCombo{model:['15 seconds','1 minute','15 minutes','1 hour','1 day'];currentIndex:Math.max(0,[15,60,900,3600,86400].indexOf(root.prefs.shuffleSeconds));onActivated:i=>root.prefs.shuffleSeconds=[15,60,900,3600,86400][i]}}
    RowLayout{ConfigSwitch{text:'Random order';checked:root.prefs.shuffleRandom;onToggled:v=>root.prefs.shuffleRandom=v}ConfigSwitch{text:'Favorites only';checked:root.prefs.shuffleFavorites;onToggled:v=>root.prefs.shuffleFavorites=v}}
    Repeater{model:root.prefs.folders;delegate:RowLayout{required property string modelData;Text{text:modelData;elide:Text.ElideMiddle;color:Theme.textSecondary;Layout.fillWidth:true}TahoeButton{text:'Remove';onClicked:WallpaperSettings.removeFolder(modelData)}}}
   }
  }
 }
}
'''
write(p,s)
# Instantiate the saved display profile on shell startup, not only on opening Settings.
edit('shell.qml','    id: appRoot','    id: appRoot\n    readonly property var displayManager:MonitorState')

# Match the wallpaper matte and dimming in the glass fallback as well.
p='components/glass/WallpaperSlot.qml';s=(r/p).read_text();s=s.replace('    property string path:',"    Rectangle{anchors.fill:parent;z:-1;visible:slot.path!==\"\" && slot.imageStatus===Image.Ready;color:ShellConfig.options.wallpaper.backgroundColor}\n    property string path:",1);write(p,s)
p='components/glass/LiquidGlassBackdrop.qml';s=(r/p).read_text();s=s.replace('        DesktopSnapshot {','        Rectangle{anchors.fill:parent;color:"black";opacity:ShellConfig.options.wallpaper.dim}\n        DesktopSnapshot {',1);write(p,s)
