from pathlib import Path
import shutil,sys
root=Path(sys.argv[1]);here=Path(__file__).parent
shutil.copytree(here,root/'quicklook',ignore=shutil.ignore_patterns('test_*','__pycache__','integrate.py'))
for copied in [root/'quicklook',*(root/'quicklook').rglob('*')]:copied.chmod(0o755 if copied.is_dir() else 0o644)
p=root/'quicklook/QuickLookState.qml';(root/'services/QuickLookState.qml').write_text(p.read_text().replace('@PYTHON@',sys.argv[2]));p.unlink()
p=root/'services/qmldir';p.write_text(p.read_text()+'\nsingleton QuickLookState QuickLookState.qml\n')
(root/'quicklook/qmldir').write_text('QuickLookIntegration QuickLookIntegration.qml\nQuickLookWindow QuickLookWindow.qml\nQuickLookModal QuickLookModal.qml\n')
p=root/'shell.qml';s=p.read_text();s='import qs.quicklook\n'+s;s=s.replace('    id: appRoot','    id: appRoot\n    QuickLookIntegration {enabled:appRoot.interfaceShown;locked:lockScreen.locked}',1);p.write_text(s)
# A normal floating preview must not capture itself into its Liquid Glass backdrop.
p=root/'components/glass/LiquidGlassBackdrop.qml';s=p.read_text().replace('    property string monitorName:', '    property string excludedAddress: ""\n    property int excludedPid: 0\n    property string monitorName:',1).replace('            sourceComponent: GlassWindows {','            sourceComponent: GlassWindows {\n                excludedAddress: root.excludedAddress\n                excludedPid: root.excludedPid',1);p.write_text(s)
p=root/'components/glass/GlassWindows.qml';s=p.read_text().replace('    id: root','    id: root\n    property string excludedAddress: ""\n    property int excludedPid: 0\n    function excludes(ipc) {return ipc && ((root.excludedPid>0 && (ipc.pid===root.excludedPid || String(ipc.title || "").startsWith("Lickintosh Quick Look"))) || (root.excludedAddress!=="" && root.addressOf(ipc.address)===root.addressOf(root.excludedAddress)))}',1).replace('&& ipc.hidden !== true','&& !root.excludes(ipc)\n                && ipc.hidden !== true',1).replace('if(c.hidden || c.mapped === false', 'if(root.excludes(c) || c.hidden || c.mapped === false',1);p.write_text(s)
p=root/'ui/desktop/DesktopLayer.qml';s=p.read_text().replace('WlrLayershell.keyboardFocus: DesktopFiles.renaming', 'WlrLayershell.keyboardFocus: QuickLookState.returnToDesktop ? WlrKeyboardFocus.Exclusive : DesktopFiles.renaming',1);anchor='            Keys.onDeletePressed: function(event) {'
assert anchor in s
s=s.replace(anchor,'''            Keys.onSpacePressed: function(event) {
                if(DesktopFiles.renaming!=="" || WidgetState.typing || !DesktopFiles.selection.length){event.accepted=false;return}
                let paths=DesktopFiles.selection.slice();let index=0
                if(paths.length===1){const chosen=paths[0];paths=[];for(let i=0;i<DesktopFiles.model.count;i++)paths.push(DesktopFiles.model.get(i,"filePath"));index=Math.max(0,paths.indexOf(chosen))}
                QuickLookState.show(paths,index,"desktop");event.accepted=true
            }
'''+anchor,1)
start=s.index('                onDropped: function(drop) {',s.index('            DropArea {'))
end=s.index('                    stage.commitCells(overrides)\n                }',start)+len('                    stage.commitCells(overrides)\n                }')
assert 'DesktopFiles.linkNames' in s[start:end]
s=s[:start]+'''                onDropped: function(drop) {
                    if(!drop.hasUrls)return
                    if(drop.formats.indexOf("application/x-lickintosh-desktop")!==-1 && drop.proposedAction===Qt.MoveAction && DesktopFiles.selection.length){
                        stage.dropIcon(DesktopFiles.nameOfPath(DesktopFiles.selection[0]),drop.x,drop.y)
                        drop.accept(Qt.MoveAction);return
                    }
                    const format="application/x-lickintosh-file-action"
                    const sourceAction=drop.formats.indexOf(format)!==-1 ? drop.getDataAsString(format):""
                    const operation=["copy","move","link"].indexOf(sourceAction)!==-1 ? sourceAction : drop.proposedAction===Qt.MoveAction ? "move":drop.proposedAction===Qt.LinkAction ? "link":"copy"
                    const token=DesktopFiles.importUrls(drop.urls,operation)
                    const next=Object.assign({},stage.pendingFileDrops);next[token]={x:drop.x,y:drop.y};stage.pendingFileDrops=next
                    drop.accept(operation==="move" ? Qt.MoveAction:operation==="link" ? Qt.LinkAction:Qt.CopyAction)
                }'''+s[end:]
s=s.replace('            id: stage\n','''            id: stage
            property var pendingFileDrops:({})
            function placeImported(paths,point) {
                const names=paths.map(path=>DesktopFiles.nameOfPath(path));const taken=[];const overrides={};const skip={}
                for(const name of names)skip[name]=true
                for(const name of names){
                    const col=Math.min(stage.iconCols-1,Math.max(0,Math.round((stage.width-stage.iconPad-point.x)/stage.iconW-.5)))
                    const row=Math.min(stage.iconRows-1,Math.max(0,Math.round((point.y-stage.iconPad-stage.iconH/2)/stage.iconH)))
                    const spot=stage.nearestFreeCell(skip,col,row,taken);taken.push(spot);overrides[name]=spot
                }
                stage.commitCells(overrides);if(paths.length)DesktopFiles.selectMany(paths)
            }
            Connections {
                target:QuickLookState
                function onTransferred(paths,token){
                    const point=stage.pendingFileDrops[token];if(!point)return
                    const next=Object.assign({},stage.pendingFileDrops);delete next[token];stage.pendingFileDrops=next
                    stage.placeImported(paths,point)
                }
                function onTransferFailed(token){const next=Object.assign({},stage.pendingFileDrops);delete next[token];stage.pendingFileDrops=next}
            }
''',1)
p.write_text(s)
p=root/'services/DesktopFiles.qml';s=p.read_text();anchor='    function linkNames(urls) {';assert anchor in s
s=s.replace(anchor,'''    function importUrls(urls,operation) {
        return QuickLookState.transfer(urls.map(url=>String(url)),root.dir,operation)
    }
'''+anchor,1);p.write_text(s)

p=root/'ui/topbar/menubar/activewindows/ActiveWindow.qml';s=p.read_text().replace('    function formatName(winClass, winTitle) {','    function formatName(winClass, winTitle) {\n        if(String(winClass).toLowerCase()==="org.gnome.nautilus" || String(winTitle).startsWith("Lickintosh Quick Look"))return "Finder"',1);p.write_text(s)

# Native windows move in compositor coordinates, without changing local QML x/y.
# Refresh shader coordinates explicitly instead of waiting for a Qt animation frame.
p=root/'components/glass/TahoeGlass.qml';s=p.read_text();anchor='    Connections {\n        target: root.Window.window'
assert anchor in s
s=s.replace(anchor,"""    Connections {
        target: root.backdrop
        ignoreUnknownSignals: true
        function onWindowPositionChanged(){root.updatePosition();root.invalidate()}
        function onScreenSizeChanged(){root.updatePosition();root.invalidate()}
    }
"""+anchor,1);p.write_text(s)
p=root/'services/DesktopFiles.qml';s=p.read_text().replace('    function isImage(', '    function isVideo(name){return /\\.(mp4|mov|m4v|mkv|webm|avi|mpe?g|ogv|3gp)$/i.test(name)}\n    function isImage(',1);p.write_text(s)
p=root/'ui/desktop/DesktopIcon.qml';s=p.read_text().replace('    property real followX:',"""    property string previewVersion: ''
    readonly property bool videoFile: !root.fileIsDir && DesktopFiles.isVideo(root.fileName)
    readonly property string videoPreview: root.videoFile ? QuickLookState.thumbnail(root.filePath,root.previewVersion):''
    property real followX:""",1).replace('!root.fileIsDir && DesktopFiles.isImage(root.fileName)',"!root.fileIsDir && (DesktopFiles.isImage(root.fileName) || root.videoPreview!=='')",1).replace('root.thumbnail ? "file://" + root.filePath :', 'root.thumbnail ? (root.videoFile ? root.videoPreview:QuickLookState.urlFor(root.filePath)) :',1);p.write_text(s)
p=root/'ui/desktop/DesktopLayer.qml';s=p.read_text().replace('                    required property var fileModified','                    previewVersion:String(fileSize)+":"+String(fileModified)\n                    required property var fileModified',1);p.write_text(s)

p=root/'components/glass/GlassTracker.qml';s=p.read_text().replace('    property bool fast: false','    property int precisionUsers: 0\n    property bool fast: false',1).replace('interval: root.fast ? root.captureFastInterval : root.captureIdleInterval','interval: root.precisionUsers>0 ? 16 : root.fast ? root.captureFastInterval : root.captureIdleInterval',1);p.write_text(s)
