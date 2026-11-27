"""Switch tabs immediately and retain visited pages without keeping sensors active."""
from pathlib import Path


def integrate(root):
    p=Path(root)/'rosa/overlays/IslandDashboard.qml';s=p.read_text()
    a=s.index('    function selectPage(index)');b=s.index('    property var selectedHour:',a)
    s=s[:a]+'''    function pageBodyWidth(index){return Math.min(width,index===0 && IslandConfig.s("shelfAdaptiveWidth") ? Math.min(IslandConfig.s("shelfWidth"),Math.max(380,[1,2,3,4].filter(i=>IslandConfig.s("shelfSlot"+i)!=="none").length*380)):({1:560,2:540,3:460,4:480,5:480,6:820,7:1000,8:1000,9:620,10:440,11:580,12:500,13:(detailWidget==="calendar" ? 620:380)})[index] || IslandConfig.s("shelfWidth"))}
    function pageBodyHeight(index){return index===8 ? Math.min(output.height-80,ShelfState.editing ? 440:310):({1:336,4:300,5:300,6:280,7:300,9:330,10:300,11:300,12:216})[index] || IslandConfig.s("shelfHeight")}
    property var visitedPages:({0:true})
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
                            // Layout at the destination size, never the intermediate morph size.
                            width:Math.max(1,panel.pageBodyWidth(index)-44)
                            height:Math.max(1,panel.pageBodyHeight(index)-44-(IslandConfig.s("shelfExpandedTabs") ? tabs.implicitHeight+12:0))
                            x:(parent.width-width)/2
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
