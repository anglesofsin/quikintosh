"""Switch tabs immediately and retain visited pages without keeping sensors active."""
from pathlib import Path


def integrate(root):
    p=Path(root)/'rosa/overlays/IslandDashboard.qml';s=p.read_text()
    a=s.index('    function selectPage(index)');b=s.index('    property var selectedHour:',a)
    s=s[:a]+'''    property var visitedPages:({0:true})
    function selectPage(index) {
        if(index<0 || index>13)return;
        if(!visitedPages[index]){const next=Object.assign({},visitedPages);next[index]=true;visitedPages=next}
        pendingPage=index;page=index;
    }
'''+s[b:]
    s=s.replace('pageOut.stop();pageIn.stop();pageContent.opacity=1;','')
    s=s.replace('opacity: panel.expandedBody && panel.geometryReady ? 1 : 0','opacity: panel.expandedBody ? 1 : 0')
    s=s.replace('enabled:panel.expandedBody && panel.geometryReady','enabled:panel.expandedBody')
    old='''                Loader {
                    id: pageContent
                    width: pageFrame.width
                    scale: 1
                    height: pageFrame.height / scale
                    transformOrigin: Item.TopLeft
                    sourceComponent: [overview, forecast, performance, media, notifications, cameraFull, tray, clipboard, library, lyrics, audioApps, activities, awake, widgetDetail][panel.page]
                }'''
    new='''                Item {
                    id:pageContent
                    anchors.fill:parent
                    Repeater {
                        model:14
                        delegate:Loader {
                            required property int index
                            anchors.fill:parent
                            active:!!panel.visitedPages[index]
                            visible:panel.page===index
                            enabled:visible && panel.expandedBody
                            sourceComponent:[overview,forecast,performance,media,notifications,cameraFull,tray,clipboard,library,lyrics,audioApps,activities,awake,widgetDetail][index]
                        }
                    }
                }'''
    assert old in s,'Tab loader changed';s=s.replace(old,new,1);p.write_text(s)


if __name__=='__main__':
    import sys
    integrate(sys.argv[1])
