pragma Singleton
import QtQuick
import Quickshell
import qs.services
QtObject{
 id:root
 readonly property bool shown:ShelfState.utilityPreferences.navigationShown!==false
 readonly property bool widgetsShown:ShelfState.utilityPreferences.navigationWidgets!==false
 readonly property bool trayOnlyWithFiles:ShelfState.utilityPreferences.navigationTrayOnlyWithFiles===true
 readonly property bool gestures:ShelfState.utilityPreferences.navigationGestures!==false
 readonly property var favorites:(ShelfState.utilityPreferences.navigationFavorites || []).filter(key=>!!key && !!find(key)).slice(0,4)
 readonly property var choices:[{key:'',title:qsTr('None'),icon:''}].concat(ShelfState.ringCatalogue,[{key:'batteries',title:qsTr('Batteries'),icon:'battery',widget:'batteries'},{key:'translate',title:qsTr('Quick Translate'),icon:'type',widget:'translate'},{key:'applications',title:qsTr('Applications'),icon:'grid',ipc:'launchpad'}],DesktopEntries.applications.values.filter(app=>!app.noDisplay).map(app=>({key:'app:'+app.id,title:app.name,icon:'grid',desktop:app})))
 function find(key){return choices.find(item=>item.key===key)}
 function set(key,value){ShelfState.send({action:'utilityPreferences',values:{[key]:value}})}
 function pin(index,key){const saved=(ShelfState.utilityPreferences.navigationFavorites || []).slice(0,4);while(saved.length<4)saved.push('');const existing=saved.indexOf(key);if(key && existing>=0 && existing!==index)saved[existing]='';saved[index]=key;set('navigationFavorites',saved)}
 function activate(key){const item=find(key);if(!item)return;if(item.desktop){ShelfState.closeRequested();item.desktop.execute()}else if(item.ipc){ShelfState.closeRequested();Quickshell.execDetached(['quickintosh','ipc','call','rice',item.ipc])}else if(item.command){ShelfState.closeRequested();Quickshell.execDetached([item.command])}else if(item.widget)ShelfState.openDetail(item.widget);else ShelfState.reveal(item.page)}
}
