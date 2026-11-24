import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import qs.services
import qs.components
import qs.components.glass
Item {
 id:root
 property string activeTarget:'desktop'
 property string group:'personal'
 property string query:''
 readonly property var shown:{
  let list=group==='shipped' ? WallpaperLibrary.shipped:WallpaperLibrary.personal
  if(group==='video')list=list.filter(item=>item.video)
  else list=list.filter(item=>!item.video)
  const q=query.toLowerCase();return q ? list.filter(item=>item.name.toLowerCase().includes(q)):list
 }
 function pathOf(target){if(target==='lockscreen')return ShellConfig.options.wallpaper.lockscreenPath;if(target==='desktopLight')return ShellConfig.options.wallpaper.pathLight;if(target==='desktopDark')return ShellConfig.options.wallpaper.pathDark;return ShellConfig.options.wallpaper.path}
 readonly property string currentPath:root.pathOf(root.activeTarget)
 function apply(item){
  if(item.video){ShellConfig.options.wallpaper.videoPath=item.path;root.activeTarget='desktop';return}
  if(root.activeTarget==='lockscreen')ShellConfig.options.wallpaper.lockscreenPath=item.path
  else if(root.activeTarget==='desktopLight')ShellConfig.options.wallpaper.pathLight=item.path
  else if(root.activeTarget==='desktopDark')ShellConfig.options.wallpaper.pathDark=item.path
  else{ShellConfig.options.wallpaper.videoPath='';ShellConfig.options.wallpaper.path=item.path}
 }
 ColumnLayout{
  anchors.fill:parent;anchors.margins:24;spacing:16
  RowLayout{
   Layout.fillWidth:true
   Text{text:'Wallpaper';font.family:'SF Pro Display';font.pixelSize:24;font.weight:Font.DemiBold;color:Theme.textPrimary;Layout.fillWidth:true}
   Button{text:'Refresh';onClicked:WallpaperLibrary.refresh()}
  }
  RowLayout{
   Layout.fillWidth:true;spacing:12
   Repeater{
    model:[{key:'desktop',label:'Desktop'},{key:'desktopLight',label:'Light'},{key:'desktopDark',label:'Dark'},{key:'lockscreen',label:'Lock Screen'}]
    delegate:ColumnLayout{
     required property var modelData
     Layout.fillWidth:true;Layout.preferredWidth:1;spacing:6
     Rectangle{
      Layout.fillWidth:true;Layout.preferredHeight:66;radius:10;clip:true;color:Theme.isLight ? '#e0e0e5':'#24252c'
      Image{anchors.fill:parent;source:root.pathOf(modelData.key) ? QuickLookState.urlFor(root.pathOf(modelData.key)):'';sourceSize:Qt.size(240,132);fillMode:Image.PreserveAspectCrop;asynchronous:true}
      Rectangle{anchors.fill:parent;radius:10;color:'transparent';border.width:root.activeTarget===modelData.key ? 2:1;border.color:root.activeTarget===modelData.key ? Theme.accent:'#30ffffff'}
      MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:root.activeTarget=modelData.key}
     }
     Text{Layout.alignment:Qt.AlignHCenter;text:modelData.label;font.pixelSize:11;color:root.activeTarget===modelData.key ? Theme.textPrimary:Theme.textSecondary}
    }
   }
  }
  RowLayout{
   Layout.fillWidth:true;spacing:8
   Repeater{model:[{key:'personal',label:'Your Photos'},{key:'shipped',label:'Collections'},{key:'video',label:'Videos'}]
    delegate:Button{required property var modelData;text:modelData.label;checkable:true;checked:root.group===modelData.key;onClicked:{root.group=modelData.key;grid.positionViewAtBeginning()}}
   }
   Item{Layout.fillWidth:true}
   Button{text:'Shuffle';enabled:root.shown.length>0;onClicked:root.apply(root.shown[Math.floor(Math.random()*root.shown.length)])}
  }
  TextField{id:search;Layout.fillWidth:true;placeholderText:'Search wallpapers';selectByMouse:true;onTextChanged:filterDelay.restart()}
  Timer{id:filterDelay;interval:100;onTriggered:{root.query=search.text;grid.positionViewAtBeginning()}}
  GridView{
   id:grid;Layout.fillWidth:true;Layout.fillHeight:true;clip:true
   cellWidth:Math.floor(width/Math.max(2,Math.floor(width/166)));cellHeight:128
   cacheBuffer:128;reuseItems:true;boundsBehavior:Flickable.StopAtBounds
   model:root.shown
   ScrollBar.vertical:ScrollBar{}
   delegate:Item{
    id:tile;required property var modelData;width:grid.cellWidth;height:grid.cellHeight
    readonly property string thumb:WallpaperLibrary.thumbnails[modelData.path] || ''
    readonly property bool inView:y+height>=grid.contentY && y<=grid.contentY+grid.height
    onInViewChanged:if(inView)WallpaperLibrary.request(modelData.path)
    onModelDataChanged:if(inView)WallpaperLibrary.request(modelData.path)
    Component.onCompleted:if(inView)WallpaperLibrary.request(modelData.path)
    Rectangle{
     anchors.left:parent.left;anchors.right:parent.right;anchors.top:parent.top;anchors.margins:5;height:99;radius:10;clip:true;color:Theme.isLight ? '#dadce2':'#24262e'
     Image{anchors.fill:parent;source:tile.thumb;sourceSize:Qt.size(320,198);fillMode:Image.PreserveAspectCrop;asynchronous:true;cache:true}
     Text{anchors.centerIn:parent;text:modelData.video ? '▶':'◈';visible:!tile.thumb;color:Theme.textSecondary;font.pixelSize:22}
     Rectangle{anchors.fill:parent;radius:10;color:mouse.containsMouse ? '#18ffffff':'transparent';border.width:root.currentPath===modelData.path || ShellConfig.options.wallpaper.videoPath===modelData.path ? 2:1;border.color:root.currentPath===modelData.path || ShellConfig.options.wallpaper.videoPath===modelData.path ? Theme.accent:'#24ffffff'}
     MouseArea{id:mouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:root.apply(modelData)}
    }
    Text{anchors.left:parent.left;anchors.right:parent.right;anchors.bottom:parent.bottom;anchors.margins:6;height:16;text:modelData.name;font.family:'SF Pro Text';font.pixelSize:11;color:Theme.textSecondary;horizontalAlignment:Text.AlignHCenter;elide:Text.ElideMiddle}
   }
   Text{anchors.centerIn:parent;text:WallpaperLibrary.loaded ? 'No wallpapers found':'Loading wallpapers…';visible:grid.count===0;color:Theme.textSecondary}
  }
  Text{Layout.fillWidth:true;text:root.shown.length+' wallpapers · '+(root.group==='shipped' ? 'Built-in collections':WallpaperLibrary.userDir);font.pixelSize:11;color:Theme.textSecondary;elide:Text.ElideMiddle}
 }
}
