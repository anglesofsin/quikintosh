from pathlib import Path
import shutil,sys
root=Path(sys.argv[1]);python=sys.argv[2];here=Path(__file__).parent
out=root/'desktop-files';out.mkdir(exist_ok=True);shutil.copyfile(here/'operations.py',out/'operations.py')
p=root/'services/DesktopFiles.qml';s=p.read_text();anchor='    property var selection: []';assert anchor in s
s=s.replace(anchor,'''    function fileCommand(operation,paths,name,destination,mode,token){
        fileWorker.write(JSON.stringify({operation:operation,paths:paths || [],name:name || '',destination:destination || root.dir,mode:mode || 'copy',token:token || 0})+'\\n')
    }
    function copySelection(cut){if(root.selection.length)root.fileCommand(cut ? 'cut':'copy',root.selection.slice())}
    function pasteSelection(){root.fileCommand('paste',[])}
    function undoFiles(redo){root.fileCommand(redo ? 'redo':'undo',[])}
    function duplicateSelection(){if(root.selection.length)root.fileCommand('duplicate',root.selection.slice())}
    Process {
        id:fileWorker;running:true;command:['@PYTHON@',Quickshell.shellDir+'/desktop-files/operations.py'];stdinEnabled:true
        stdout:SplitParser{onRead:line=>{try{
            const data=JSON.parse(line)
            if(!data.ok){if(data.token)QuickLookState.transferFailed(data.token);Quickshell.execDetached(['notify-send','-a','Files','Unable to complete file operation',data.message]);return}
            for(const change of data.changes || []){if(change.old.slice(0,change.old.lastIndexOf('/'))===root.dir && change.new.slice(0,change.new.lastIndexOf('/'))===root.dir)WidgetState.renameIcon(root.nameOfPath(change.old),root.nameOfPath(change.new))}
            if(data.paths && data.paths.length)root.selectMany(data.paths)
            if(data.operation==='new-folder' || data.operation==='new-file')root.renaming=data.paths[0]
            if(data.operation==='trash')root.clearSelection()
            if(data.token)QuickLookState.transferred(data.paths,data.token)
        }catch(error){console.warn('Desktop files:',error)}}}
    }
'''.replace('@PYTHON@',python)+anchor,1)
def replace_function(name,text):
 global s
 a=s.index('    function '+name+'(');b=s.index('\n    }',a)+len('\n    }');s=s[:a]+text+s[b:]
replace_function('trashMany',"    function trashMany(paths) {if(paths.length)root.fileCommand('trash',paths)}")
replace_function('newFolder',"    function newFolder() {root.fileCommand('new-folder',[])}")
replace_function('newFile',"    function newFile() {root.fileCommand('new-file',[])}")
replace_function('duplicate',"    function duplicate(path) {root.fileCommand('duplicate',[path])}")
replace_function('rename',"    function rename(path,newName) {root.fileCommand('rename',[path],newName)}")
replace_function('importUrls',"    function importUrls(urls,operation) {const token=++QuickLookState.transferSerial;root.fileCommand('transfer',urls.map(String),'',root.dir,operation,token);return token}")
s=s.replace('{ label: "New File", action: "new-file" },','{ label: "New File", action: "new-file" },\n            { label: "Paste", action: "paste-files" },\n            { label: "Undo", action: "undo-files" },\n            { label: "Redo", action: "redo-files" },',1)
s=s.replace('    function fileMenu(count) {','    function fileMenu(count) {',1)
# Both single- and multi-selection menus expose real file clipboard operations.
a=s.index('    function fileMenu(count) {');b=s.index('    function handle(',a)
part=s[a:b].replace('{ label: "Open", action: "open" },','{ label: "Open", action: "open" },\n            { label: "Copy", action: "copy-files" },\n            { label: "Cut", action: "cut-files" },')
s=s[:a]+part+s[b:]
s=s.replace('    function handle(action, target) {','''    function handle(action, target) {
        if(action==='paste-files'){root.pasteSelection();return}
        if(action==='undo-files' || action==='redo-files'){root.undoFiles(action==='redo-files');return}
        if(action==='copy-files' || action==='cut-files'){root.fileCommand(action==='cut-files' ? 'cut':'copy',root.targetsOf(target));return}
''',1)
p.write_text(s)
p=root/'ui/desktop/DesktopLayer.qml';s=p.read_text();anchor='            Keys.onPressed: function(event) {';assert anchor in s
s=s.replace(anchor,anchor+'''
                if(DesktopFiles.renaming!=="" || WidgetState.typing){event.accepted=false;return}
                if(event.matches(StandardKey.Copy)){DesktopFiles.copySelection(false);event.accepted=true;return}
                if(event.matches(StandardKey.Cut)){DesktopFiles.copySelection(true);event.accepted=true;return}
                if(event.matches(StandardKey.Paste)){DesktopFiles.pasteSelection();event.accepted=true;return}
                if(event.matches(StandardKey.Undo)){DesktopFiles.undoFiles(false);event.accepted=true;return}
                if(event.matches(StandardKey.Redo)){DesktopFiles.undoFiles(true);event.accepted=true;return}
                if(event.modifiers===Qt.ControlModifier && event.key===Qt.Key_D){DesktopFiles.duplicateSelection();event.accepted=true;return}
                if(event.modifiers===(Qt.ControlModifier|Qt.ShiftModifier) && event.key===Qt.Key_N){DesktopFiles.newFolder();event.accepted=true;return}
                if(event.modifiers===Qt.ControlModifier && event.key===Qt.Key_H){WidgetState.showHidden=!WidgetState.showHidden;event.accepted=true;return}
                if((event.key===Qt.Key_Return || event.key===Qt.Key_Enter) && DesktopFiles.selection.length){for(const path of DesktopFiles.selection)DesktopFiles.open(path,DesktopFiles.nameOfPath(path));event.accepted=true;return}
                if(event.key===Qt.Key_F2 && DesktopFiles.selection.length===1){DesktopFiles.renaming=DesktopFiles.selection[0];event.accepted=true;return}
''',1);p.write_text(s)
