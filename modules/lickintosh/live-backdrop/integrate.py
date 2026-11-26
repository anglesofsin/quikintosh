from pathlib import Path
import sys
root=Path(sys.argv[1]);here=Path(__file__).parent
p=root/'components/glass/AnimatedBackdrop.qml';p.write_text((here/'AnimatedBackdrop.qml').read_text())
p=root/'components/glass/qmldir';p.write_text(p.read_text()+'\nAnimatedBackdrop AnimatedBackdrop.qml\n')
p=root/'components/glass/GlassWallpaper.qml';s=p.read_text().replace('    property string preview:', '    property double videoPosition:0\n    property bool videoPlaying:false\n    property string preview:',1);p.write_text(s)
p=root/'components/VideoWallpaper.qml';s=p.read_text().replace('        id: player','        id: player\n        onPositionChanged:if(root.source===ShellConfig.options.wallpaper.videoPath)GlassWallpaper.videoPosition=position\n        onPlaybackStateChanged:if(root.source===ShellConfig.options.wallpaper.videoPath)GlassWallpaper.videoPlaying=playbackState===MediaPlayer.PlayingState',1).replace('import qs.components.glass','import qs.components.glass\nimport qs.services',1);p.write_text(s)
p=root/'components/glass/LiquidGlassBackdrop.qml';s=p.read_text().replace('        WallpaperCrossfade {','''        readonly property string animatedPath:WallpaperSettings.videoFor(root.monitorName) || (GlassWallpaper.videoActive ? ShellConfig.options.wallpaper.videoPath:'')
        Loader {
            id:animatedBackground
            anchors.fill:parent
            active:root.ready && scene.animatedPath!=='' && !root.frozenSource
            sourceComponent:AnimatedBackdrop{path:scene.animatedPath;playing:GlassWallpaper.videoPlaying && ShellConfig.options.wallpaper.videoEnabled}
        }
        WallpaperCrossfade {
            visible:!animatedBackground.item?.hasFrame''',1);p.write_text(s)
# A generated icon reply used to republish the entire map for each file.
# Merge replies once per event-loop turn, keeping the renderer and pixels intact.
p=root/'services/LayeredIcons.qml';s=p.read_text().replace(' property var origins:({})',''' property var origins:({})
 property var completed:[]
 function flushCompleted(){
  if(!completed.length)return
  const batch=completed;completed=[]
  const next=Object.assign({},files),reverse=Object.assign({},origins)
  for(const data of batch){reverse['file://'+data.path]=data.key.split('|')[0];next[data.key]=data.path}
  origins=reverse;files=next;pending=Math.max(0,pending-batch.length);lastRenderMs=batch[batch.length-1].ms
 }
''',1)
old="else if(data.type==='rendered'){const reverse=Object.assign({},root.origins);reverse['file://'+data.path]=data.key.split('|')[0];root.origins=reverse;const next=Object.assign({},root.files);next[data.key]=data.path;root.files=next;root.pending=Math.max(0,root.pending-1);root.lastRenderMs=data.ms}"
assert old in s;s=s.replace(old,"else if(data.type==='rendered'){root.completed.push(data);Qt.callLater(root.flushCompleted)}");p.write_text(s)
