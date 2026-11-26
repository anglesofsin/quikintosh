import QtQuick
import QtQuick.Effects
import qs.services
Item {
 id:root
 property var entry:({})
 property var thumbnailMap:({})
 readonly property bool previewStack:!!entry.stack && entry.display!=='folder' && entry.previews && entry.previews.length>0
 property int iconSize:52
 property bool dropTarget:false
 property real dropScale:dropTarget ? 1.06:1
 Behavior on dropScale{NumberAnimation{duration:110;easing.type:Easing.OutCubic}}
 property real zoom:1
 property bool vertical:false
 property bool indicators:true
 property bool animateLaunch:true
 property bool dragging:false
 property bool suppressClick:false
 property real pressX:0
 property real pressY:0
 signal activated(int modifiers)
 signal contextRequested()
 signal hovered(bool on)
 property real dragSceneX:0
 property real dragSceneY:0
 function updateDragPosition(){
  if(!root.dragging)return
  const p=root.mapFromItem(null,root.dragSceneX,root.dragSceneY)
  root.dragOffsetX=p.x-artwork.x-artwork.width/2
  root.dragOffsetY=p.y-artwork.y-artwork.height/2
 }
 FrameAnimation{running:root.dragging;onTriggered:root.updateDragPosition()}
 property real dragOffsetX:0
 property real dragOffsetY:0
 signal dragMoved(real delta,real outside)
 signal dragFinished(real delta,real outside)
 width:vertical ? iconSize+16 : iconSize+8
 height:vertical ? iconSize+12 : iconSize+16
 property real bounce:0
 SequentialAnimation {id:bouncer;loops:2;NumberAnimation{target:root;property:'bounce';to:16;duration:150;easing.type:Easing.OutQuad}NumberAnimation{target:root;property:'bounce';to:0;duration:200;easing.type:Easing.InQuad}}
 function launch(){if(animateLaunch && entry.kind==='app' && !entry.running)bouncer.restart()}
 Item {
  id:artwork
  x:(parent.width-width)/2;y:root.vertical ? (parent.height-height)/2:parent.height-8-height
  transformOrigin:root.vertical ? (ShellConfig.options.dockAppearance.position==='right' ? Item.Right:Item.Left):Item.Bottom
  width:root.iconSize;height:width;scale:root.dragging ? 1:root.zoom*root.dropScale
  transform:Translate{y:(!root.dragging && !root.vertical ? -root.bounce : 0)+root.dragOffsetY;x:(!root.dragging && root.vertical ? root.bounce : 0)+root.dragOffsetX;Behavior on x{enabled:!root.dragging;NumberAnimation{duration:160;easing.type:Easing.OutCubic}}Behavior on y{enabled:!root.dragging;NumberAnimation{duration:160;easing.type:Easing.OutCubic}}}
  Image {asynchronous:true;visible:!root.previewStack;anchors.fill:parent;anchors.margins:-ShellConfig.options.dockAppearance.iconOverflow;source:root.entry.icon || '';sourceSize:Qt.size(128,128);smooth:true;mipmap:true;fillMode:Image.PreserveAspectFit
   layer.enabled:ShellConfig.options.dockAppearance.monochromeIcons || ShellConfig.options.dockAppearance.iconTint
   layer.effect:MultiEffect{saturation:ShellConfig.options.dockAppearance.monochromeIcons ? -1 : 0;colorization:ShellConfig.options.dockAppearance.iconTint ? ShellConfig.options.dockAppearance.iconTintStrength : 0;colorizationColor:ShellConfig.options.dockAppearance.iconTintColor}
  }
  Repeater {
   model:root.previewStack ? root.entry.previews.slice(0,3) : []
   Item {
    required property var modelData;required property int index
    width:parent.width;height:parent.height;z:3-index
    x:index*2;y:-index*3;rotation:index===0 ? 0 : -index*5
    Image{id:preview;anchors.fill:parent;source:root.thumbnailMap[parent.modelData.path] || parent.modelData.thumbnail || (parent.modelData.image ? 'file://'+parent.modelData.path.split('/').map(encodeURIComponent).join('/') : parent.modelData.directory ? IconResolver.forFolder() : IconResolver.forFile(parent.modelData.name));sourceSize:Qt.size(128,128);fillMode:Image.PreserveAspectFit;asynchronous:true;smooth:true;mipmap:true}

   }
  }
  Text {anchors.right:parent.right;anchors.bottom:parent.bottom;visible:!!root.entry.stack;text:'⌃';color:'white';font.pixelSize:18;style:Text.Outline;styleColor:'#50000000'}
 }
 Rectangle {width:4;height:4;radius:2;color:Theme.textPrimary;visible:root.indicators && !!root.entry.running;x:root.vertical ? 1 : (parent.width-width)/2;y:root.vertical ? (parent.height-height)/2 : parent.height-3}
 MouseArea {
  id:mouse;x:root.vertical ? -root.iconSize*(root.zoom-1)/2:-root.iconSize*(root.zoom-1)/2;y:root.vertical ? -root.iconSize*(root.zoom-1)/2:-root.iconSize*(root.zoom-1);width:root.width+root.iconSize*(root.zoom-1);height:root.height+root.iconSize*(root.zoom-1);hoverEnabled:true;acceptedButtons:Qt.LeftButton|Qt.RightButton;cursorShape:Qt.PointingHandCursor
  onEntered:root.hovered(true)
  onExited:root.hovered(false)
  onPressed:m=>{const p=mouse.mapToItem(null,m.x,m.y);root.pressX=p.x;root.pressY=p.y;root.dragging=false;root.suppressClick=false}
  onPositionChanged:m=>{const p=mouse.mapToItem(null,m.x,m.y);if(pressedButtons===Qt.LeftButton && Math.hypot(p.x-root.pressX,p.y-root.pressY)>10){root.dragSceneX=p.x;root.dragSceneY=p.y;root.dragging=true;root.updateDragPosition();root.dragMoved(root.vertical ? p.y-root.pressY:p.x-root.pressX,root.vertical ? Math.abs(p.x-root.pressX):Math.abs(p.y-root.pressY))}}
  onReleased:m=>{if(root.dragging){root.suppressClick=true;const p=mouse.mapToItem(null,m.x,m.y);root.dragFinished(root.vertical ? p.y-root.pressY : p.x-root.pressX,root.vertical ? Math.abs(p.x-root.pressX) : Math.abs(p.y-root.pressY));root.dragging=false;root.dragOffsetX=0;root.dragOffsetY=0}}
  onCanceled:{root.dragging=false;root.dragOffsetX=0;root.dragOffsetY=0;root.dragFinished(0,0)}
  onClicked:m=>{if(root.suppressClick){root.suppressClick=false;return}if(m.button===Qt.RightButton)root.contextRequested();else {root.launch();root.activated(m.modifiers)}}
 }
}
