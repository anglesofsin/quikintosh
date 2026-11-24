pragma Singleton
import Quickshell
import Quickshell.Io
import qs.services
Singleton {
 id:root
 property var icons:({})
 FileView {path:Quickshell.shellDir+'/tahoedock/icons.json';onLoaded:{try{root.icons=JSON.parse(text())}catch(e){console.warn('Dock icons:',e)}}}
 function byName(name){
  const theme=Theme.isLight ? 'MacTahoe-light':'MacTahoe-dark'
  let path=root.icons[theme+':'+name]
  if(!path && name && name.endsWith('.desktop'))path=root.icons[theme+':'+name.slice(0,-8)]
  return path ? 'file://'+Quickshell.shellDir+'/'+path : IconResolver.byName(name)
 }
 function forApp(app){return app && app.icon ? byName(app.icon) : ''}
 function forAppId(id){return forApp(DesktopEntries.heuristicLookup(id))}
}
