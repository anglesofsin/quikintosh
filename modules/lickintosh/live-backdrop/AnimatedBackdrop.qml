import QtQuick
import QtMultimedia
import Quickintosh.Render
import qs.services
import qs.components.glass
Item {
 id:root
 property string path:''
 property bool playing:false
 readonly property var sharedSink:GlassWallpaper.videoSinks[path] || null
 readonly property bool hasFrame:relay.hasFrame
 VideoOutput { id:video;anchors.fill:parent;fillMode:VideoOutput.PreserveAspectCrop }
 VideoFrameRelay { id:relay;source:root.sharedSink;destination:video.videoSink }
}
