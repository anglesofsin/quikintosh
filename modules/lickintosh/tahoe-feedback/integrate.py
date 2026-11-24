from pathlib import Path
import sys
r=Path(sys.argv[1]);h=Path(__file__).parent
def edit(name,old,new):
 p=r/name;s=p.read_text()
 if old not in s:raise ValueError('Feedback anchor '+name+' '+old[:60])
 p.chmod(p.stat().st_mode|0o200);p.write_text(s.replace(old,new))
(r/'components/FullscreenPrivacy.qml').write_text((h/'FullscreenPrivacy.qml').read_text())
p=r/'components/qmldir';p.write_text(p.read_text()+'\nFullscreenPrivacy FullscreenPrivacy.qml\n')
edit('shell.qml','    id: appRoot','    id: appRoot\n    FullscreenPrivacy{}')
edit('ui/topbar/statusarea/controlcenter/ControlCenter.qml','anchors.topMargin: MediaCaptureState.controlCenterActive ? 88:30','anchors.topMargin: MediaCaptureState.controlCenterActive ? 58:30')
edit('ui/topbar/statusarea/controlcenter/ControlCenter.qml','x:0;y:-52;width:parent.width;height:44','anchors.horizontalCenter:parent.horizontalCenter;y:-29;width:Math.min(parent.width,170);height:22')
edit('ui/topbar/statusarea/controlcenter/ControlCenter.qml','MediaCaptureState.summary',"MediaCaptureState.entries.length ? MediaCaptureState.entries[0].label : ''")
edit('ui/topbar/statusarea/controlcenter/ControlCenter.qml','Layout.preferredWidth:7;Layout.preferredHeight:7;radius:4','Layout.preferredWidth:5;Layout.preferredHeight:5;radius:2.5')
# Keep the same glass backdrop and native audio wiring, with Tahoe proportions.
edit('ui/osd/OSD.qml','implicitWidth:  320','implicitWidth:  372')
edit('ui/osd/OSD.qml','implicitHeight: 106','implicitHeight: 112')
edit('ui/osd/OSD.qml','width:  300','width:  352')
edit('ui/osd/OSD.qml','height: 66','height: 72')
edit('ui/osd/OSD.qml','radius:       16','radius:       24')
edit('ui/osd/OSD.qml','_currentFill  = "#F5A623"','_currentFill  = "#ffffff"')
edit('ui/osd/OSD.qml','text:           root.livePercent + " %"','visible:root._currentType!=="volume"\n                            text:           root.livePercent + " %"')
edit('ui/osd/OSD.qml','font.pixelSize: 12','font.pixelSize: 13')
edit('ui/topbar/statusarea/volume/VolumePanel.qml','text: I18n.tr("Sound")','text: root.sink ? root.outputLabel(root.sink) : I18n.tr("Sound")\n            Layout.fillWidth:true;elide:Text.ElideRight')

p=r/'rosa/overlays/IslandWindow.qml';s=p.read_text();a=s.index('            id: privacy');b=s.index('            readonly property color hue:',a);head=s[a:b].replace('width: 7','width: 5').replace('height: 7','height: 5');s=s[:a]+head+s[b:];s=s.replace('                blur: 8\n                color: Colors.alpha(privacy.hue, 0.8)','                visible:false\n                blur: 0\n                color: Colors.alpha(privacy.hue, 0.8)');p.write_text(s)
