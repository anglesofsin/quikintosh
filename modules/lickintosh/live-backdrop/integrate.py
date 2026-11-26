from pathlib import Path
import sys
root=Path(sys.argv[1]);here=Path(__file__).parent
p=root/'components/glass/AnimatedBackdrop.qml';p.write_text((here/'AnimatedBackdrop.qml').read_text())
p=root/'components/glass/qmldir';p.write_text(p.read_text()+'\nAnimatedBackdrop AnimatedBackdrop.qml\n')
p=root/'components/glass/GlassWallpaper.qml';s=p.read_text().replace('    property string preview:', '    property var videoSinks:({})\n    function registerVideo(path,sink){const next=Object.assign({},videoSinks);next[path]=sink;videoSinks=next}\n    function unregisterVideo(path,sink){if(videoSinks[path]!==sink)return;const next=Object.assign({},videoSinks);delete next[path];videoSinks=next}\n    property double videoPosition:0\n    property bool videoPlaying:false\n    property string preview:',1);p.write_text(s)
p=root/'tools/wallpaper-video-render.py';p.write_text((here/'video-render.py').read_text())
p=root/'services/WallpaperVideo.qml';p.write_text((here/'WallpaperVideo.qml').read_text().replace('@PYTHON@',sys.executable))
p=root/'services/qmldir';p.write_text(p.read_text()+'\nsingleton WallpaperVideo WallpaperVideo.qml\n')
p=root/'services/ShellConfig.qml';p.write_text(p.read_text().replace('property bool videoEnabled:true','property int videoHeight:0\n                property int videoFps:0\n                property bool videoEnabled:true',1))
p=root/'components/VideoWallpaper.qml';s=p.read_text().replace('        id: player','        id: player\n        onPositionChanged:if(root.source===ShellConfig.options.wallpaper.videoPath)GlassWallpaper.videoPosition=position\n        onPlaybackStateChanged:if(root.source===ShellConfig.options.wallpaper.videoPath)GlassWallpaper.videoPlaying=playbackState===MediaPlayer.PlayingState',1).replace('import qs.components.glass','import qs.components.glass\nimport qs.services',1)
s=s.replace('    onSourceChanged: {', '    property string registeredPath: \"\"\n    function registerSink(){if(!output)return;if(registeredPath)GlassWallpaper.unregisterVideo(registeredPath,output.videoSink);registeredPath=root.source;if(registeredPath)GlassWallpaper.registerVideo(registeredPath,output.videoSink)}\n    Component.onCompleted:registerSink()\n    onSourceChanged: {\n        registerSink()',1).replace('    Component.onDestruction: GlassWallpaper.videoUrl = \"\"', '    Component.onDestruction:{GlassWallpaper.unregisterVideo(registeredPath,output.videoSink);GlassWallpaper.videoUrl=\"\"}')
s=s.replace('source: root.source !== \"\" ? \"file://\" + root.source : \"\"', 'source:root.source ? \"file://\"+WallpaperVideo.resolve(root.source):\"\"',1)
p.write_text(s)
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

# A monitor query in flight must not swallow the final workspace change.
p=root/'components/glass/GlassTracker.qml'
s=p.read_text().replace('    Process {\n        id: monitorQuery', '    property bool monitorQueryAgain:false\n    Process {\n        id: monitorQuery',1)
s=s.replace('        id: monitorQuery\n', '        id: monitorQuery\n        onExited:if(root.monitorQueryAgain){root.monitorQueryAgain=false;Qt.callLater(function(){monitorQuery.running=true})}\n',1)
s=s.replace('if (!monitorQuery.running) monitorQuery.running = true','if (!monitorQuery.running) monitorQuery.running = true;else root.monitorQueryAgain=true',1)
p.write_text(s)
