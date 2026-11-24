//@ pragma AppId org.lickintosh.Settings
pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.components
import qs.components.glass
import qs.services
import qs.settingsapp
FloatingWindow{
 id:window
 visible:true;title:'Settings';implicitWidth:1000;implicitHeight:740;minimumSize:Qt.size(820,560);color:'transparent'
 property string route:'general'
 property string query:''
 property var history:['general']
 property int historyIndex:0
 property bool initialized:false
 SettingsWindowGlass{id:windowGlass;host:window}
 readonly property var page:SettingsCatalog.page(route)
 readonly property bool canBack:historyIndex>0
 readonly property bool canForward:historyIndex<history.length-1
 function navigate(id,record){
  const next=SettingsCatalog.resolve(id)
  if(route===next && !query)return
  if(record!==false){const stack=history.slice(0,historyIndex+1);stack.push(next);history=stack;historyIndex=stack.length-1}
  route=next;query='';search.text='';SettingsPreferences.lastPage=next
 }
 function back(){if(canBack){historyIndex--;navigate(history[historyIndex],false)}}
 function forward(){if(canForward){historyIndex++;navigate(history[historyIndex],false)}}
 function initialize(){if(initialized || !SettingsPreferences.ready || !SettingsCatalog.pages.length)return;initialized=true;const wanted=Quickshell.env('LICKINTOSH_PAGE') || SettingsPreferences.lastPage;route=SettingsCatalog.resolve(wanted);history=[route];historyIndex=0}
 Component.onCompleted:{Quickshell.watchFiles=false;Theme.applyToCompositor=false;initialize()}
 Connections{target:SettingsPreferences;function onReadyChanged(){window.initialize()}}
 Connections{target:SettingsCatalog;function onPagesChanged(){window.initialize()}}
 IpcHandler{
  target:'settingsWindow'
  function open(page:string):void{if(page)window.navigate(page);window.minimized=false;window.visible=false;Qt.callLater(()=>window.visible=true)}
  function navigate(page:string):void{window.navigate(page)}
  function state():string{return JSON.stringify({page:window.route,title:window.page?.title,history:window.history,position:window.historyIndex,search:window.query,loaded:loader.status===Loader.Ready,error:SettingsState.error,loadError:loader.status===Loader.Error,glassReady:windowGlass.captureSettled,owner:SettingsState.ownerPid,ownAddress:windowGlass.own.address || '',pages:SettingsCatalog.pages.map(p=>p.id)})}
 }
 Shortcut{sequence:'Ctrl+F';onActivated:search.forceActiveFocus()}
 Shortcut{sequence:'Alt+Left';onActivated:window.back()}
 Shortcut{sequence:'Alt+Right';onActivated:window.forward()}
 Shortcut{sequence:'Escape';enabled:!!window.query;onActivated:{search.text='';window.query=''}}
 Dialog{
  id:pageHelp;parent:Overlay.overlay;anchors.centerIn:parent;width:Math.min(480,window.width-64);modal:true;focus:true;header:null;padding:24
  background:Rectangle{radius:18;color:Theme.isLight ? '#f6f6f8':'#28292d';border.width:1;border.color:Theme.cardRim}
  contentItem:ColumnLayout{spacing:18
   Text{Layout.fillWidth:true;text:window.page?.title || 'Settings';font.pixelSize:18;font.bold:true;color:Theme.textPrimary}
   Text{Layout.fillWidth:true;text:loader.item?.helpText || 'Use the controls on this page to customize Lickintosh.';wrapMode:Text.WordWrap;font.pixelSize:13;color:Theme.textSecondary}
   TahoeButton{Layout.alignment:Qt.AlignRight;text:'Done';onClicked:pageHelp.close()}
  }
 }
 Rectangle{
  width:window.width/scale;height:window.height/scale;scale:SettingsPreferences.accessibility.textScale;transformOrigin:Item.TopLeft;radius:18;color:Theme.isLight ? '#fafafa':'#1c1c1e';clip:true
  RowLayout{
   anchors.fill:parent;spacing:0
   Rectangle{
    Layout.preferredWidth:248;Layout.fillHeight:true;Layout.margins:9;Layout.rightMargin:0;radius:16
    color:Theme.isLight ? '#e9e9ed':'#28282d';border.width:1;border.color:Theme.isLight ? '#12000000':'#14ffffff'
    TahoeGlass{anchors.fill:parent;backdrop:windowGlass;cornerRadius:16;visible:windowGlass.captureSettled && windowGlass.ready}
    Rectangle{anchors.fill:parent;radius:16;color:Theme.isLight ? '#b8e9e9ed':'#b828282d';visible:windowGlass.captureSettled && windowGlass.ready}
    ColumnLayout{
     anchors.fill:parent;anchors.margins:11;spacing:10
     Item{
      Layout.fillWidth:true;Layout.preferredHeight:33
      MouseArea{anchors.fill:parent;onPressed:window.startSystemMove()}
      Row{anchors.left:parent.left;anchors.verticalCenter:parent.verticalCenter;anchors.leftMargin:6;spacing:8
       Repeater{model:['#ff5f57','#febc2e','#28c840'];delegate:Rectangle{
        required property string modelData;required property int index;width:12;height:12;radius:6;color:modelData
        Text{anchors.centerIn:parent;text:parent.index===0 ? '×':parent.index===1 ? '−':'+';visible:lights.containsMouse;color:'#80000000';font.pixelSize:11}
        MouseArea{id:lights;anchors.fill:parent;hoverEnabled:true;onClicked:{if(index===0)window.visible=false;else if(index===1)window.minimized=true;else window.maximized=!window.maximized}}
       }}
      }
     }
     TahoeField{id:search;Layout.fillWidth:true;placeholderText:'Search';text:window.query;onTextEdited:window.query=text;Accessible.name:'Search settings'}
     ListView{
      id:sidebar;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:1;cacheBuffer:100;reuseItems:true
      model:SettingsCatalog.sidebar
      ScrollBar.vertical:ScrollBar{policy:ScrollBar.AsNeeded}
      delegate:Item{
       id:entry;required property var modelData;required property int index;width:sidebar.width;height:(index>0 && SettingsCatalog.sidebar[index-1].group!==modelData.group ? 14:0)+(modelData.id==='account' ? 64:35)
       readonly property bool selected:SettingsCatalog.parentPage(window.route)===modelData.id && !window.query
       Rectangle{
        anchors{left:parent.left;right:parent.right;bottom:parent.bottom}height:modelData.id==='account' ? 60:35;radius:7;color:entry.selected ? Theme.accent:itemMouse.containsMouse ? Theme.isLight ? '#10000000':'#15ffffff':'transparent'
        RowLayout{anchors.fill:parent;anchors.leftMargin:7;anchors.rightMargin:7;spacing:9
         ProfileAvatar{visible:modelData.id==='account';Layout.preferredWidth:40;Layout.preferredHeight:40;source:SettingsPreferences.profile.avatar ? QuickLookState.urlFor(SettingsPreferences.profile.avatar):Quickshell.shellDir+'/assets/icons/settings/user.svg'}
         Image{visible:modelData.id!=='account';Layout.preferredWidth:modelData.id==='account' ? 40:23;Layout.preferredHeight:width;source:modelData.id==='account' && SettingsPreferences.profile.avatar ? QuickLookState.urlFor(SettingsPreferences.profile.avatar):Quickshell.shellDir+'/assets/icons/settings/'+modelData.icon;fillMode:Image.PreserveAspectFit;sourceSize:Qt.size(64,64);asynchronous:true}
         ColumnLayout{Layout.fillWidth:true;spacing:3
          Text{Layout.fillWidth:true;text:modelData.id==='account' ? SettingsPreferences.profile.displayName || SettingsState.data.system?.fullName || 'Your Account':modelData.title;font.family:'SF Pro Text';font.pixelSize:13;font.weight:modelData.id==='account' ? Font.DemiBold:Font.Normal;color:entry.selected ? 'white':Theme.textPrimary;elide:Text.ElideRight}
          Text{visible:modelData.id==='account';text:'Local Account';font.pixelSize:10;color:entry.selected ? '#dfffffff':Theme.textSecondary}
         }
        }
        MouseArea{id:itemMouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:window.navigate(modelData.id)}
       }
      }
     }
    }
   }
   Item{
    Layout.fillWidth:true;Layout.fillHeight:true
    ColumnLayout{
     anchors.fill:parent;spacing:0
     Item{
      Layout.fillWidth:true;Layout.preferredHeight:74
      MouseArea{anchors.fill:parent;onPressed:window.startSystemMove()}
      RowLayout{anchors.fill:parent;anchors.leftMargin:24;anchors.rightMargin:24;spacing:13
       RowLayout{spacing:2
        TahoeButton{text:'‹';implicitWidth:28;enabled:window.canBack;onClicked:window.back()}
        TahoeButton{text:'›';implicitWidth:28;enabled:window.canForward;onClicked:window.forward()}
       }
       Text{Layout.fillWidth:true;text:window.query ? 'Search Results':window.page?.title || 'Settings';font.family:'SF Pro Display';font.pixelSize:23;font.weight:Font.Bold;color:Theme.textPrimary;elide:Text.ElideRight}
       TahoeButton{text:'?';implicitWidth:28;onClicked:pageHelp.open()}
      }
     }
     Rectangle{Layout.fillWidth:true;visible:!!SettingsState.error;implicitHeight:errorLabel.implicitHeight+24;color:Theme.isLight ? '#18ff453a':'#28ff453a'
      Text{id:errorLabel;anchors{left:parent.left;right:parent.right;top:parent.top;margins:12}text:SettingsState.error;color:Theme.textPrimary;font.pixelSize:12;wrapMode:Text.WordWrap}
     }
     Loader{
      id:loader;Layout.fillWidth:true;Layout.fillHeight:true;Layout.bottomMargin:18;active:!window.query;asynchronous:false
      source:!window.page ? '':window.page.legacy ? Quickshell.shellDir+'/ui/settings/pages/'+window.page.legacy+'.qml':Quickshell.shellDir+'/settingsapp/SettingsContent.qml'
      onLoaded:{if(item.hasOwnProperty('pageId'))item.pageId=Qt.binding(()=>window.route);if(item.navigate && item.navigate.connect)item.navigate.connect(id=>window.navigate(id));if(item.hasOwnProperty('goToControlCenterPage'))item.goToControlCenterPage.connect(()=>window.navigate('controlcenter'))}
     }
     Text{
      Layout.fillWidth:true;Layout.leftMargin:24;Layout.rightMargin:24
      visible:loader.status===Loader.Error && !window.query
      text:'This page could not be loaded. Reopen Settings after updating the shell.'
      color:Theme.textSecondary;wrapMode:Text.WordWrap
     }
     ListView{
      Layout.fillWidth:true;Layout.fillHeight:true;Layout.leftMargin:24;Layout.rightMargin:24;visible:!!window.query;clip:true;spacing:7
      model:SettingsCatalog.search(window.query)
      delegate:Rectangle{
       required property var modelData;width:ListView.view.width;height:66;radius:11;color:resultMouse.containsMouse ? Theme.fillHover:Theme.card
       Column{anchors{left:parent.left;right:parent.right;verticalCenter:parent.verticalCenter;leftMargin:14;rightMargin:30}spacing:4
        Text{text:modelData.title;font.pixelSize:14;font.family:'SF Pro Text';color:Theme.textPrimary}
        Text{width:parent.width;text:modelData.parent ? (SettingsCatalog.page(modelData.parent)?.title || '')+' › '+modelData.title:modelData.keywords;font.pixelSize:11;color:Theme.textSecondary;elide:Text.ElideRight}
       }
       Text{anchors{right:parent.right;verticalCenter:parent.verticalCenter;rightMargin:12}text:'›';font.pixelSize:22;color:Theme.textSecondary}
       MouseArea{id:resultMouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:window.navigate(modelData.id)}
      }
     }
    }
   }
  }
 }
}
