"""Keep clipped vector controls crisp on fractional-DPI outputs and zoom."""
from pathlib import Path
import sys

root=Path(sys.argv[1])
p=root/'components/CFClippingRect.qml'
s=p.read_text().replace('    property alias antialiasing:', '''    readonly property real rasterDpr: Math.max(1, QsWindow.window?.screen?.devicePixelRatio || 1)
    property alias antialiasing:''',1)
# Nearest-neighbour sampling undoes the antialiasing of every vector icon
# inside the offscreen clip, especially while its control animates to 1.25x.
s=s.replace('        layer.enabled: true', '        layer.enabled: true\n        layer.smooth: true\n        antialiasing: true\n        layer.textureSize: Qt.size(Math.max(1,Math.ceil(width*root.rasterDpr)),Math.max(1,Math.ceil(height*root.rasterDpr)))',1)
s=s.replace('            smooth: false', '            smooth: true')
s=s.replace('            sourceItem: contentItemContainer', '''            sourceItem: contentItemContainer
            textureSize: Qt.size(Math.max(1,Math.ceil(contentItemContainer.width*root.rasterDpr)),
                                 Math.max(1,Math.ceil(contentItemContainer.height*root.rasterDpr)))''',1)
p.write_text(s)
p=root/'components/CFVI.qml'
s=p.read_text().replace('Math.ceil(vi.width * 3)', 'Math.ceil(vi.width * Math.max(3, vi.Screen.devicePixelRatio))').replace('Math.ceil(vi.height * 3)', 'Math.ceil(vi.height * Math.max(3, vi.Screen.devicePixelRatio))')
p.write_text(s)
# Canvas glyphs retain their original logical coordinates and size. The clip
# above supplies DPI-aware compositing without scaling the artwork twice.
p=root/'components/PlayerGlyph.qml'
s=p.read_text().replace('    id: g','    id: g\n    smooth: true\n    antialiasing: true',1)
p.write_text(s)
