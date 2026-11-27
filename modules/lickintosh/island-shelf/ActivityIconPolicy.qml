pragma Singleton
import QtQuick
import qs.services
import "IconRules.js" as Rules
QtObject {
 id:root
 readonly property var spec:@ICON_SPEC@
 readonly property var preferences:ShelfState.utilityPreferences
 function resolve(event,presentation){return Rules.resolve(spec,preferences,event,presentation)}
 function set(key,value){ShelfState.send({action:'utilityPreferences',values:{[key]:value}})}
 function override(kind,icon){const saved=Object.assign({},preferences.iconPolicyOverrides || {});if(icon)saved[kind]=icon;else delete saved[kind];set('iconPolicyOverrides',saved)}
 function stateOverride(state,icon){const saved=Object.assign({},preferences.iconPolicyStatusOverrides || {});if(icon)saved[state]=icon;else delete saved[state];set('iconPolicyStatusOverrides',saved)}
 function reset(){ShelfState.send({action:'utilityPreferences',values:spec.defaults})}
}
