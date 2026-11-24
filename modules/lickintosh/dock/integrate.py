from pathlib import Path
import shutil,sys,json
root=Path(sys.argv[1]);here=Path(__file__).parent
out=root/'tahoedock';shutil.copytree(here,out,ignore=shutil.ignore_patterns('__pycache__','test_*','integrate.py'))
out.chmod(0o755)
p=out/'TahoeDockSurface.qml';p.chmod(0o644);p.write_text(p.read_text().replace('@PYTHON@',sys.argv[2]))
(out/'qmldir').write_text('singleton DockIcons DockIcons.qml\nsingleton DockDrag DockDrag.qml\n'+ '\n'.join(p.stem+' '+p.name for p in out.glob('*.qml') if p.name not in ['DockIcons.qml','DockDrag.qml'])+'\n')
icons={}
for theme in ['MacTahoe-light','MacTahoe-dark']:
 base=root/'assets/icons_desktop'/theme
 for section in ['places','apps','mimes']:
  for size in ['16','22','24','32','48','64','96','128','256','scalable']:
   directory=base/section/size
   if directory.is_dir():
    for p in directory.iterdir():
     if p.suffix in ['.svg','.png'] and p.is_file():icons[theme+':'+p.stem]=str(p.relative_to(root))
(out/'icons.json').write_text(json.dumps(icons))
p=root/'ui/dock/Dock.qml';s=p.read_text();s='import qs.tahoedock\n'+s
start=s.index('    Loader {\n        active: true\n');end=s.index('    Loader {\n        active: dockRoot.menuVisible',start)
s=s[:start]+'    TahoeDockSurface {id:tahoeSurface;controller:dockRoot}\n\n'+s[end:]
s=s.replace('        return cmd\n', '        return cmd === \"lickintosh-finder\" ? \"org.gnome.nautilus\" : cmd\n',1)
s=s.replace('    property string menuGroupKey:', '    property string menuRecentKey: ""\n    property string menuGroupKey:',1)
anchor='                        DockMenuItem {\n                            id: _optionsItem'
assert s.count(anchor)==1
s=s.replace(anchor,'''                        DockMenuItem {
                            visible:dockRoot.menuRecentKey !== ""
                            label:"Remove from Recents"
                            onActivated:{tahoeSurface.removeRecent(dockRoot.menuRecentKey,dockRoot.menuAppName,false);dockRoot.closeContextMenu()}
                        }
                        DockMenuItem {
                            visible:dockRoot.menuRecentKey !== ""
                            label:"Never Show in Recents"
                            onActivated:{tahoeSurface.removeRecent(dockRoot.menuRecentKey,dockRoot.menuAppName,true);dockRoot.closeContextMenu()}
                        }
                        DockMenuDivider {visible:dockRoot.menuRecentKey !== ""}
'''+anchor,1)
s=s.replace('IconResolver.byName(', 'DockIcons.byName(').replace('IconResolver.forApp(', 'DockIcons.forApp(').replace('return IconResolver.forAppId(appId)','return DockIcons.forAppId(appId)')
s=s.replace('    property bool pinned:', '    property string activeAppId: \"\"\n    property bool pinned:',1)
s=s.replace('var d = JSON.parse(json)\n            var wasFullscreen', 'var d = JSON.parse(json)\n            dockRoot.activeAppId=String(d.initialClass || d.class || \"\").toLowerCase()\n            var wasFullscreen',1)
s=s.replace('_trashEmpty.running = true','tahoeSurface.requestEmptyTrash()')
start=s.index('    function focusWindow(address) {')
end=s.index('    function cycleWindow(',start)
s=s[:start]+'''    function focusWindow(address) {if(address)tahoeSurface.focusWindow(address)}

'''+s[end:]
start=s.index('        if (inst.wsName && inst.wsName.indexOf("special:") === 0) {',s.index('    function cycleWindow('))
end=s.index('        var ci = dockRoot.cycleIndex',start)
s=s[:start]+'''        // Focus the owning workspace; never relocate scratchpad windows.
        if(inst.wsName && inst.wsName.indexOf("special:hidden_")===0 && dockRoot.hiddenDestinations[inst.address]) {
            const home=dockRoot.hiddenDestinations[inst.address]
            dockRoot.dispatchLua('hl.dsp.window.move({workspace='+home+',window="address:'+inst.address+'",follow=false})')
        }
        tahoeSurface.focusWindow(inst.address)
'''+s[end:]
s=s.replace('    property var pinnedFiles: []','    property var hiddenDestinations: ({})\n    property var pinnedFiles: []',1)
s=s.replace('pinnedFiles: dockRoot.pinnedFiles, launchpadSeeded: true','pinnedFiles: dockRoot.pinnedFiles, hiddenDestinations:dockRoot.hiddenDestinations, launchpadSeeded: true',1)
s=s.replace('if (data.pinnedFiles) dockRoot.pinnedFiles = data.pinnedFiles','if (data.hiddenDestinations) dockRoot.hiddenDestinations=data.hiddenDestinations\n                    if (data.pinnedFiles) dockRoot.pinnedFiles = data.pinnedFiles',1)
s=s.replace('    function hideWindows() {','''    function hideWindows() {
        const destinations=Object.assign({},dockRoot.hiddenDestinations)
        for(const inst of dockRoot.menuInstances)if(inst.ws>0)destinations[inst.address]=inst.ws
        dockRoot.hiddenDestinations=destinations;dockRoot.saveState()
''',1)

s=s.replace('y: dockRoot.menuY - height - 45','y: Math.max(38,Math.min(parent.height-height-12,dockRoot.menuY-height-45))')
anchor='                        DockMenuDivider { visible: dockRoot.menuMode === "trash" }'
s=s.replace(anchor,'''                        DockMenuItem {
                            visible:dockRoot.menuMode === "trash"
                            label:"Remove from Dock"
                            onActivated:{ShellConfig.options.dockAppearance.showTrash=false;dockRoot.closeContextMenu()}
                        }
'''+anchor)
p.write_text(s)
p=root/'services/ShellConfig.qml';s=p.read_text();anchor='            property JsonObject dockAppearance: JsonObject {';assert s.count(anchor)==1
s=s.replace(anchor,anchor+'''
                property string position:"bottom"
                property bool showTrash:true
                property bool confirmEmptyTrash:true
                property bool showDownloads:true
                property bool showRecentFiles:true
                property bool showRecentApps:true
                property int recentAppCount:3
                property list<var> recentAppBlacklist: []
                property string stackDisplay:"stack"
                property list<var> stackPreferences: []
                property string stackView:"automatic"
                property string stackSort:"modified"
                property bool minimizeToAppIcon:true
                property bool animateOpening:true
                property bool showIndicators:true
                property int hideDelay:500
''');p.write_text(s)
p=root/'ui/settings/pages/DockPage.qml';s=p.read_text();anchor='    ContentSection {';assert anchor in s;s=s.replace(anchor,(here/'Settings.qml.inc').read_text()+'\n'+anchor,1);p.write_text(s)

# Native file drags work across the Desktop, Dock, and external applications.
p=root/'ui/desktop/DesktopIcon.qml';s=p.read_text();s='import qs.tahoedock\n'+s
anchor='    MouseArea {\n        id: area'
assert anchor in s
s=s.replace(anchor,"""    DropArea {
        id:folderDrop;anchors.fill:parent;enabled:root.fileIsDir
        onEntered:drag=>{drag.accepted=drag.hasUrls}
        onDropped:drop=>{
            if(!drop.hasUrls)return
            const format='application/x-lickintosh-file-action'
            const mode=drop.formats.indexOf(format)!==-1 ? drop.getDataAsString(format):''
            const operation=['copy','move','link'].indexOf(mode)!==-1 ? mode:drop.proposedAction===Qt.MoveAction ? 'move':drop.proposedAction===Qt.LinkAction ? 'link':'copy'
            QuickLookState.transfer(drop.urls.map(String),root.filePath,operation)
            drop.accept(operation==='move' ? Qt.MoveAction:operation==='link' ? Qt.LinkAction:Qt.CopyAction)
        }
    }
    Rectangle{anchors.fill:glyph;anchors.margins:-4;radius:9;color:'#30000000';border.color:'#28ffffff';border.width:1;visible:folderDrop.containsDrag}
    Item {
        id: nativeDrag
        width:1;height:1
        Drag.dragType:Drag.Automatic
        Drag.active:area.drag.active
        Drag.supportedActions:(area.pressModifiers & Qt.ControlModifier) ? Qt.CopyAction:(area.pressModifiers & Qt.AltModifier) ? Qt.LinkAction:Qt.CopyAction | Qt.MoveAction | Qt.LinkAction
        Drag.proposedAction:(area.pressModifiers & Qt.ControlModifier) ? Qt.CopyAction:(area.pressModifiers & Qt.AltModifier) ? Qt.LinkAction:Qt.MoveAction
        Drag.mimeData:({'text/uri-list':(root.selected ? DesktopFiles.selection:[root.filePath]).map(path=>'file://'+String(path).split('/').map(encodeURIComponent).join('/')).join('\\r\\n')+'\\r\\n','application/x-lickintosh-desktop':'1','application/x-lickintosh-file-action':(area.pressModifiers & Qt.ControlModifier) ? 'copy':(area.pressModifiers & Qt.AltModifier) ? 'link':'move'})
        Drag.imageSource:glyph.source
        Drag.imageSourceSize:Qt.size(80,80)
        Drag.hotSpot:Qt.point(40,40)
        Drag.onDragStarted:DockDrag.desktopDragging=true
        Drag.onDragFinished:{DockDrag.desktopDragging=false;root.resetPosition();area.moved=true}
        Component.onDestruction:if(Drag.active)DockDrag.desktopDragging=false
    }
"""+anchor,1)
s=s.replace('        property bool moved: false','        property int pressModifiers: 0\n        property bool moved: false',1).replace('drag.target: pressedButtons === Qt.LeftButton ? root : null','drag.target: pressedButtons === Qt.LeftButton ? nativeDrag : null',1).replace('        onPressed: function(mouse) {','        onPressed: function(mouse) {\n            area.pressModifiers=mouse.modifiers;area.moved=false',1)
a=s.index('        onReleased: function(mouse) {',s.index('id: area'));z=s.index('        onClicked: function(mouse) {',a)
s=s[:a]+"""        onReleased: function(mouse) {
            if(!moved && mouse.button===Qt.LeftButton && !ctrlPressed && DesktopFiles.selection.length>1)DesktopFiles.selectOnly(root.filePath)
            ctrlPressed=false
        }
"""+s[z:];p.write_text(s)
