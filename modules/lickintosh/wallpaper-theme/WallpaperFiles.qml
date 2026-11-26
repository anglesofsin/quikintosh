pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
Singleton {
 id:root
 property var sources:({})
 property bool enabled:false
 function resolve(name){return root.enabled && root.sources[name] ? 'file://'+root.sources[name]:''}
 function forSource(source){
  const value=String(source || '')
  if(value.indexOf('image://icon/')!==0 && !/\/(?:places|mimes)(?:@2x)?\//.test(value))return ''
  const name=value.split('/').pop().split('?')[0].replace(/\.(svg|png)$/,'')
  return root.resolve(name)
 }
 FileView{
  path:Quickshell.env('HOME')+'/.local/state/lickintosh/theming/finder.json'
  watchChanges:true
  onFileChanged:reload()
  onLoaded:{try{const data=JSON.parse(text());root.sources=data.icons || ({});root.enabled=data.iconsEnabled===true}catch(e){root.sources=({});root.enabled=false}}
 }
}
