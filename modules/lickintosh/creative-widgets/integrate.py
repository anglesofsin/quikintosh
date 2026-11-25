"""Creative widgets with focus-gated playback and one native picker owner."""
from pathlib import Path
import re,sys,json
root=Path(sys.argv[1]);here=Path(__file__).parent
python=sys.argv[2];ffmpeg=sys.argv[3];ffprobe=sys.argv[4]
def write(name,value):
 p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():p.chmod(p.stat().st_mode|0o200)
 p.write_text(value)
def edit(name,old,new,count=1):
 s=(root/name).read_text()
 if s.count(old)!=count:raise ValueError(f'Creative widgets {name}: {old[:80]!r} ({s.count(old)})')
 write(name,s.replace(old,new))
for p in here.glob('*.qml'):
 target='services' if p.name=='CreativeMedia.qml' else 'ui/widgets' if p.name in ['CreativeWidgetEditor.qml','TypographyEditor.qml'] else 'ui/widgets/types'
 write(target+'/'+p.name,p.read_text().replace('@MEDIA_PYTHON@',python))
 entry=('singleton ' if target=='services' else '')+p.stem+' '+p.name+'\n'
 write(target+'/qmldir',(root/target/'qmldir').read_text()+'\n'+entry)
write('tools/widget-media.py',(here/'media.py').read_text().replace('@FFMPEG@',ffmpeg).replace('@FFPROBE@',ffprobe))
# Existing image widgets keep their IDs, files, dimensions and styles.
write('ui/widgets/types/ImageWidget.qml','import QtQuick\nimport qs.ui.widgets.types\nMediaLibraryWidget{}\n')
name='services/WidgetRegistry.qml';s=(root/name).read_text();anchor='    readonly property var types: ['
entries=[dict(type='musicsticker',title='Music',file='MusicSticker',sizes=['s','m','l','square','wide','tall'],icon='notch/music.svg',tint='#ff375f',variants=[dict(key='card',title='Music card',sizes=['l']),dict(key='disc',title='Spinning record',sizes=['l'])]),dict(type='textsticker',title='Styled Text',file='TextSticker',sizes=['s','m','l','banner','wide','tall','square'],icon='notch/type.svg',tint='#af52de',variants=[dict(key='modern',title='Modern',sizes=['m']),dict(key='typewriter',title='Typewriter',sizes=['m']),dict(key='neon',title='Neon',sizes=['m'])]),dict(type='lyricssticker',title='Live Lyrics',file='LyricsSticker',sizes=['s','m','l','banner','wide','tall','square'],icon='notch/file-text.svg',tint='#30b0c7',variants=[dict(key='line',title='Current line',sizes=['m']),dict(key='stacked',title='Surrounding lines',sizes=['l']),dict(key='karaoke',title='Line progress',sizes=['m'])])]
assert s.count(anchor)==1;s=s.replace(anchor,anchor+'\n'+',\n'.join(json.dumps(entry) for entry in entries)+',')
s,n=re.subn(r"""(type:\s*['"]image['"],\s*title:\s*)(?:I18n\.tr\()?['"]Image['"]\)?""",r'\1"Media"',s);assert n==1
s=s.replace("label:'Image'","label:'Media'")
# Preset alternatives remain in the editor, not multiplied in the gallery.
a='    function sizesOf(type, variant) {';assert s.count(a)==1;s=s.replace(a,a+"\n        if(['musicsticker','textsticker','lyricssticker'].includes(type))return root.info(type).sizes")
write(name,s)
for name in ['services/WidgetState.qml','ui/desktop/DesktopLayer.qml']:
 s=(root/name).read_text().replace("'personalclock','image','notes'","'personalclock','image','musicsticker','textsticker','lyricssticker','notes'")
 write(name,s)
edit('services/WidgetState.qml','{ image: path }',"{ image:path, mediaFiles:path ? [path]:[], mediaFolder:'' }")
p=root/'services/WidgetState.qml';write('services/WidgetState.qml',p.read_text().replace('Choose Photo','Choose Media'))
edit('ui/widgets/WidgetView.qml','    required property var widgetData','    required property var widgetData\n    property bool desktopWidget:false')
edit('ui/widgets/WidgetView.qml','        onLoaded: {','        onLoaded: {\n            if(loader.item.desktopWidget!==undefined)loader.item.desktopWidget=Qt.binding(function(){return root.desktopWidget})')
edit('ui/desktop/DesktopLayer.qml','                        id:liveWidget','                        id:liveWidget\n                        desktopWidget:true')
# Native dialogs must be above the editor for every new file/folder role.
name='ui/widgets/WidgetSettings.qml';s=(root/name).read_text()
s=s.replace('picker.visible ?','win.nativeDialogVisible ?').replace('!picker.visible','!win.nativeDialogVisible')
a='   id:win;';assert s.count(a)==1;s=s.replace(a,r'''   property bool nativeDialogVisible:picker.visible || folderPicker.visible
   property string assetRole:'media'
   function localPath(url){return decodeURIComponent(String(url).replace(/^file:\/\//,''))}
   function chooseAsset(role){
    win.assetRole=role
    picker.fileMode=role==='media' ? FileDialog.OpenFiles:FileDialog.OpenFile
    picker.title=role==='audio' ? 'Choose music':role==='cover' ? 'Choose cover':role==='lyrics' ? 'Choose LRC':'Choose media'
    picker.nameFilters=role==='audio' ? ['Audio (*.mp3 *.flac *.ogg *.wav *.m4a *.aac *.opus)']:role==='lyrics' ? ['Lyrics (*.lrc)']:role==='cover' ? ['Images (*.png *.jpg *.jpeg *.webp *.avif *.gif)']:['Media (*.png *.jpg *.jpeg *.webp *.avif *.gif *.bmp *.tif *.tiff *.mp4 *.mkv *.webm *.mov *.m4v *.avi *.ogv)']
    picker.open()
   }
   function acceptAssets(urls){
    if(!root.entry || !urls.length)return
    const files=urls.map(win.localPath),path=files[0]
    if(win.assetRole==='media'){const previous=root.entry.mediaFolder ? []:root.entry.mediaFiles || (root.entry.image ? [root.entry.image]:[]);const merged=Array.from(new Set(previous.concat(files)));WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{mediaFiles:merged,image:merged[0] || '',mediaFolder:''})}
    else if(win.assetRole==='audio'){
     WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{audioFile:path})
     if(audioMetadata.running)audioMetadata.running=false
     audioMetadata.path=path;Qt.callLater(function(){audioMetadata.running=true})
    }
    else if(win.assetRole==='cover')WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{musicCover:path})
    else if(win.assetRole==='lyrics')WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{lyricsFile:path})
   }
   function acceptFolder(url){if(root.entry && String(url))WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{mediaFolder:win.localPath(url),mediaFiles:[],image:''})}
'''+a)
# Remove the old image-only preview/options. Surface, sizes and appearance stay.
def remove_object(text,anchor):
 a=text.index(anchor);start=text.index('{',a);depth=0;quote=None;escaped=False
 for i in range(start,len(text)):
  c=text[i]
  if quote:
   if escaped:escaped=False
   elif c=='\\':escaped=True
   elif c==quote:quote=None
  elif c in ['"',"'"]:quote=c
  elif c=='{':depth+=1
  elif c=='}':
   depth-=1
   if depth==0:return text[:a]+text[i+1:]
 raise ValueError('Unclosed image editor')
a="     Item{\n      visible:root.entry.type==='image'";assert s.count(a)==1;s=remove_object(s,a)
for anchor in ["     RowLayout{visible:root.entry.type==='image'","     TahoeField{visible:root.entry.type==='image'","     TahoeButton{visible:root.entry.type==='image'"]:
 while anchor in s:s=remove_object(s,anchor)
a='     RowLayout{Layout.fillWidth:true\n      Text{text:\'Surface\''
if a not in s:
 a='     RowLayout{Layout.fillWidth:true\n      Text{text:I18n.tr(\'Surface\')'
# Insert without relying on untranslated labels.
a=s.index("     RowLayout{visible:root.entry.type==='clock'")
s=s[:a]+'''     CreativeWidgetEditor{
      visible:['image','musicsticker','textsticker','lyricssticker'].includes(root.entry.type)
      Layout.fillWidth:true;entry:root.entry
      onChooseFile:role=>win.chooseAsset(role)
      onChooseFolder:folderPicker.open()
     }
'''+s[a:]
a=s.index('   FileDialog{id:picker;');b=s.index('\n',a)
s=s[:a]+'''   FileDialog{
    id:picker;modality:Qt.WindowModal;currentFolder:'file://'+Quickshell.env('HOME')+'/Pictures'
    onAccepted:win.acceptAssets(Array.from(selectedFiles))
   }
   FolderDialog{
    id:folderPicker;modality:Qt.WindowModal;title:'Choose media folder'
    currentFolder:root.entry.mediaFolder ? 'file://'+root.entry.mediaFolder:'file://'+Quickshell.env('HOME')+'/Pictures'
    onAccepted:win.acceptFolder(selectedFolder)
   }
   Process{
    id:audioMetadata;property string path:'';property string requested:'';property string editingId:''
    onStarted:{requested=path;editingId=WidgetState.editingId}
    command:['@MEDIA_PYTHON@',Quickshell.shellDir+'/tools/widget-media.py','metadata',path]
    stdout:StdioCollector{onStreamFinished:{
     if(!root.entry || audioMetadata.requested!==root.entry.audioFile || audioMetadata.editingId!==WidgetState.editingId)return
     try{const m=JSON.parse(text),changes={};if(!root.entry.musicTitle && m.title)changes.musicTitle=m.title;if(!root.entry.musicArtist && m.artist)changes.musicArtist=m.artist;if(!root.entry.musicDescription && m.album)changes.musicDescription=m.album;WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,changes)}catch(error){}
    }}
   }
'''.replace('@MEDIA_PYTHON@',python)+s[b:]
s=s.replace('import Quickshell\n','import Quickshell\nimport Quickshell.Io\n',1)
write(name,s)
