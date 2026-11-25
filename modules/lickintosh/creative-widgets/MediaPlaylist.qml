import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
Item {
 id:root
 property var widgetData:null
 property bool active:false
 property bool isSnapshot:false
 property var files:[]
 property int index:0
 property string error:''
 property bool rescan:false
 readonly property string folder:widgetData?.mediaFolder || ''
 readonly property bool recursive:!!widgetData?.mediaRecursive
 readonly property string sort:widgetData?.mediaSort || 'name'
 readonly property string path:(isSnapshot ? CreativeMedia.frames[widgetData?.id]:'') || files[index] || ''
 onPathChanged:if(!isSnapshot)CreativeMedia.frame(widgetData?.id,path)
 readonly property bool video:/\.(mp4|mkv|webm|mov|m4v|avi|ogv)$/i.test(path)
 readonly property int interval:Math.max(1,Math.min(86400,Number(widgetData?.mediaInterval ?? 60)))*1000
 function adopt(list){
  const previous=path;files=list;index=Math.max(0,list.indexOf(previous))
 }
 readonly property string inputKey:JSON.stringify([folder,recursive,sort,widgetData?.mediaFiles || [],widgetData?.image || ''])
 function refresh(){
  if(folder && !isSnapshot){if(scan.running){rescan=true;return}scan.requested=folder;scan.recursive=recursive;scan.sort=sort;scan.running=true}
  else{error='';adopt(widgetData?.mediaFiles?.length ? widgetData.mediaFiles:(widgetData?.image ? [widgetData.image]:[]))}
 }
 function next(){
  if(files.length<2)return
  index=widgetData?.mediaShuffle ? (index+1+Math.floor(Math.random()*(files.length-1)))%files.length:(index+1)%files.length
 }
 onInputKeyChanged:refresh()
 onActiveChanged:if(active && folder && !files.length)refresh()
 Component.onCompleted:refresh()
 Process{
  id:scan
  property string requested:''
  property bool recursive:false
  property string sort:'name'
  command:['@MEDIA_PYTHON@',Quickshell.shellDir+'/tools/widget-media.py','scan',requested,String(recursive),sort]
  onExited:code=>{if(code!==0)root.error="Unable to read folder";if(root.rescan){root.rescan=false;Qt.callLater(root.refresh)}}
  stdout:StdioCollector{onStreamFinished:{
   if(scan.requested!==root.folder){Qt.callLater(root.refresh);return}
   try{const result=JSON.parse(text);root.error=result.error || '';root.adopt(result.files || [])}catch(error){root.error='Unable to read folder'}
  }}
 }
 Timer{interval:root.interval;running:root.active && root.files.length>1 && !(root.video && root.widgetData?.mediaFinishVideo);repeat:true;onTriggered:root.next()}
 Timer{interval:120000;running:root.active && !!root.folder;repeat:true;onTriggered:root.refresh()}
}
