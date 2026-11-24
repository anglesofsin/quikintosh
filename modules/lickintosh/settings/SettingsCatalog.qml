pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
Singleton{
 id:root
 property var pages:[]
 readonly property var sidebar:pages.filter(page=>!page.parent)
 FileView{path:Quickshell.shellDir+'/settingsapp/catalog.json';onLoaded:{try{root.pages=JSON.parse(text())}catch(error){console.warn('Settings catalog:',error)}}}
 function page(id){return pages.find(item=>item.id===id) || null}
 function resolve(id){const aliases={AccountPage:'account',GeneralPage:'general',AppearancePage:'appearance',SoundPage:'sound',NotificationsPage:'notifications'};return page(id)?.id || aliases[id] || pages.find(item=>item.legacy===id)?.id || 'general'}
 function childPages(id){return pages.filter(item=>item.parent===id)}
 function parentPage(id){const item=page(id);return item?.parent || id}
 function search(query){const words=query.toLowerCase().trim().split(/\s+/);if(!query.trim())return [];return pages.filter(page=>words.every(word=>(page.title+' '+page.keywords).toLowerCase().includes(word))).sort((a,b)=>(b.title.toLowerCase().startsWith(query.toLowerCase()) ? 1:0)-(a.title.toLowerCase().startsWith(query.toLowerCase()) ? 1:0))}
}
