"""Adaptive bar ink for achromatic tray symbols, without tinting app artwork."""
from pathlib import Path
import sys
root=Path(sys.argv[1]);here=Path(__file__).parent
p=root/'components/TrayIcon.qml';p.write_text((here/'TrayIcon.qml').read_text())
p=root/'components/qmldir';p.chmod(p.stat().st_mode|0o200);p.write_text(p.read_text()+'\nTrayIcon TrayIcon.qml\n')
p=root/'ui/topbar/statusarea/systemtray/SysTrayItem.qml';s=p.read_text().replace('import qs.services','import qs.services\nimport qs.components')
a='    property var hostWindow: null';assert s.count(a)==1;s=s.replace(a,a+'\n    readonly property color foreground:TopBarStyle.colorFor(root.hostWindow?.screen || QsWindow.window?.screen,"right")')
a='            IconImage {\n                id: trayIcon';assert s.count(a)==1;s=s.replace(a,'            TrayIcon {\n                id: trayIcon\n                foreground:root.foreground')
s=s.replace('color: "#FFFFFF"','color: root.foreground');p.chmod(p.stat().st_mode|0o200);p.write_text(s)
p=root/'ui/topbar/statusarea/systemtray/SystemTray.qml';s=p.read_text().replace('import qs.components','import qs.components\nimport qs.services');a='            icon: "chevron-left.svg"';assert s.count(a)==1;s=s.replace(a,a+'\n            color:TopBarStyle.colorFor(root.hostWindow?.screen || QsWindow.window?.screen,"right")');p.chmod(p.stat().st_mode|0o200);p.write_text(s)
