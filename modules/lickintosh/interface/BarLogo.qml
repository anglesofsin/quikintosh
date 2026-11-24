import QtQuick
import Quickshell
import qs.services
Item {
    id:root
    readonly property var options:ShellConfig.options.topbar
    readonly property color foreground:TopBarStyle.logoColor(QsWindow.window ? QsWindow.window.screen : null)
    readonly property bool customText:options.logoType==='text'
    readonly property bool tintImage:options.logoColorMode!=='original'
    implicitWidth:Math.max(12,Math.min(28,options.logoSize));implicitHeight:implicitWidth
    function imageUrl(path) {if(path.startsWith('~/'))return 'file://'+Quickshell.env('HOME')+path.slice(1);if(path.startsWith('/'))return 'file://'+path;return path}
    Image {
        id:picture;anchors.fill:parent;visible:!root.customText
        source:root.options.logoType==='image' && root.options.logoSource ? root.imageUrl(root.options.logoSource) : Quickshell.shellDir+'/assets/pngs/linux-logo.png'
        fillMode:Image.PreserveAspectFit;sourceSize:Qt.size(80,80);asynchronous:true;cache:true;smooth:true;mipmap:true
        layer.enabled:root.tintImage
        layer.effect:ShaderEffect {property var source;property color tint:root.foreground;fragmentShader:Quickshell.shellDir+'/components/bar-tint.frag.qsb'}
    }
    Text {anchors.centerIn:parent;visible:root.customText;text:root.options.logoText;textFormat:Text.PlainText;color:root.foreground;font.family:'Symbols Nerd Font Mono';font.pixelSize:root.implicitHeight}
}
