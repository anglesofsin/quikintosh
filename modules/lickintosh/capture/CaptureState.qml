pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
Singleton {
    id:root
    property bool enabled:false
    property bool opened:false
    property double quietClipboardUntil:0
    signal screenshotSaved(string path)
    property bool cameraOpened:false
    property string pickedColor:""
    property string resultText:""
    property string resultTitle:""
    property var palette:[]
    property string recordFormat:"mp4"
    property bool recording:false
    property double recordingSince:0
    readonly property string recordTime:Math.floor((recordClock.date.getTime()-recordingSince)/60000)+":"+String(Math.floor((recordClock.date.getTime()-recordingSince)/1000)%60).padStart(2,"0")
    SystemClock {id:recordClock;precision:SystemClock.Seconds;enabled:root.recording}
    function launch(kind){opened=false;launchDelay.kind=kind;launchDelay.restart()}
    Timer {id:launchDelay;property string kind:"region";interval:100;onTriggered:root.open(kind)}
    property bool busy:false
    property bool workerReady:false
    property bool restartReady:true
    property string mode:"region"
    property string pendingMode:""
    property var frame:({})
    property var pins:[]
    property string pixelHex:"#000000"
    property var pixelRgb:[0,0,0]
    property int pixelX:0
    property int pixelY:0
    property bool flash:false
    property string flashMonitor:""
    readonly property var options:ShellConfig.options.capture
    signal captured()
    signal imagePatch(int id,string path,var box)
    signal error(string message)
    function send(data) {if(workerReady)worker.write(JSON.stringify(data)+"\n")}
    function filename(width,height,mode){if(frame.editSelection && frame.filename)return frame.filename;const now=new Date();return options.filenameTemplate.replace('{date}',Qt.formatDateTime(now,'yyyy-MM-dd')).replace('{time}',Qt.formatDateTime(now,'hh-mm-ss')).replace('{datetime}',Qt.formatDateTime(now,'yyyy-MM-dd_hh-mm-ss')).replace('{w}',String(Math.round(width))).replace('{h}',String(Math.round(height))).replace('{mode}',mode)}
    function config() {return {autoSave:options.autoSave,directory:options.directory,filenameTemplate:options.filenameTemplate,feedback:options.feedback,ocrLanguages:options.ocrLanguages,recordFormat:recordFormat,recordSystemAudio:options.recordSystemAudio,recordMic:options.recordMic,recordCursor:options.recordCursor,recordMaxSeconds:options.recordMaxSeconds,videoDirectory:options.videoDirectory}}
    function open(kind) {
        if(!enabled)return
        if(opened){cancel();return}
        if(busy)return
        quietClipboardUntil=Date.now()+1500;busy=true;resultText="";resultTitle="";palette=[];mode=kind || "region"
        if(!workerReady){pendingMode=mode;return}
        send({action:"prepare",mode:mode,config:config()})
    }
    function editFile(path){if(!enabled || busy || !workerReady)return;opened=false;busy=true;mode="annotate";send({action:"editImage",path:path})}
    function cancel() {opened=false;busy=false;send({action:"cancel"});frame=({})}
    function sample(x,y) {send({action:"sample",x:Math.round(x),y:Math.round(y)})}
    function copyColor(){send({action:"text",text:pixelHex})}
    function pickColor(){send({action:"colorResult"});opened=false}
    function mosaic(id,box,block,effect){send({action:"mosaic",id:id,box:box,block:block,effect:effect || "mosaic"})}
    function finish(kind,path,width,height,target){quietClipboardUntil=Date.now()+1500;opened=false;busy=true;send({action:"finish",kind:kind,path:path,width:width,height:height,target:target || "",config:config()})}
    function unpin(id) {const p=pins.find(p=>p.id===id);if(p)send({action:"unpin",path:p.path});pins=pins.filter(p=>p.id!==id)}
    Process {
        id:worker;running:root.enabled && root.restartReady;stdinEnabled:true
        command:["@CAPTURE_PYTHON@",Quickshell.shellDir+"/capture/backend.py"]
        stdout:SplitParser {onRead:line=>{
            try {
                const event=JSON.parse(line)
                if(event.type==="ready"){root.workerReady=true;if(root.pendingMode){root.send({action:"prepare",mode:root.pendingMode,config:root.config()});root.pendingMode=""}}
                else if(event.type==="prepared"){root.frame=event;root.busy=false;root.captured();root.opened=true}
                else if(event.type==="sample"){root.pixelHex=event.hex;root.pixelRgb=event.rgb;root.pixelX=event.x;root.pixelY=event.y}
                else if(event.type==="mosaic")root.imagePatch(event.id,event.path,event.box)
                else if(event.type==="pinned"){root.pins=root.pins.concat([event]);root.busy=false;root.frame=({})}
                else if(event.type==="result"){root.resultTitle=event.title;root.resultText=event.text || "";root.palette=event.palette || [];if(event.title==="Pixel color" && root.palette.length)root.pickedColor=root.palette[0];root.busy=false;root.opened=true;}
                else if(event.type==="recording"){root.recording=true;root.recordingSince=Date.now();root.busy=false;root.opened=false;root.frame=({})}
                else if(event.type==="recorded"){root.recording=false;root.resultTitle="Recording saved";root.resultText=event.path;root.busy=false}
                else if(event.type==="complete"){root.quietClipboardUntil=Date.now()+800;if(event.saved && ["copy","save","fullscreen"].includes(event.action))root.screenshotSaved(event.saved);root.busy=false;root.opened=false;root.frame=({});if(event.flash){root.flashMonitor=event.monitor;root.flash=true;flashEnd.restart()}}
                else if(event.type==="emptyOcr"){root.busy=false;root.opened=true;root.error("No text was found. Select another area or change the OCR language.")}
                else if(event.type==="error"){if(event.recording===false)root.recording=false;root.busy=false;if(root.frame.session)root.opened=true;root.error(event.message)}
            } catch(e) {console.warn("Capture worker event:",e)}
        }}
        onExited:{root.workerReady=false;root.busy=false;root.opened=false;if(root.enabled){root.restartReady=false;restart.restart()}}
    }
    Timer {id:restart;interval:1000;onTriggered:root.restartReady=true}
    Timer {id:flashEnd;interval:100;onTriggered:root.flash=false}
    onEnabledChanged:if(!enabled){restart.stop();restartReady=true;pendingMode="";opened=false;cameraOpened=false;pins=[]}
}
