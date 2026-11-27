import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import qs.services
Scope {
 id:app
 property bool opened:false
 property bool ready:false
 property var pending:[]
 property var state:({value:'0',rawValue:'0',expression:'',history:[],mode:'basic',degrees:true,base:10,bits:64,rpn:false,stack:[],memory:'0',bases:{},units:{},notes:''})
 property var selectedHistory:null
 property var history:[]
 property bool historyShown:false
 property bool converting:false
 property bool second:false
 property string conversion:''
 property string category:'Length'
 property string sourceUnit:'m'
 property string targetUnit:'km'
 property var noteResults:[]
 property var rates:({})
 property string rateDate:''
 property string currencyError:''
 property var currencies:['EUR','USD','BRL','GBP','JPY','CAD','AUD','CHF','CNY','INR','KRW','MXN']
 readonly property bool light:Theme.isLight
 readonly property color ink:light ? '#252525':'#ffffff'
 readonly property color secondaryInk:light ? '#80252525':'#a0ffffff'
 readonly property var categories:Object.keys(state.units || {}).concat(['Currency'])
 readonly property var units:category==='Currency' ? currencies:(state.units?.[category] || [])
 function tr(value){return I18n.tr(value)}
 function open(){const wasOpen=opened;window.minimized=false;opened=true;Qt.callLater(()=>keyboard.forceActiveFocus());if(wasOpen)Quickshell.execDetached(['hyprctl','eval','hl.dispatch(hl.dsp.focus({window=\"title:^Quickintosh Calculator$\"}))'])}
 function send(data){if(!ready){pending=pending.concat([data]);return}worker.write(JSON.stringify(data)+'\n')}
 function key(value){send({action:'key',key:value})}
 function changeMode(mode){converting=false;send({action:'mode',mode:mode});modeMenu.close();Qt.callLater(()=>keyboard.forceActiveFocus())}
 function copy(value){copyProcess.command=['wl-copy','--',String(value)];copyProcess.running=true}
 function unitChanged(){conversionDelay.restart()}
 function refreshConversion(){
  if(!converting)return
  if(category==='Currency'){
   if(!rates[sourceUnit] || !rates[targetUnit]){conversion='—';return}
   conversion=String(Number(state.rawValue)*rates[targetUnit]/rates[sourceUnit]);return
  }
  send({action:'convert',category:category,source:sourceUnit,target:targetUnit})
 }
 function resetUnits(){sourceUnit=units[0] || '';targetUnit=units[Math.min(1,units.length-1)] || '';unitChanged();if(category==='Currency' && Object.keys(rates).length===0)ratesProcess.running=true}
 onCategoryChanged:resetUnits()
 onSourceUnitChanged:unitChanged()
 onTargetUnitChanged:unitChanged()
 onConvertingChanged:if(converting){resetUnits();unitChanged()}
 function formatted(value){
  if(state.mode==='programmer')return value
  const parts=String(value).split('.');if(parts[0].indexOf('e')>=0)return value
  const decimal=I18n.lang.startsWith('pt') ? ',':'.',group=decimal===',' ? '.':','
  return parts[0].replace(/\B(?=(\d{3})+(?!\d))/g,group)+(parts.length>1 ? decimal+parts[1]:'')
 }
  function execute(action:string):void{
   if(['basic','scientific','programmer','notes'].includes(action)){app.changeMode(action);app.open()}
   else if(action==='history')app.historyShown=!app.historyShown
   else if(action==='convert')app.converting=!app.converting
   else if(action==='rpn')app.send({action:'rpn'})
   else if(action==='copy')app.copy(app.state.rawValue)
   else if(action==='paste')pasteProcess.running=true
   else if(action==='clear')app.key('AC')
   else if(action==='minimize')window.minimized=true
   else if(action==='close')app.opened=false
  }

 IpcHandler {target:'calculator'
  function open():void{app.open()}
  function command(action:string):void{app.execute(action)}

  function status():string{return JSON.stringify({opened:app.opened,ready:app.ready,mode:app.state.mode,value:app.state.rawValue,history:app.state.history.length})}
 }
 Process {id:worker;running:true;command:['@PYTHON@',Quickshell.shellDir+'/calculator/engine.py']
  stdinEnabled:true
  stdout:SplitParser {onRead:line=>{try{
   const reply=JSON.parse(line)
   if(reply.conversion!==undefined){app.conversion=reply.conversion;return}
   if(reply.noteResults!==undefined){app.noteResults=reply.noteResults;return}
   if(JSON.stringify(reply.history)!==JSON.stringify(app.state.history)){const now=Date.now()/1000;app.history=(reply.history || []).map(item=>Object.assign({},item,{group:app.tr(now-item.time<86400 ? 'Today':now-item.time<7*86400 ? 'Previous 7 Days':'Previous 30 Days')}))}
   app.state=reply
   if(!app.ready){app.ready=true;const requests=app.pending;app.pending=[];for(const request of requests)app.send(request)}
   app.unitChanged()
  }catch(error){console.warn('Calculator response:',error)}}}
  onExited:{app.ready=false;app.state=Object.assign({},app.state,{error:app.tr('Calculator unavailable')});workerRetry.restart()}
 }
 Timer{id:windowSizeDelay;interval:16;onTriggered:{
  if(!app.opened || !window.backingWindowVisible)return
  const scale=Number(Quickshell.env('QT_SCALE_FACTOR') || 1)
  Hyprland.dispatch('hl.dsp.window.resize({window="title:^Quickintosh Calculator$",x='+Math.round(window.implicitWidth*scale)+',y='+Math.round(window.implicitHeight*scale)+',relative=false})')
 }}
 Timer{id:workerRetry;interval:1000;onTriggered:worker.running=true}
 Process{id:copyProcess}
 Process{id:pasteProcess;command:['wl-paste','--no-newline'];stdout:StdioCollector{onStreamFinished:app.send({action:'paste',text:text})}}
 Process{id:ratesProcess;command:['@PYTHON@',Quickshell.shellDir+'/calculator/rates.py'];stdout:StdioCollector{onStreamFinished:{try{const data=JSON.parse(text);app.rates=data.rates || {};if(Object.keys(app.rates).length)app.currencies=Object.keys(app.rates).sort();app.rateDate=data.date || '';app.currencyError=data.error || '';app.unitChanged()}catch(_){app.currencyError=app.tr('Rates unavailable')}}}}
 Timer{id:conversionDelay;interval:30;onTriggered:app.refreshConversion()}
 Timer{id:notesDelay;interval:350;onTriggered:app.send({action:'notes',text:notes.text})}
 component CalcButton:AbstractButton {
  id:button
  required property string label
  property string keyValue:label
  property bool orange:false
  property bool utility:false
  property real textSize:26
  implicitWidth:64;implicitHeight:64
  focusPolicy:Qt.NoFocus
  opacity:enabled ? 1:.35
  Accessible.name:label
  background:Rectangle {
   radius:width/2
   color:button.orange ? (button.down ? '#ffd28a':'#ff9f0a'):button.down ? (app.light ? '#b9b9bf':'#99999f'):button.utility ? (app.light ? '#b0bec5':'#708590a3'):(app.light ? '#c0c5cb':'#507585a0')
   border.width:button.hovered ? 1:0;border.color:app.light ? '#22000000':'#30ffffff'
   Behavior on color{ColorAnimation{duration:75}}
  }
  contentItem:Item {
   Text {anchors.fill:parent;visible:button.keyValue!=='mode';text:button.label;font.family:'SF Pro Display';font.pixelSize:button.textSize;font.weight:Font.Normal;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter;color:button.orange ? 'white':app.ink}
   Image{anchors.centerIn:parent;visible:button.keyValue==='mode';width:25;height:30;source:Quickshell.shellDir+'/calculator/mode.svg';fillMode:Image.PreserveAspectFit}
  }
  onClicked:{if(keyValue==='mode')modeMenu.open();else if(keyValue==='2nd')app.second=!app.second;else if(keyValue==='angle')app.send({action:'degrees'});else app.key(keyValue);keyboard.forceActiveFocus()}
 }
 component SmallButton:AbstractButton {
  id:b
  required property string label
  property url iconSource:''
  property color labelColor:app.ink
  opacity:enabled ? 1:.4
  implicitHeight:28;implicitWidth:Math.max(30,label.length*7+18)
  focusPolicy:Qt.NoFocus
  background:Rectangle{radius:7;color:b.down ? '#30ffffff':b.hovered ? '#18ffffff':'transparent'}
  contentItem:Item{
   Text{anchors.fill:parent;visible:String(b.iconSource).length===0;text:b.label;font.family:'SF Pro Text';font.pixelSize:12;color:b.labelColor;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter}
   Image{anchors.centerIn:parent;visible:String(b.iconSource).length>0;source:b.iconSource;width:18;height:18;fillMode:Image.PreserveAspectFit}
  }
 }
 component CalcMenu:Menu {
  padding:6;implicitWidth:236;modal:false
  font.family:'SF Pro Text';font.pixelSize:13
  background:Rectangle{radius:12;color:app.light ? '#f5f5f7':'#303033';border.width:1;border.color:app.light ? '#18000000':'#30ffffff'}
  enter:Transition{NumberAnimation{property:'opacity';from:0;to:1;duration:100}}
  exit:Transition{NumberAnimation{property:'opacity';from:1;to:0;duration:100}}
 }
 component CalcMenuItem:MenuItem {
  id:entry;implicitHeight:32;implicitWidth:224;padding:0
  property string hint:''
  font.family:'SF Pro Text';font.pixelSize:13
  background:Rectangle{radius:6;color:entry.highlighted ? '#3478f6':'transparent'}
  indicator:Text{x:8;anchors.verticalCenter:parent.verticalCenter;text:'✓';visible:entry.checked;font.family:'SF Pro Text';font.pixelSize:13;color:entry.highlighted ? 'white':app.ink}
  contentItem:Item{
   Text{anchors{left:parent.left;leftMargin:27;right:shortcutText.left;rightMargin:12;verticalCenter:parent.verticalCenter}text:entry.text;font:entry.font;color:!entry.enabled ? app.secondaryInk:entry.highlighted ? 'white':app.ink;elide:Text.ElideRight}
   Text{id:shortcutText;anchors{right:parent.right;rightMargin:9;verticalCenter:parent.verticalCenter}text:entry.hint;font.family:'SF Pro Text';font.pixelSize:12;color:entry.highlighted ? '#ddffffff':app.secondaryInk}
  }
 }
 component CalcSeparator:MenuSeparator{padding:5;contentItem:Rectangle{implicitHeight:1;color:app.light ? '#18000000':'#22ffffff'}}
 component UnitChoice:ComboBox {
  id:choice
  implicitWidth:130;implicitHeight:32;padding:0;leftPadding:0;rightPadding:0;spacing:0
  font.family:'SF Pro Text';font.pixelSize:13
  background:Rectangle{radius:8;color:app.light ? '#16000000':'#15ffffff'}
  contentItem:Text {leftPadding:10;rightPadding:20;text:choice.displayText;color:app.ink;font:choice.font;verticalAlignment:Text.AlignVCenter;elide:Text.ElideRight}
  indicator:Text{x:parent.width-18;y:8;text:'⌄';color:app.secondaryInk}
  delegate:ItemDelegate{id:option;required property var modelData;required property int index;width:ListView.view.width;implicitHeight:32;padding:0;highlighted:choice.highlightedIndex===index;contentItem:Text{leftPadding:10;rightPadding:10;text:option.modelData;font:choice.font;color:option.highlighted ? 'white':app.ink;verticalAlignment:Text.AlignVCenter;elide:Text.ElideRight}background:Rectangle{radius:6;color:option.highlighted ? '#3478f6':'transparent'}}
  popup:Popup{y:choice.height+5;width:Math.max(150,choice.width);padding:5;background:Rectangle{radius:10;color:app.light ? '#f4f4f4':'#303033';border.color:'#25ffffff'}contentItem:ListView{implicitHeight:Math.min(contentHeight,280);model:choice.delegateModel;clip:true;currentIndex:choice.highlightedIndex;ScrollIndicator.vertical:ScrollIndicator{}}}
 }
 FloatingWindow {
  id:window
  visible:app.opened
  title:'Quickintosh Calculator'
  color:'transparent'
  readonly property int sidebarWidth:app.historyShown ? 280:0
  readonly property int mainWidth:app.state.mode==='notes' ? 640:app.state.mode==='scientific' ? 730:app.state.mode==='programmer' ? 590:330
  implicitWidth:mainWidth+sidebarWidth
  implicitHeight:app.state.mode==='notes' ? 570:app.state.mode==='programmer' ? 680:app.converting ? 720:app.state.rpn ? 650:570
  minimumSize:Qt.size(330,570)
  maximumSize:Qt.size(1200,900)
  onVisibleChanged:if(!visible)app.opened=false
  onClosed:app.opened=false
  onImplicitWidthChanged:windowSizeDelay.restart()
  onImplicitHeightChanged:windowSizeDelay.restart()
  onBackingWindowVisibleChanged:if(backingWindowVisible)windowSizeDelay.restart()
  Rectangle {
   anchors.fill:parent;radius:19
   Keys.onPressed:event=>{
    if(!(event.modifiers & Qt.ControlModifier))return
    if(event.key===Qt.Key_W){app.opened=false;event.accepted=true}
    else if([Qt.Key_1,Qt.Key_2,Qt.Key_3].includes(event.key)){app.changeMode(['basic','scientific','programmer'][event.key-Qt.Key_1]);event.accepted=true}
    else if(event.key===Qt.Key_H){app.historyShown=!app.historyShown;event.accepted=true}
   }

   color:Theme.plainSurfaces ? (app.light ? '#e8e8eb':'#292b31'):(app.light ? '#85e8e8ed':'#50232730')
   border.width:1;border.color:app.light ? '#50000000':'#55ffffff'
   Item {
    id:keyboard;anchors.fill:parent;focus:true
    Keys.onPressed:event=>{
     const ctrl=(event.modifiers & Qt.ControlModifier)!==0,alt=(event.modifiers & Qt.AltModifier)!==0
     if(ctrl && !alt && event.key===Qt.Key_C){app.copy(app.state.rawValue);event.accepted=true;return}
     if(ctrl && event.key===Qt.Key_Z){app.send({action:(event.modifiers & Qt.ShiftModifier) ? 'redo':'undo'});event.accepted=true;return}
     if(ctrl && event.key===Qt.Key_V){pasteProcess.running=true;event.accepted=true;return}
     if(ctrl && event.key===Qt.Key_H){app.historyShown=!app.historyShown;event.accepted=true;return}
     if(ctrl && event.key===Qt.Key_R){app.send({action:'rpn'});event.accepted=true;return}
     if(ctrl && event.key===Qt.Key_W){app.opened=false;event.accepted=true;return}
     if(ctrl && [Qt.Key_1,Qt.Key_2,Qt.Key_3].includes(event.key)){app.changeMode(['basic','scientific','programmer'][event.key-Qt.Key_1]);event.accepted=true;return}
     if(ctrl && alt && event.key===Qt.Key_C){app.converting=!app.converting;event.accepted=true;return}
     if(ctrl && alt && event.key===Qt.Key_M){app.changeMode('notes');event.accepted=true;return}
     if(event.key===Qt.Key_Escape){app.key('AC');event.accepted=true;return}
     if(event.key===Qt.Key_Backspace || event.key===Qt.Key_Delete){app.key('⌫');event.accepted=true;return}
     if(event.key===Qt.Key_Return || event.key===Qt.Key_Enter){app.key('=');event.accepted=true;return}
     const t=event.text
     if(!ctrl && app.state.mode==='scientific' && t==='p'){app.key('π');event.accepted=true;return}
     if(!ctrl && app.state.mode==='scientific' && t==='e'){app.key('log');event.accepted=true;return}
     if(/^[0-9A-Fa-f.()+*/%\-^&|~!<>=]$/.test(t)){app.key(t===',' ? '.':t==='*' ? '×':t==='/' ? '÷':t==='-' ? '−':t);event.accepted=true}
     else if(t===','){app.key('.');event.accepted=true}
    }
   }
   Item {
    id:titlebar;height:58;anchors{top:parent.top;left:parent.left;right:parent.right}
    MouseArea{anchors.fill:parent;onPressed:window.startSystemMove();onDoubleClicked:app.historyShown=!app.historyShown}
    Row {id:trafficLights;x:20;y:23;spacing:8
     Repeater {model:['#ff5f57','#febc2e','#55565a']
      Rectangle {required property string modelData;required property int index;width:14;height:14;radius:7;color:modelData
       Text{anchors.fill:parent;text:index===0 ? '×':index===1 ? '−':'';font.family:'SF Pro Text';font.weight:Font.DemiBold;font.pixelSize:12;color:'#95000000';horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter;visible:traffic.containsMouse && index!==2}
       MouseArea{id:traffic;anchors.fill:parent;hoverEnabled:true;enabled:index!==2;onClicked:if(index===0)app.opened=false;else window.minimized=true}
      }
     }
    }
    SmallButton{anchors{right:parent.right;rightMargin:13;verticalCenter:parent.verticalCenter}label:'';iconSource:Quickshell.shellDir+'/assets/icons/notch/sidebar.svg';Accessible.name:app.tr('Show History');onClicked:app.historyShown=!app.historyShown}
   }
   Item {
    id:sidebar;visible:app.historyShown;width:window.sidebarWidth
    anchors{left:parent.left;top:titlebar.bottom;bottom:parent.bottom}
    Rectangle{anchors{right:parent.right;top:parent.top;bottom:parent.bottom}width:1;color:app.light ? '#22000000':'#40000000'}
    Text{visible:app.state.history.length===0;anchors.centerIn:parent;text:app.tr('No calculations yet');color:app.secondaryInk;font.family:'SF Pro Text';font.pixelSize:13}
    ListView{
     id:history;anchors{fill:parent;margins:16;topMargin:35;bottomMargin:15}clip:true;spacing:0
     model:app.history
     section.delegate:Text{required property string section;text:section;color:app.secondaryInk;font.family:'SF Pro Display';font.pixelSize:16;font.weight:Font.DemiBold;height:34;verticalAlignment:Text.AlignVCenter;leftPadding:12}
     section.property:'group';section.criteria:ViewSection.FullString
     delegate:Item {
      required property var modelData;required property int index
      width:history.width;height:88
      Rectangle{anchors.fill:parent;radius:8;color:historyMouse.containsMouse ? '#12ffffff':'transparent'}
      Column{x:14;y:18;width:parent.width-28;spacing:6
       Text{width:parent.width;text:modelData.expression.replace(/\*/g,'×').replace(/\//g,'÷');elide:Text.ElideLeft;color:app.secondaryInk;font.family:'SF Pro Display';font.pixelSize:17}
       Text{width:parent.width;text:app.formatted(modelData.result);elide:Text.ElideLeft;color:app.ink;font.family:'SF Pro Display';font.pixelSize:21}
      }
      Rectangle{anchors{left:parent.left;right:parent.right;bottom:parent.bottom}height:1;color:app.light ? '#15000000':'#18ffffff'}
      MouseArea{id:historyMouse;anchors.fill:parent;hoverEnabled:true;acceptedButtons:Qt.LeftButton|Qt.RightButton;onClicked:event=>{if(event.button===Qt.RightButton){app.selectedHistory=modelData;historyContext.popup()}else{app.send({action:'restore',expression:modelData.expression});keyboard.forceActiveFocus()}}}
     }
     ScrollIndicator.vertical:ScrollIndicator{}
    }
    SmallButton{x:12;y:0;label:app.tr('History');enabled:false}
    SmallButton{anchors.right:parent.right;anchors.rightMargin:10;y:0;label:'';iconSource:Quickshell.shellDir+'/assets/icons/notch/trash.svg';enabled:app.state.history.length>0;Accessible.name:app.tr('Clear history');onClicked:clearHistoryDialog.open()}
   }
   Item {
    id:main;anchors{left:sidebar.right;right:parent.right;top:titlebar.bottom;bottom:parent.bottom}
    visible:app.state.mode!=='notes'
    Item {
     id:display;anchors{left:parent.left;right:parent.right;top:parent.top}height:app.state.mode==='programmer' ? 218:app.converting ? 280:app.state.rpn ? 210:142
     Text {
      anchors{left:parent.left;right:parent.right;rightMargin:22;leftMargin:20;top:parent.top;topMargin:20}
      horizontalAlignment:Text.AlignRight;text:app.state.expression.replace(/\*/g,'×').replace(/\//g,'÷');color:app.secondaryInk
      font.family:'SF Pro Display';font.pixelSize:26;elide:Text.ElideLeft
     }
     Text {
      id:result;anchors{left:parent.left;right:parent.right;rightMargin:20;leftMargin:20;top:parent.top;topMargin:62}
      text:app.state.error ? app.tr('Error'):app.formatted(app.state.value)
      horizontalAlignment:Text.AlignRight;color:app.ink;font.family:'SF Pro Display';font.pixelSize:52;fontSizeMode:Text.Fit;minimumPixelSize:18;height:64
      MouseArea{anchors.fill:parent;acceptedButtons:Qt.RightButton;onClicked:app.copy(app.state.rawValue)}
     }
     Text{x:18;y:111;visible:app.state.error!=='' && app.state.error!==undefined;width:parent.width-36;text:app.state.error || '';elide:Text.ElideRight;font.family:'SF Pro Text';font.pixelSize:11;color:'#ffc36b'}
     Row{visible:app.state.rpn;x:18;y:142;spacing:6
      Repeater{model:[['⇄','swap'],['↑','up'],['↓','down'],['Drop','drop']];SmallButton{required property var modelData;label:modelData[0];onClicked:app.send({action:'stack',key:modelData[1]})}}
      Text{text:app.state.stack.slice(-4).join('   ›   ');font.family:'SF Mono';font.pixelSize:12;color:app.secondaryInk;elide:Text.ElideLeft;width:Math.max(30,display.width-200);anchors.verticalCenter:parent.verticalCenter}
     }
     Column {visible:app.state.mode==='programmer';x:18;y:140;spacing:5
      Row{spacing:6;Repeater{model:[2,8,10,16];SmallButton{required property int modelData;label:({2:'BIN',8:'OCT',10:'DEC',16:'HEX'})[modelData];onClicked:app.send({action:'base',base:modelData});opacity:app.state.base===modelData ? 1:.45}}
       UnitChoice{width:90;model:['8 bit','16 bit','32 bit','64 bit'];currentIndex:[8,16,32,64].indexOf(app.state.bits);onActivated:app.send({action:'bits',bits:[8,16,32,64][currentIndex]})}
      }
      Text{text:'BIN '+(app.state.bases?.['2'] || '')+'   '+(app.state.character ? 'Unicode: '+app.state.character:'');font.family:'SF Mono';font.pixelSize:11;color:app.secondaryInk;elide:Text.ElideLeft;width:main.width-40}
     }
     Grid {visible:app.state.mode==='programmer';x:18;y:198;columns:16;spacing:2
      Repeater{model:app.state.bits || 64
       AbstractButton{required property int index;implicitWidth:(main.width-70)/16;implicitHeight:12;focusPolicy:Qt.NoFocus
        contentItem:Text{text:(app.state.binary || '').charAt(index);horizontalAlignment:Text.AlignHCenter;font.family:'SF Mono';font.pixelSize:10;color:text==='1' ? '#ffbb52':app.secondaryInk}
        onClicked:app.send({action:'toggleBit',bit:app.state.bits-index-1})
       }
      }
     }
     Column {visible:app.converting;x:16;y:137;width:main.width-32;spacing:8
      UnitChoice{width:parent.width;model:app.categories;currentIndex:app.categories.indexOf(app.category);onActivated:app.category=currentText}
      Row{width:parent.width;spacing:6
       UnitChoice{width:(parent.width-44)/2;model:app.units;currentIndex:app.units.indexOf(app.sourceUnit);onActivated:app.sourceUnit=currentText}
       SmallButton{implicitWidth:32;implicitHeight:32;label:'⇄';onClicked:{const old=app.sourceUnit;app.sourceUnit=app.targetUnit;app.targetUnit=old}}
       UnitChoice{width:(parent.width-44)/2;model:app.units;currentIndex:app.units.indexOf(app.targetUnit);onActivated:app.targetUnit=currentText}
      }
      Text{width:parent.width;text:app.formatted(app.conversion)+' '+app.targetUnit;horizontalAlignment:Text.AlignRight;color:app.ink;font.family:'SF Pro Display';font.pixelSize:21;elide:Text.ElideLeft}
      Text{visible:app.category==='Currency';width:parent.width;text:app.currencyError || app.rateDate;color:app.secondaryInk;font.family:'SF Pro Text';font.pixelSize:10;elide:Text.ElideRight}
     }
    }
    Row {
     id:pad;spacing:10;anchors{horizontalCenter:parent.horizontalCenter;bottom:parent.bottom;bottomMargin:18}
     Grid {visible:app.state.mode==='scientific';columns:6;spacing:8
      Repeater {model:app.second ? ['(',')','mc','m+','m−','mr','2nd','square','cube','^','pow2','pow10','reciprocal','sqrt','cbrt','root','log','log2','factorial','asin','acos','atan','e','EE','angle','asinh','acosh','atanh','π','Rand']:['(',')','mc','m+','m−','mr','2nd','square','cube','^','exp','pow10','reciprocal','sqrt','cbrt','root','log','log10','factorial','sin','cos','tan','e','EE','angle','sinh','cosh','tanh','π','Rand']
       CalcButton{required property string modelData;implicitWidth:56;keyValue:modelData;label:({'root':'ʸ√x','square':'x²','cube':'x³','^':'xʸ','sqrt':'√x','cbrt':'∛x','exp':'eˣ','pow10':'10ˣ','pow2':'2ˣ','reciprocal':'1/x','factorial':'x!','angle':app.state.degrees ? 'Rad':'Deg'})[modelData] || modelData;textSize:17}
      }
     }
     Grid {visible:app.state.mode==='programmer';columns:3;spacing:8
      Repeater {model:['A','B','C','D','E','F','&','|','NOT','<<','>>','(' ,')','⊕','mr']
       CalcButton{required property string modelData;implicitHeight:60;keyValue:modelData;label:({'&':'AND','|':'OR','⊕':'XOR'})[modelData] || modelData;textSize:17;enabled:!(/^[A-F]$/.test(modelData)) || app.state.base===16}
      }
     }
     Grid {columns:4;spacing:8
      Repeater {model:['AC','±','%','÷','7','8','9','×','4','5','6','−','1','2','3','+','mode','0','.','=']
       CalcButton{required property string modelData;keyValue:modelData;label:modelData==='mode' ? '▦':modelData==='±' ? '+/−':modelData==='=' && app.state.rpn ? '↵':modelData;implicitHeight:app.state.mode==='programmer' ? 60:64;textSize:modelData==='±' ? 23:modelData==='mode' ? 25:modelData==='=' && app.state.rpn ? 26:29;orange:['÷','×','−','+','='].includes(modelData);utility:['AC','±','%'].includes(modelData);enabled:app.state.mode!=='programmer' || !/^[0-9]$/.test(modelData) || Number(modelData)<app.state.base}
      }
     }
    }
    Text{x:18;y:display.height+3;visible:app.state.memory!=='0' || (!app.state.degrees && app.state.mode==='scientific');text:(app.state.memory!=='0' ? 'M  ':'')+(!app.state.degrees ? 'Rad':'');color:app.secondaryInk;font.family:'SF Pro Text';font.pixelSize:11}
   }
   ColumnLayout {
    visible:app.state.mode==='notes';anchors{left:sidebar.right;right:parent.right;top:titlebar.bottom;bottom:parent.bottom;margins:20}spacing:12
    Text{text:app.tr('Math Notes');font.family:'SF Pro Display';font.pixelSize:25;font.weight:Font.DemiBold;color:app.ink}
    Text{text:app.tr('Write expressions or define variables, one per line.');font.family:'SF Pro Text';font.pixelSize:12;color:app.secondaryInk}
    RowLayout{Layout.fillWidth:true;Layout.fillHeight:true;spacing:14
     ScrollView{Layout.fillWidth:true;Layout.fillHeight:true
      TextArea{id:notes;text:app.state.notes || '';font.family:'SF Mono';font.pixelSize:17;color:app.ink;selectByMouse:true;placeholderTextColor:app.secondaryInk;wrapMode:TextEdit.NoWrap;placeholderText:'coffee = 12\npeople = 4\ncoffee * people\n(2 + 3) * 4';background:Rectangle{radius:12;color:'#0cffffff'}onTextChanged:if(activeFocus)notesDelay.restart()}
     }
     ScrollView{Layout.preferredWidth:170;Layout.fillHeight:true
      Text{text:app.noteResults.join('\n');font.family:'SF Mono';font.pixelSize:17;color:'#ffbb52';lineHeight:1.2}
     }
    }
    SmallButton{label:app.tr('Basic');onClicked:app.changeMode('basic')}
   }
   CalcMenu {
    id:modeMenu;x:Math.max(10,window.width-width-15);y:window.height-height-20
    CalcMenuItem{text:app.tr('Basic');hint:'Ctrl+1';onTriggered:app.changeMode('basic')}
    CalcMenuItem{text:app.tr('Scientific');hint:'Ctrl+2';onTriggered:app.changeMode('scientific')}
    CalcMenuItem{text:app.tr('Programmer');hint:'Ctrl+3';onTriggered:app.changeMode('programmer')}
    CalcSeparator{}
    CalcMenuItem{text:app.tr('Convert');checkable:true;checked:app.converting;enabled:app.state.mode==='basic' || app.state.mode==='scientific';onTriggered:app.converting=!app.converting}
    CalcMenuItem{text:app.tr('RPN Mode');checkable:true;checked:app.state.rpn;enabled:app.state.mode==='basic' || app.state.mode==='scientific';onTriggered:app.send({action:'rpn'})}
    CalcMenuItem{text:app.tr('Show History');checkable:true;checked:app.historyShown;onTriggered:app.historyShown=!app.historyShown}
    CalcSeparator{}
    CalcMenuItem{text:app.tr('Math Notes');onTriggered:app.changeMode('notes')}
    CalcMenuItem{text:app.tr('Copy Result');onTriggered:app.copy(app.state.rawValue)}
   }
   CalcMenu{id:historyContext
    CalcMenuItem{text:app.tr('Copy Result');onTriggered:if(app.selectedHistory)app.copy(app.selectedHistory.result)}
    CalcMenuItem{text:app.tr('Copy Expression');onTriggered:if(app.selectedHistory)app.copy(app.selectedHistory.expression)}
    CalcSeparator{}
    CalcMenuItem{text:app.tr('Delete');onTriggered:if(app.selectedHistory)app.send({action:'deleteHistory',time:app.selectedHistory.time})}
   }
   Popup{
    id:clearHistoryDialog;anchors.centerIn:parent;width:292;padding:22;modal:true;focus:true
    closePolicy:Popup.CloseOnEscape
    background:Rectangle{radius:18;color:app.light ? '#f1f1f3':'#303033';border.width:1;border.color:app.light ? '#20000000':'#30ffffff'}
    Overlay.modal:Rectangle{color:'#28000000'}
    enter:Transition{NumberAnimation{property:'opacity';from:0;to:1;duration:120}}
    exit:Transition{NumberAnimation{property:'opacity';from:1;to:0;duration:100}}
    contentItem:Column{
     spacing:20
     Text{width:parent.width;text:app.tr('Clear history?');wrapMode:Text.WordWrap;font.family:'SF Pro Display';font.pixelSize:17;font.weight:Font.DemiBold;color:app.ink;horizontalAlignment:Text.AlignHCenter}
     Row{spacing:10
      SmallButton{implicitWidth:119;implicitHeight:32;label:app.tr('Cancel');background:Rectangle{radius:8;color:app.light ? '#ffffff':'#555558'}onClicked:clearHistoryDialog.close()}
      SmallButton{implicitWidth:119;implicitHeight:32;label:app.tr('Clear history');labelColor:'white';background:Rectangle{radius:8;color:'#3478f6'}onClicked:{app.send({action:'clearHistory'});clearHistoryDialog.close()}}
     }
    }
   }
  }
 }
}
