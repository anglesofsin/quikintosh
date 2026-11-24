import QtQuick
import Quickshell
import Quickshell.Widgets
import qs.services
Item {
 id:root
 property url source
 property color foreground:TopBarStyle.colorFor(QsWindow.window?.screen,'right')
 readonly property bool monochrome:probe.monochrome
 IconImage {
  anchors.fill:parent
  source:root.source
  layer.enabled:root.monochrome
  layer.smooth:true
  layer.effect:ShaderEffect {
   property var source
   property color tint:root.foreground
   fragmentShader:Quickshell.shellDir+'/components/bar-tint.frag.qsb'
  }
 }
 // Analyze each new icon once, at icon-sized resolution. Recoloring the bar
 // itself never rereads pixels, and colored application artwork is preserved.
 Canvas {
  id:probe;width:32;height:32;opacity:0
  property bool monochrome:false
  property string loaded:''
  function reload(){
   const next=String(root.source)
   if(loaded===next)return
   if(loaded)unloadImage(loaded)
   loaded=next;monochrome=false
   if(loaded){loadImage(loaded,Qt.size(32,32));if(isImageLoaded(loaded))requestPaint()}
  }
  Component.onCompleted:reload()
  Connections{target:root;function onSourceChanged(){probe.reload()}}
  onImageLoaded:requestPaint()
  onPaint:{
   if(!loaded || !isImageLoaded(loaded))return
   const ctx=getContext('2d');ctx.clearRect(0,0,width,height);ctx.drawImage(loaded,0,0,width,height)
   const pixels=ctx.getImageData(0,0,width,height).data
   let visible=0,colored=0
   for(let i=0;i<pixels.length;i+=4){
    if(pixels[i+3]<40)continue
    visible++
    const hi=Math.max(pixels[i],pixels[i+1],pixels[i+2]),lo=Math.min(pixels[i],pixels[i+1],pixels[i+2])
    if(hi-lo>24 && (hi-lo)/Math.max(1,hi)>.16)colored++
   }
   monochrome=visible>0 && colored<=Math.max(1,visible*.008)
  }
 }
}
