import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Wayland
import qs.services
import qs.capture
import qs.components.glass
import "Draw.js" as Draw
PanelWindow {
 id:win
 screen:Quickshell.screens.find(s=>s.name===CaptureState.frame.monitor) || Quickshell.screens[0]
 anchors {top:true;bottom:true;left:true;right:true}
 color:"transparent";exclusiveZone:-1
 WlrLayershell.namespace:"lickintosh:capture"
 WlrLayershell.layer:WlrLayer.Overlay
 WlrLayershell.keyboardFocus:visible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
 property var selection:({x:0,y:0,w:0,h:0})
 property bool chosen:false
 property var items:[]
 property var draft:null
 property var undoStack:[]
 property var redoStack:[]
 property int nextId:1
 property string tool:"move"
 property var colors:[CaptureState.pickedColor || "#ff3b30","#ffcc00","#34c759","#007aff"]
 property int colorIndex:0
 property int sizeIndex:1
 property var widths:[2,4,7]
 property bool hints:false
 property bool extras:false
 property bool toolbarManual:false
 property real toolbarX:0
 property real toolbarY:0
 property real cursorX:0
 property real cursorY:0
 property var hoverRect:({x:0,y:0,w:0,h:0})
 property string operation:""
 property var originalSelection:null
 property var originalItem:null
 property int movingIndex:-1
 property real startX:0
 property real startY:0
 property bool textEditing:false
 property int editingIndex:-1
 property real textX:0
 property real textY:0
 property bool exporting:false
 property var exportRequest:null
 property bool grabPending:false
 property int renderFrames:0
 property string loadedSession:""
 readonly property bool frameReady:background.status===Image.Ready
 readonly property real factor:CaptureState.frame.factor || 1
 readonly property bool selecting:operation === "select"
 readonly property var area:chosen || selecting ? selection : ({x:0,y:0,w:0,h:0})
 readonly property string annotationColor:colors[colorIndex]
 readonly property var tools:[{name:"move",glyph:"\ue121",key:"M"},{name:"arrow",glyph:"\ue493",key:"A"},{name:"rect",glyph:"\ue167",key:"R"},{name:"ellipse",glyph:"\ue076",key:"E"},{name:"pen",glyph:"\ue1f9",key:"P"},{name:"text",glyph:"\ue198",key:"T"},{name:"mosaic",glyph:"\ue4ff",key:"B"}]
 FontLoader {id:lucide;source:Qt.resolvedUrl("assets/lucide.ttf")}
 LiquidGlassBackdrop {
  id:captureBackdrop
  frozenSource:background
  ready:win.visible && win.frameReady
  screenSize:Qt.size(win.width,win.height)
  windowPosition:Qt.point(0,0)
  element:"menus"
  captureWindows:false;showDesktopItems:false;showDesktopWidgets:false
  instantReveal:true
 }

 function clone(value){return JSON.parse(JSON.stringify(value))}
 function history(){undoStack=undoStack.concat([clone(items)]).slice(-100);redoStack=[]}
 function redraw(){annotations.requestPaint();exportCanvas.requestPaint()}
 function undo(){if(!undoStack.length)return;redoStack=redoStack.concat([clone(items)]);items=undoStack[undoStack.length-1];undoStack=undoStack.slice(0,-1);redraw()}
 function redo(){if(!redoStack.length)return;undoStack=undoStack.concat([clone(items)]);items=redoStack[redoStack.length-1];redoStack=redoStack.slice(0,-1);redraw()}
 function reset(){grabPending=false;extras=false;selection={x:0,y:0,w:0,h:0};chosen=false;items=[];draft=null;undoStack=[];redoStack=[];tool="move";toolbarManual=false;textEditing=false;exporting=false;nextId=1;cursorX=CaptureState.frame.cursorX || 0;cursorY=CaptureState.frame.cursorY || 0;if(['annotate','recordFull'].includes(CaptureState.mode)){selection=CaptureState.frame.editSelection || {x:0,y:0,w:CaptureState.frame.width,h:CaptureState.frame.height};chosen=true}hover(cursorX,cursorY);redraw();Qt.callLater(()=>keys.forceActiveFocus())}
 onVisibleChanged:if(visible){if(loadedSession!==CaptureState.frame.session){loadedSession=CaptureState.frame.session;reset()}else Qt.callLater(()=>keys.forceActiveFocus())}
 function hover(x,y){cursorX=x;cursorY=y;if(!chosen){const hit=(CaptureState.frame.windows || []).find(r=>x>=r.x && x<r.x+r.w && y>=r.y && y<r.y+r.h);hoverRect=hit || {x:0,y:0,w:0,h:0};if((CaptureState.mode==='color' || win.selecting) && !pixelTimer.running)pixelTimer.start()}}
 function normalized(x,y,x2,y2){let left=Math.max(0,Math.min(x,x2)),top=Math.max(0,Math.min(y,y2));return {x:left,y:top,w:Math.max(0,Math.min(width,Math.max(x,x2))-left),h:Math.max(0,Math.min(height,Math.max(y,y2))-top)}}
 function inside(x,y){return chosen && x>=selection.x && x<=selection.x+selection.w && y>=selection.y && y<=selection.y+selection.h}
 function handle(x,y){if(!chosen)return '';const r=selection;let left=Math.abs(x-r.x)<7,right=Math.abs(x-r.x-r.w)<7,top=Math.abs(y-r.y)<7,bottom=Math.abs(y-r.y-r.h)<7;if(x<r.x-7 || x>r.x+r.w+7 || y<r.y-7 || y>r.y+r.h+7)return '';return (top?'n':bottom?'s':'')+(left?'w':right?'e':'')}
 function hitItem(x,y){for(let i=items.length-1;i>=0;i--)if(Draw.contains(items[i],x,y))return i;return -1}
 function editText(x,y,index){editingIndex=index;textX=x;textY=y;textInput.text=index>=0 ? items[index].text : '';textEditing=true;textInput.font.pixelSize=index>=0 ? items[index].fontSize : [16,24,36][sizeIndex];Qt.callLater(()=>textInput.forceActiveFocus())}
 function commitText(discard){if(!textEditing)return;if(!discard && textInput.text.trim()){history();let a={id:nextId++,tool:'text',x:textX,y:textY,text:textInput.text,fontSize:textInput.font.pixelSize,color:annotationColor,size:widths[sizeIndex]};let list=items.slice();if(editingIndex>=0)list[editingIndex]=a;else list.push(a);items=list}textEditing=false;editingIndex=-1;keys.forceActiveFocus();redraw()}
 function down(x,y){if(CaptureState.mode==='measure'){startX=x;startY=y;selection={x:x,y:y,w:1,h:1};chosen=false;operation='select';return}if(CaptureState.mode==='color'){CaptureState.sample(x*factor,y*factor);colorPick.restart();return}if(textEditing)commitText(false);startX=x;startY=y;originalSelection=clone(selection);movingIndex=-1;operation='';const h=handle(x,y);if(h){operation='resize:'+h;return}if(!chosen || !inside(x,y)){chosen=false;selection={x:x,y:y,w:0,h:0};operation='select';return}if(tool==='text'){const i=hitItem(x,y);editText(x,y,i>=0 && items[i].tool==='text' ? i : -1);return}if(tool==='move'){const i=hitItem(x,y);if(i>=0){history();movingIndex=i;originalItem=clone(items[i]);operation='moveItem'}else operation='moveRegion';return}draft={id:nextId++,tool:tool,x:x,y:y,x2:x,y2:y,color:annotationColor,size:widths[sizeIndex],points:[{x:x,y:y}]};operation='draw';redraw()}
 function drag(x,y,modifiers){if(CaptureState.mode==='measure' && (modifiers & Qt.AltModifier)){if(Math.abs(x-startX)>Math.abs(y-startY))y=startY;else x=startX}hover(x,y);const dx=x-startX,dy=y-startY;if(operation==='select'){selection=normalized(startX,startY,x,y);if(CaptureState.mode==='measure'){selection={x:selection.x,y:selection.y,w:Math.max(1,selection.w),h:Math.max(1,selection.h)}}return}if(operation==='moveRegion'){selection={x:Math.max(0,Math.min(width-selection.w,originalSelection.x+dx)),y:Math.max(0,Math.min(height-selection.h,originalSelection.y+dy)),w:selection.w,h:selection.h};return}if(operation==='moveItem'){const list=items.slice();list[movingIndex]=Draw.move(originalItem,dx,dy);items=list;redraw();return}if(operation.startsWith('resize:')){const h=operation.slice(7),r=originalSelection;let x1=r.x,y1=r.y,x2=r.x+r.w,y2=r.y+r.h;if(h.includes('w'))x1=x;if(h.includes('e'))x2=x;if(h.includes('n'))y1=y;if(h.includes('s'))y2=y;selection=normalized(x1,y1,x2,y2);return}if(draft){draft.x2=x;draft.y2=y;if(draft.tool==='pen'){const last=draft.points[draft.points.length-1];if(Math.hypot(x-last.x,y-last.y)>1)draft.points.push({x:x,y:y})}redraw()}}
 function up(x,y){if(operation)drag(x,y,0);if(operation==='select'){if(Math.hypot(x-startX,y-startY)<4 && hoverRect.w>0)selection=clone(hoverRect);chosen=(CaptureState.mode==='measure' && selection.w+selection.h>3) || (selection.w>=2 && selection.h>=2);if(chosen && ['ocr','qr','palette','pin'].includes(CaptureState.mode))Qt.callLater(()=>finish(CaptureState.mode));if(chosen && CaptureState.mode==='lens')lensConfirm.open()}if(draft){if(Math.hypot(draft.x2-draft.x,draft.y2-draft.y)>2){history();const a=clone(draft);items=items.concat([a]);if((a.tool==='mosaic' || a.tool==='blur')){const b=Draw.bounds(a);CaptureState.mosaic(a.id,[b.x,b.y,b.w,b.h],[8,14,22][sizeIndex],a.tool)}}draft=null;redraw()}operation=''}
 function finish(kind,target){if(kind==='record'){CaptureState.opened=false;CaptureState.busy=true;CaptureState.send({action:'record',box:[selection.x,selection.y,selection.w,selection.h],config:CaptureState.config()});return}if(!chosen || CaptureState.busy || exporting)return;if(textEditing)commitText(false);exportRequest={kind:kind,target:target || ''};exporting=true;grabPending=false;renderFrames=0;for(const a of items)if(a.path && !exportCanvas.isImageLoaded(a.path))exportCanvas.loadImage(a.path);exportCanvas.requestPaint()}
 function exportReady(){return exportBackground.status===Image.Ready && items.every(a=>(a.tool!=='mosaic' && a.tool!=='blur') || (a.path && exportCanvas.isImageLoaded(a.path)))}
 function exportNow(){if(grabPending)return;grabPending=true;const request=exportRequest;const ok=exportSurface.grabToImage(result=>{const path=CaptureState.frame.exportPath;if(!result.saveToFile(path)){exporting=false;CaptureState.error('Could not write screenshot');return}CaptureState.finish(request.kind,path,selection.w,selection.h,request.target);exporting=false},Qt.size(Math.max(1,Math.round(selection.w*factor)),Math.max(1,Math.round(selection.h*factor))));if(!ok){exporting=false;CaptureState.error('Could not render screenshot')}}
 Connections {target:CaptureState;function onImagePatch(id,path,box){const list=items.slice();const i=list.findIndex(a=>a.id===id);if(i>=0){list[i]=Object.assign({},list[i],{path:path});items=list;annotations.loadImage(path);exportCanvas.loadImage(path);redraw()}}}
 Timer {id:pixelTimer;interval:35;onTriggered:if(!win.chosen)CaptureState.sample(win.cursorX*win.factor,win.cursorY*win.factor)}
 FrameAnimation {running:win.exporting;onTriggered:{if(win.exportReady()){if(++win.renderFrames>=2)win.exportNow()}else win.renderFrames=0}}
 Item {
  id:exportSurface;z:-10;visible:win.exporting;width:win.selection.w;height:win.selection.h;clip:true
  Image {id:exportBackground;x:-win.selection.x;y:-win.selection.y;width:win.width;height:win.height;source:CaptureState.frame.path ? 'file://'+CaptureState.frame.path : '';fillMode:Image.Stretch;cache:true}
  Canvas {id:exportCanvas;anchors.fill:parent;onPaint:{const ctx=getContext('2d');ctx.reset();ctx.clearRect(0,0,width,height);ctx.save();ctx.translate(-win.selection.x,-win.selection.y);Draw.paint(ctx,win.items,exportCanvas);ctx.restore()}onImageLoaded:requestPaint()}
 }
 Image {id:background;anchors.fill:parent;source:CaptureState.frame.path ? 'file://'+CaptureState.frame.path : '';fillMode:Image.Stretch;cache:true;asynchronous:true}
 Canvas {id:annotations;anchors.fill:parent;onPaint:{const ctx=getContext('2d');ctx.reset();ctx.clearRect(0,0,width,height);Draw.paint(ctx,win.items.filter((a,i)=>!(win.textEditing && i===win.editingIndex)).concat(win.draft ? [win.draft] : []),annotations)}onImageLoaded:requestPaint()}
 // Four dimming rectangles leave the selection itself at full brightness.
 Rectangle {x:0;y:0;width:win.width;height:win.area.h>0 ? win.area.y : win.height;color:win.chosen || win.selecting ? '#66000000' : '#18000000'}
 Rectangle {x:0;y:win.area.y;width:win.area.x;height:win.area.h;color:'#66000000';visible:win.area.h>0}
 Rectangle {x:win.area.x+win.area.w;y:win.area.y;width:win.width-x;height:win.area.h;color:'#66000000';visible:win.area.h>0}
 Rectangle {x:0;y:win.area.y+win.area.h;width:win.width;height:win.height-y;color:'#66000000';visible:win.area.h>0}
 Rectangle {x:win.area.x;y:win.area.y;width:win.area.w;height:win.area.h;color:'transparent';border.width:1;border.color:win.chosen ? '#ff6b35' : '#ffa888';visible:win.area.w>0 && win.area.h>0}
 Repeater {model:win.chosen ? [[0,0],[.5,0],[1,0],[0,.5],[1,.5],[0,1],[.5,1],[1,1]] : [];Rectangle {required property var modelData;x:win.selection.x+win.selection.w*modelData[0]-3;y:win.selection.y+win.selection.h*modelData[1]-3;width:6;height:6;color:'#ffffff';border.color:'#202023';border.width:1}}
 Rectangle {x:Math.max(3,win.area.x);y:Math.max(3,win.area.y-24);width:dimensions.implicitWidth+10;height:22;radius:4;color:'#e81c1c1f';visible:win.area.w>0
  Text {id:dimensions;anchors.centerIn:parent;text:Math.round(win.area.w*win.factor)+' × '+Math.round(win.area.h*win.factor)+(CaptureState.mode==='measure' ? ' · '+Math.round(Math.hypot(win.area.w,win.area.h)*win.factor)+' px diagonal' : '');color:'#ffffff';font.family:'monospace';font.pixelSize:13}
 }
 FocusScope {
  id:keys;anchors.fill:parent;focus:true
  MouseArea {anchors.fill:parent;hoverEnabled:true;cursorShape:win.tool==='move' && win.chosen ? Qt.SizeAllCursor : Qt.CrossCursor;onPressed:m=>win.down(m.x,m.y);onPositionChanged:m=>{if(pressed)win.drag(m.x,m.y,m.modifiers);else win.hover(m.x,m.y)}onReleased:m=>win.up(m.x,m.y);onDoubleClicked:m=>{const i=win.hitItem(m.x,m.y);if(i>=0 && win.items[i].tool==='text')win.editText(win.items[i].x,win.items[i].y,i);else if(win.chosen)win.finish('copy')}}
  Keys.onPressed:event=>{
   if(win.textEditing)return
   if(event.key===Qt.Key_Escape){if(win.extras){win.extras=false;event.accepted=true;return}if(CaptureState.resultTitle){CaptureState.resultTitle="";event.accepted=true;return}CaptureState.cancel();event.accepted=true;return}
   if(event.modifiers & Qt.ControlModifier){if(event.key===Qt.Key_Z){if(event.modifiers & Qt.ShiftModifier)win.redo();else win.undo();event.accepted=true;return}if(event.key===Qt.Key_Y){win.redo();event.accepted=true;return}if(event.key===Qt.Key_S && win.chosen){saveDialog.open();event.accepted=true;return}if(event.key===Qt.Key_C && win.chosen){win.finish('copy');event.accepted=true;return}}
   if(event.key===Qt.Key_Return || event.key===Qt.Key_Enter){if(win.chosen) {if(CaptureState.mode==='lens')lensConfirm.open();else win.finish(CaptureState.mode==='record' ? 'record' : ['ocr','qr','palette'].includes(CaptureState.mode) ? CaptureState.mode : 'copy')}event.accepted=true;return}
   if(event.key===Qt.Key_C && !win.chosen){CaptureState.copyColor();event.accepted=true;return}
   const letters={77:'move',65:'arrow',82:'rect',69:'ellipse',80:'pen',84:'text',66:'mosaic'}
   if(letters[event.key] && win.chosen){win.tool=letters[event.key];event.accepted=true;return}
   if(event.key>=Qt.Key_1 && event.key<=Qt.Key_4){win.colorIndex=event.key-Qt.Key_1;event.accepted=true;return}
   if(event.key===Qt.Key_BracketLeft)win.sizeIndex=Math.max(0,win.sizeIndex-1)
   if(event.key===Qt.Key_BracketRight)win.sizeIndex=Math.min(2,win.sizeIndex+1)
   if(event.key===Qt.Key_H)win.hints=!win.hints
  }
 }
 TextArea {
  id:textInput;z:25;visible:win.textEditing;x:win.textX;y:win.textY;width:Math.min(win.width-x-4,Math.max(140,contentWidth+8));height:Math.max(30,contentHeight+6)
  padding:0;color:win.annotationColor;selectionColor:'#80678cff';selectedTextColor:'white';font.family:'SF Pro Text';font.pixelSize:24;wrapMode:TextEdit.NoWrap;selectByMouse:true;textFormat:TextEdit.PlainText;background:Rectangle{color:'#18000000';border.color:'#88ffffff';border.width:1}
  Keys.onPressed:event=>{if(event.key===Qt.Key_Escape){win.commitText(true);event.accepted=true}else if((event.key===Qt.Key_Return || event.key===Qt.Key_Enter) && !(event.modifiers & Qt.ShiftModifier)){win.commitText(false);event.accepted=true}}
 }
 CaptureGlass {
  id:toolbar;z:30;visible:win.chosen && !CaptureState.resultTitle;width:toolRow.implicitWidth+16;height:56;radius:18;backdrop:captureBackdrop
  x:win.toolbarManual ? win.toolbarX : Math.max(6,Math.min(win.width-width-6,win.selection.x+win.selection.w/2-width/2))
  y:win.toolbarManual ? win.toolbarY : (win.selection.y+win.selection.h+height+100<win.height ? win.selection.y+win.selection.h+8 : Math.max(6,win.selection.y-height-100))
  MouseArea {anchors.fill:parent}
  Row {
   id:toolRow;z:1;anchors.centerIn:parent;spacing:2
   Item {width:24;height:40
    Text {anchors.centerIn:parent;text:'⠿';color:'#909096';font.pixelSize:21}
    MouseArea {anchors.fill:parent;cursorShape:Qt.SizeAllCursor;property real dx:0;property real dy:0;onPressed:m=>{const p=mapToItem(win.contentItem,m.x,m.y);dx=p.x-toolbar.x;dy=p.y-toolbar.y;win.toolbarX=toolbar.x;win.toolbarY=toolbar.y;win.toolbarManual=true};onPositionChanged:m=>{if(pressed){const p=mapToItem(win.contentItem,m.x,m.y);win.toolbarX=Math.max(0,Math.min(win.width-toolbar.width,p.x-dx));win.toolbarY=Math.max(0,Math.min(win.height-toolbar.height-48,p.y-dy))}}}
   }
   Repeater {model:win.tools;ToolButton {required property var modelData;glyph:modelData.glyph;label:modelData.name;iconFont:lucide.name;selected:win.tool===modelData.name;onClicked:{if(win.textEditing)win.commitText(false);win.tool=modelData.name}}}
   Rectangle {width:13;height:32;anchors.verticalCenter:parent.verticalCenter;color:'transparent';Rectangle{anchors.centerIn:parent;width:1;height:24;color:'#3c3c41'}}
   ToolButton {glyph:'\ue2a1';label:'Undo';iconFont:lucide.name;available:win.undoStack.length>0;onClicked:win.undo()}
   ToolButton {glyph:'\ue2a0';label:'Redo';iconFont:lucide.name;available:win.redoStack.length>0;onClicked:win.redo()}
   Rectangle {width:13;height:32;anchors.verticalCenter:parent.verticalCenter;color:'transparent';Rectangle{anchors.centerIn:parent;width:1;height:24;color:'#3c3c41'}}
   ToolButton {glyph:'\ue259';label:'Pin screenshot';iconFont:lucide.name;onClicked:win.finish('pin')}
   ToolButton {glyph:'\ue14d';label:'Save screenshot';iconFont:lucide.name;onClicked:saveDialog.open()}
   Rectangle {width:13;height:32;anchors.verticalCenter:parent.verticalCenter;color:'transparent';Rectangle{anchors.centerIn:parent;width:1;height:24;color:'#3c3c41'}}
   ToolButton {glyph:'⋯';label:'More capture actions';onClicked:win.extras=!win.extras}
   ToolButton {glyph:'×';label:'Cancel';onClicked:CaptureState.cancel()}
   ToolButton {glyph:CaptureState.mode==='record' ? '●' : '✓';label:'Confirm';primary:true;onClicked:if(CaptureState.mode==='lens')lensConfirm.open();else win.finish(CaptureState.mode==='record' ? 'record' : 'copy')}
  }
  CaptureGlass {
   backdrop:captureBackdrop;visible:win.tool!=='move';anchors.top:parent.bottom;anchors.topMargin:6;anchors.horizontalCenter:parent.horizontalCenter;width:styles.implicitWidth+16;height:44;radius:15
   MouseArea {anchors.fill:parent}
   Row {id:styles;z:1;anchors.centerIn:parent;spacing:4
    Repeater {model:win.colors;Item {required property string modelData;required property int index;width:30;height:30;opacity:win.tool==='mosaic' ? .4 : 1
     Rectangle {anchors.centerIn:parent;width:26;height:26;radius:13;color:'transparent';border.width:win.colorIndex===index ? 2 : 0;border.color:'white'}
     Rectangle {anchors.centerIn:parent;width:20;height:20;radius:10;color:modelData}
     MouseArea {anchors.fill:parent;onClicked:win.colorIndex=parent.index}
    }}
    Rectangle {width:13;height:30;color:'transparent';Rectangle{anchors.centerIn:parent;width:1;height:24;color:'#3c3c41'}}
    Repeater {model:[4,7,11];Rectangle {required property int modelData;required property int index;width:30;height:30;radius:7;color:win.sizeIndex===index ? '#3c3c3f' : 'transparent';Rectangle{anchors.centerIn:parent;width:parent.modelData;height:width;radius:width/2;color:parent.index===1 ? '#ffffff' : '#9c9ca3'}MouseArea{anchors.fill:parent;onClicked:win.sizeIndex=parent.index}}}
   }
  }
  Text {visible:win.hints;anchors.top:parent.bottom;anchors.topMargin:win.tool==='move' ? 44 : 94;anchors.horizontalCenter:parent.horizontalCenter;text:'M Move · A Arrow · R Rectangle · E Ellipse · P Pen · T Text · B Mosaic · Ctrl+Z Undo · Enter Copy · Esc Cancel';color:'white';font.pixelSize:11;style:Text.Outline;styleColor:'#1c1c1f'}
 }
 CaptureActions {
  z:35;visible:win.extras && win.chosen;backdrop:captureBackdrop
  x:Math.max(8,Math.min(win.width-width-8,toolbar.x+toolbar.width-width))
  y:Math.max(8,Math.min(win.height-height-8,toolbar.y+toolbar.height+54))
  onSelected:action=>{
   win.extras=false
   if(action==='lens')lensConfirm.open()
   else if(['highlight','blur'].includes(action))win.tool=action
   else if(['color','measure'].includes(action))CaptureState.launch(action)
   else if(['record','gif'].includes(action)){CaptureState.recordFormat=action==='gif' ? 'gif' : 'mp4';win.finish('record')}
   else if(action==='camera'){CaptureState.cancel();CaptureState.cameraOpened=true}
   else win.finish(action)
  }
 }
 CaptureResults {
  z:36;anchors.centerIn:parent;backdrop:captureBackdrop
  visible:CaptureState.resultTitle!=='' && CaptureState.resultText!=='' && CaptureState.opened
  title:CaptureState.resultTitle;result:CaptureState.resultText;colors:CaptureState.palette
  onCopyRequested:value=>CaptureState.send({action:'text',text:value})
  onDismissed:{CaptureState.resultTitle='';keys.forceActiveFocus()}
 }
 CaptureGlass {
  backdrop:captureBackdrop;id:loupe;z:40;visible:CaptureState.options.magnifier && (CaptureState.mode==='color' || win.selecting)
  x:Math.min(win.width-width-8,win.cursorX+24);y:Math.min(win.height-height-8,win.cursorY+24);width:178;height:226;radius:18
  ShaderEffectSource {id:zoom;x:8;y:8;width:162;height:162;sourceItem:background;sourceRect:Qt.rect(win.cursorX-6.5/win.factor,win.cursorY-6.5/win.factor,13/win.factor,13/win.factor);textureSize:Qt.size(13,13);smooth:false;live:true}
  Canvas {x:8;y:8;width:162;height:162;onPaint:{const c=getContext('2d');c.clearRect(0,0,width,height);c.strokeStyle='#22777777';c.lineWidth=1;for(let i=1;i<13;i++){c.beginPath();c.moveTo(i*width/13,0);c.lineTo(i*width/13,height);c.moveTo(0,i*height/13);c.lineTo(width,i*height/13);c.stroke()}}}
  Rectangle {x:8+162/2-6;y:8+162/2-6;width:12;height:12;color:'transparent';border.width:1;border.color:'white'}
  Text {x:12;y:178;text:CaptureState.pixelHex;color:'#e8e8ed';font.family:'monospace';font.pixelSize:14}
  Text {x:12;y:200;text:CaptureState.pixelRgb.join(', ')+'  ·  '+CaptureState.pixelX+', '+CaptureState.pixelY;color:'#99999f';font.family:'monospace';font.pixelSize:10}
 }
 Rectangle {z:50;visible:win.exporting;anchors.centerIn:parent;width:160;height:38;radius:10;color:'#ee1c1c1f';Text {anchors.centerIn:parent;text:'Rendering screenshot…';color:'white';font.pixelSize:13}}
 Timer {id:colorPick;interval:80;onTriggered:CaptureState.pickColor()}
 Dialog {id:lensConfirm;background:CaptureGlass{backdrop:captureBackdrop}parent:win.contentItem;x:(win.width-width)/2;y:(win.height-height)/2;width:460;title:'Search with Google Lens?';modal:true;standardButtons:Dialog.Ok | Dialog.Cancel;contentItem:Label {text:'This sends only the selected image to the temporary host uguu.se, then opens it in Google Lens. Other tools stay local.';wrapMode:Text.WordWrap}onAccepted:win.finish('lens')}
 SaveDialog {id:saveDialog;glassBackdrop:captureBackdrop;parent:win.contentItem;suggestedName:CaptureState.filename(win.selection.w*win.factor,win.selection.h*win.factor,'region');onSaveRequested:path=>win.finish('save',path)}
}
