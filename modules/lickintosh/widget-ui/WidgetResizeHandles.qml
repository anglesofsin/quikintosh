import QtQuick
import qs.services
Item {
 id:root
 z:1000
 required property var slot
 required property var stage
 visible:WidgetState.galleryZone==='desktop' || WidgetState.resizingId===slot.spec.id || root.active
 property bool active:false
 property point startPoint
 property real startWidth:0
 property real startHeight:0
 signal finished()
 function cancel(){root.slot.resizing=false;root.active=false}
 Connections{
  target:WidgetState
  function onResizingIdChanged(){if(root.active && WidgetState.resizingId!==root.slot.spec.id && WidgetState.galleryZone!=='desktop')root.cancel()}
  function onGalleryZoneChanged(){if(root.active && WidgetState.resizingId!==root.slot.spec.id && WidgetState.galleryZone!=='desktop')root.cancel()}
 }
 Repeater {
  model:['x','y','xy']
  delegate:Rectangle {
   id:handle
   required property string modelData
   width:12;height:12;radius:4;z:1000;color:Theme.accent;border.width:1;border.color:'#e0ffffff'
   x:modelData==='y' ? (root.width-width)/2:root.width-width
   y:modelData==='x' ? (root.height-height)/2:root.height-height
   MouseArea{
    anchors.fill:parent;anchors.margins:-5;preventStealing:true
    cursorShape:handle.modelData==='x' ? Qt.SizeHorCursor:handle.modelData==='y' ? Qt.SizeVerCursor:Qt.SizeFDiagCursor
    onPressed:mouse=>{
     root.startPoint=mapToItem(root.stage,mouse.x,mouse.y);root.startWidth=root.slot.width;root.startHeight=root.slot.height
     root.slot.resizeWidth=root.startWidth;root.slot.resizeHeight=root.startHeight;root.slot.resizing=true;root.active=true
    }
    onPositionChanged:mouse=>{
     if(!pressed || !root.active)return
     const p=mapToItem(root.stage,mouse.x,mouse.y)
     if(handle.modelData!=='y')root.slot.resizeWidth=Math.max(100,Math.min(root.stage.width-root.slot.x,root.startWidth+p.x-root.startPoint.x))
     if(handle.modelData!=='x')root.slot.resizeHeight=Math.max(72,Math.min(root.stage.height-root.slot.y,root.startHeight+p.y-root.startPoint.y))
    }
    onReleased:mouse=>{
     if(!root.active)return
     const id=root.slot.spec.id,w=root.slot.resizeWidth,h=root.slot.resizeHeight,free=!!(mouse.modifiers & Qt.ControlModifier)
     root.cancel();if(WidgetState.resizingId===id)WidgetState.resizingId="";root.finished()
     WidgetState.resizeWidgetTo(id,w,h,free)
    }
    onCanceled:{root.cancel();if(WidgetState.resizingId===root.slot.spec.id)WidgetState.resizingId=""}
   }
  }
 }
 Rectangle{anchors.fill:parent;anchors.margins:-1;radius:22;color:'transparent';border.width:1;border.color:Theme.accent;z:-1}
}
