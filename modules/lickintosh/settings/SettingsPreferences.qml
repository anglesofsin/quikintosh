pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
Singleton{
 id:root
 property bool ready:false
 property bool locked:false
 property alias accessibility:adapter.accessibility
 property alias notifications:adapter.notifications
 property alias focus:adapter.focus
 property alias activity:adapter.activity
 property alias session:adapter.session
 property alias profile:adapter.profile
 property alias inputOverrides:adapter.inputOverrides
 property alias defaultApps:adapter.defaultApps
 property alias servers:adapter.servers
 property alias lastPage:adapter.lastPage
 function input(key,value){const next=Object.assign({},root.inputOverrides);if(value===null)delete next[key];else next[key]=value;root.inputOverrides=next}
 function appRule(name){return root.notifications.rules.find(rule=>rule.app===name) || {app:name,allowed:true,banners:true}}
 function rule(name,key,value){const list=root.notifications.rules.slice(),index=list.findIndex(rule=>rule.app===name);const entry=Object.assign({},root.appRule(name));entry[key]=value;if(index<0)list.push(entry);else list[index]=entry;root.notifications.rules=list}
 Timer{id:save;interval:150;onTriggered:file.writeAdapter()}
 Timer{id:reload;interval:100;onTriggered:file.reload()}
 FileView{
  id:file;path:Quickshell.env('HOME')+'/.config/lickintosh/core/settings-preferences.json';watchChanges:true
  onFileChanged:reload.restart()
  onLoaded:root.ready=true
  onLoadFailed:error=>{if(error===FileViewError.FileNotFound){root.ready=true;file.writeAdapter()}}
  onAdapterUpdated:if(root.ready)save.restart()
  JsonAdapter{
   id:adapter
   property string lastPage:'general'
   property var inputOverrides:({})
   property var defaultApps:({})
   property list<var> servers:[]
   property JsonObject profile:JsonObject{property string displayName:'';property string avatar:'';property bool autoAppearance:false}
   property JsonObject accessibility:JsonObject{
    property bool reduceMotion:false
    property bool reduceTransparency:false
    property bool increaseContrast:false
    property real textScale:1
   }
   property JsonObject notifications:JsonObject{
    property bool banners:true
    property string previews:'always'
    property int duration:5000
    property list<var> rules:[]
    property list<var> appNames:[]
   }
   property JsonObject focus:JsonObject{
    property int profileVersion:0
    property bool autoDndSharing:false
    property string activeId:'dnd'
    property list<var> profiles:[
     {id:'dnd',name:'Do Not Disturb',appMode:'allow',apps:'',peopleMode:'allow',people:'',allowCritical:true,timeSensitive:false,schedule:false,start:'22:00',end:'07:00',days:[0,1,2,3,4,5,6],triggerApps:''},
     {id:'work',name:'Work',appMode:'allow',apps:'',peopleMode:'allow',people:'',allowCritical:true,timeSensitive:false,schedule:false,start:'09:00',end:'17:00',days:[1,2,3,4,5],triggerApps:''},
     {id:'personal',name:'Personal',appMode:'silence',apps:'',peopleMode:'allow',people:'',allowCritical:true,timeSensitive:false,schedule:false,start:'18:00',end:'22:00',days:[0,1,2,3,4,5,6],triggerApps:''},
     {id:'sleep',name:'Sleep',appMode:'allow',apps:'',peopleMode:'allow',people:'',allowCritical:true,timeSensitive:false,schedule:false,start:'22:00',end:'07:00',days:[0,1,2,3,4,5,6],triggerApps:''}
    ]
    property double endAt:0
    property bool schedule:false
    property string start:'22:00'
    property string end:'07:00'
    property list<var> days:[0,1,2,3,4,5,6]
    property bool allowCritical:true
   }
   property JsonObject activity:JsonObject{
    property bool enabled:false
   }
   property JsonObject session:JsonObject{
    property bool autoLock:false
    property int lockAfter:600
    property string savedAppearance:''
   }
  }
 }
}
