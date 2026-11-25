pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.components.glass
import Quickintosh.Render as Native
Singleton {
 id:root
 readonly property var options:ShellConfig.options.performance
 readonly property bool glassEnabled:options.glassEnabled && !SettingsPreferences.accessibility.reduceTransparency
 readonly property bool blurEnabled:options.blurEnabled
 readonly property bool shadows:options.shadows
 readonly property bool ambientAnimations:options.ambientAnimations && !SettingsPreferences.accessibility.reduceMotion && !GameMode.enabled
 readonly property bool prewarm:options.prewarm
 readonly property int maximumFps:Math.max(0,Math.min(1000,options.maximumFps))
 readonly property int glassFps:Math.max(0,Math.min(1000,options.glassFps))
 readonly property int geometryFps:Math.max(0,Math.min(1000,options.geometryFps))
 readonly property real textureScale:Math.max(.25,Math.min(1,options.textureScale))
 readonly property real blurScale:Math.max(.25,Math.min(1,options.blurScale))
 readonly property real motionScale:Math.max(.1,Math.min(3,options.motionScale))
 Binding{target:Native.FramePacer;property:'maximumFps';value:root.maximumFps}
 Binding{target:Native.FramePacer;property:'measuring';value:root.options.measureFrames}
 onPrewarmChanged:Native.FramePacer.prepareWindows(prewarm)
 Component.onCompleted:{Native.FramePacer.prepareWindows(prewarm);Native.FramePacer.requestGeometry()}
 readonly property var geometry:Native.FramePacer.geometry
 readonly property bool geometryAvailable:Native.FramePacer.geometryAvailable
 function updateGeometry(){if(!GlassTracker.fast)Native.FramePacer.requestGeometry()}
 function synchronizeMotion(){if(GlassTracker.captureUsers>0)Native.FramePacer.requestGeometry();Native.FramePacer.setGeometryMotion((GlassTracker.fast || GlassTracker.precisionUsers>0) && GlassTracker.captureUsers>0,root.geometryFps)}
 onGeometryFpsChanged:synchronizeMotion()
 Connections{target:GlassTracker;function onFastChanged(){root.synchronizeMotion()}function onCaptureUsersChanged(){root.synchronizeMotion()}function onPrecisionUsersChanged(){root.synchronizeMotion()}function onTransitionEpochChanged(){if(GlassTracker.captureUsers>0)Native.FramePacer.requestGeometry()}}
 function register(window,role){if(window)Native.FramePacer.label(window,role || 'interface')}
 function statistics(){return Native.FramePacer.statistics()}
 function set(name,value){options[name]=value}
 readonly property var presets:({
  native:{maximumFps:0,glassFps:0,geometryFps:0,textureScale:.5,blurScale:.5,glassEnabled:true,blurEnabled:true,shadows:true,ambientAnimations:true,prewarm:true,motionScale:1,cacheWidgetDrag:false},
  balanced:{maximumFps:60,glassFps:60,geometryFps:60,textureScale:.5,blurScale:.5,glassEnabled:true,blurEnabled:true,shadows:true,ambientAnimations:true,prewarm:true,motionScale:1,cacheWidgetDrag:true},
  saving:{maximumFps:30,glassFps:15,geometryFps:30,textureScale:.25,blurScale:.25,glassEnabled:true,blurEnabled:true,shadows:false,ambientAnimations:false,prewarm:false,motionScale:.6,cacheWidgetDrag:true}
 })
 function applyPreset(name){const preset=presets[name];if(!preset)return;for(const key in preset)options[key]=preset[key];SettingsPreferences.accessibility.reduceMotion=false}
 readonly property string profile:{for(const name in presets)if(!SettingsPreferences.accessibility.reduceMotion && Object.keys(presets[name]).every(key=>options[key]===presets[name][key]))return name;return 'custom'}
 IpcHandler{target:'frames'
  function status():string{return JSON.stringify({limit:root.maximumFps,glassLimit:root.glassFps,geometryLimit:root.geometryFps,measuring:Native.FramePacer.measuring,preciseGeometry:root.geometryAvailable,frameSynchronized:Native.FramePacer.frameSynchronized,windows:root.statistics()})}
  function monitor(enabled:bool):void{root.options.measureFrames=enabled}
 }
}
