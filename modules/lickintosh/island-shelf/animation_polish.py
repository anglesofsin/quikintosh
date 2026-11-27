"""Staged presentation timing, delayed media and explicit screenshot-only card."""
from pathlib import Path
import runpy
edit=runpy.run_path(str(Path(__file__).with_name("media_polish.py")))["edit"]

def integrate(root):
 root=Path(root)
 def hub(s):
  s=s.replace('    property bool mediaBig: false', '''    property bool mediaReady:false
    Timer{id:mediaArrival;interval:2000;onTriggered:root.mediaReady=Media.has && Media.playing}
    Connections{target:Media;function onPlayingChanged(){if(Media.has && Media.playing)mediaArrival.restart();else{mediaArrival.stop();root.mediaReady=false}}function onHasChanged(){if(!Media.has){mediaArrival.stop();root.mediaReady=false}else if(Media.playing)mediaArrival.restart()}}
    Timer{interval:0;running:true;onTriggered:if(Media.has && Media.playing)mediaArrival.restart()}
    property bool mediaBig: false''',1)
  s=s.replace('Media.has && Media.playing','Media.has && Media.playing && root.mediaReady')
  s=s.replace('root.mediaReady=Media.has && Media.playing && root.mediaReady','root.mediaReady=Media.has && Media.playing')
  s=s.replace('if(Media.has && Media.playing && root.mediaReady)mediaArrival.restart()', 'if(Media.has && Media.playing)mediaArrival.restart()')
  s=s.replace('else if(Media.playing)mediaArrival.restart()', 'else if(Media.playing)mediaArrival.restart()')
  return s
 edit(root,'rosa/overlays/Island.qml',hub)
 def window(s):
  # A single timeline allows reversal from the current state; children derive
  # staggered phases, never restart independent one-shot visibility timers.
  s=s.replace(' ? 0:160;easing.type:Easing.OutCubic',' ? 0:560;easing.type:Easing.InOutCubic',1)
  s=s.replace('    readonly property bool idleEligible:', '''    function phase(start,end){const p=Math.min(idleVisibility.progress,presentationProgress);const k=Math.max(0,Math.min(1,(p-start)/(end-start)));return k*k*(3-2*k)}
    readonly property bool entering:presentationWanted && !idleVisibility.hideRequested
    readonly property real corePhase:entering ? phase(0,.56):phase(0,.6)
    readonly property real leftPhase:entering ? phase(.48,.76):phase(.78,1)
    readonly property real rightPhase:entering ? phase(.64,.9):phase(.88,1)
    readonly property real privacyPhase:entering ? phase(.82,1):phase(.60,.82)
    readonly property bool idleEligible:''',1)
  s=s.replace('xScale:idleVisibility.progress*win.presentationProgress','xScale:win.corePhase').replace('yScale:0.85+0.15*idleVisibility.progress*win.presentationProgress','yScale:.25+.75*win.corePhase')
  s=s.replace('stage.detach:','stage.detach:')
  s=s.replace('dotLife.value * (1 - stage.swallowed)','dotLife.value * (1 - stage.swallowed)*win.rightPhase')
  s=s.replace('slotLife.value * (1 - stage.swallowed)','slotLife.value * (1 - stage.swallowed)*win.leftPhase')
  s=s.replace('visible: win.sideActivitiesVisible && stage.dotShow','visible: stage.dotShow').replace('visible: win.sideActivitiesVisible && stage.headDetach','visible: stage.headDetach')
  s=s.replace('id: dotLife\n','id: dotLife\n        response:.38;damping:0.9\n').replace('id: slotLife\n','id: slotLife\n        response:.38;damping:0.9\n')
  s=s.replace('const progress=idleVisibility.progress*win.presentationProgress','const progress=win.corePhase')
  s=s.replace('privacy.visualRight.x+8','privacy.visualRight.x+8+(1-win.privacyPhase)*14').replace('scale: privacy.on ? 1 : 0','opacity:win.privacyPhase\n            scale: privacy.on ? 1 : 0')
  s=s.replace('visible: !win.privacyHandoff && scale > 0.01 && (NativeSettings.PrivacyPreferences.showExpanded || (!win.wide && !win.seeking && Math.abs(morph.value) < 0.02 && Math.abs(seek.value) < 0.02))', 'property real activityOpacity:privacy.on && !win.privacyHandoff && (NativeSettings.PrivacyPreferences.showExpanded || (!win.wide && !win.seeking && Math.abs(morph.value) < 0.02 && Math.abs(seek.value) < 0.02)) ? 1:0\n            Behavior on activityOpacity{NumberAnimation{duration:260;easing.type:Easing.OutCubic}}\n            visible:opacity>0.005 && scale>0.01')
  s=s.replace('opacity:win.privacyPhase','opacity:win.privacyPhase*activityOpacity')
  # Decorative sheen/rim must not flash a contour around a media morph.
  s=s.replace('visible: !pill.newEvent && IslandConfig.s("sheen")','visible: win.wideKind!=="media" && !pill.newEvent && IslandConfig.s("sheen")')
  s=s.replace('IslandRim {\n                visible:!pill.newEvent','IslandRim {\n                visible:win.wideKind!=="media" && !pill.newEvent')
  # The filename is never part of compact screenshot presentation, even for
  # legacy event sources or when an expansion is interrupted.
  s=s.replace(': win.hub.flashText',': win.hub.flashKind==="shot" ? "":win.hub.flashText')
  s=s.replace('visible: opacity > 0.01 && !win.suppressIdleClock','visible: win.hub.kind!=="shot" && opacity > 0.01 && !win.suppressIdleClock',1)
  return s
 edit(root,'rosa/overlays/IslandWindow.qml',window)
 edit(root,'rosa/overlays/IdleVisibility.qml',lambda s:s.replace('root.animate ? 240:0','root.animate ? 560:0'))
 capture=root/'capture'
 if capture.is_symlink():
  original=capture.resolve();capture.unlink();capture.mkdir()
  for entry in original.iterdir():(capture/entry.name).symlink_to(entry,target_is_directory=entry.is_dir())
 edit(root,'capture/CaptureIntegration.qml',lambda s:s.replace("else Quickshell.execDetached(['notify-send','-a','Quickintosh Capture','Screenshot saved',path])", "else if(!Rosa.IslandConfig.s('enabled'))Quickshell.execDetached(['notify-send','-a','Quickintosh Capture','Screenshot saved',path])"))

