"""Replace the legacy fixed navigation with the configurable three-page strip."""
from pathlib import Path

def integrate(root):
 p=Path(root)/'rosa/overlays/IslandDashboard.qml';s=p.read_text();a=s.index('    Rectangle {\n        id:navigation');b=s.index('    Component {id:overview;',a)
 s=s[:a]+'''    Item {
        id:navigation
        anchors.horizontalCenter:parent.horizontalCenter
        y:body.height+18
        implicitWidth:ShelfNavigation.shown ? navigationGroups.implicitWidth:0;implicitHeight:ShelfNavigation.shown ? 36:0
        opacity:ShelfNavigation.shown && panel.expandedBody && body.height>panel.bodyHeight-4 ? 1:0
        visible:opacity>0.001;enabled:panel.expandedBody && ShelfNavigation.shown
        Behavior on opacity{NumberAnimation{duration:SettingsPreferences.accessibility.reduceMotion ? 0:120}}
        HoverHandler{onHoveredChanged:panel.pointerChanged(hovered)}
        RowLayout{id:navigationGroups;anchors.centerIn:parent;spacing:8
            Rectangle{implicitWidth:navigationRow.implicitWidth+12;implicitHeight:36;radius:18;color:'#b51b1b20';border.width:1;border.color:'#20ffffff'
                RowLayout{id:navigationRow;anchors.centerIn:parent;spacing:6
                    ShelfButton{objectName:'navigation-home';implicitWidth:34;implicitHeight:28;flat:true;iconSize:15;icon:'notch/home.svg';accessibleLabel:qsTr('Home');selected:![6,8].includes(panel.page);onClicked:panel.selectPage(0)}
                    ShelfButton{objectName:'navigation-tray';visible:!ShelfNavigation.trayOnlyWithFiles || ShelfState.items.length>0;implicitWidth:badge>0 ? Math.max(34,15+String(badge).length*6+10):34;implicitHeight:28;flat:true;iconSize:15;icon:'notch/inbox.svg';accessibleLabel:qsTr('File tray');badge:ShelfState.items.length;selected:panel.page===6;onClicked:panel.selectPage(6)}
                    ShelfButton{objectName:'navigation-widgets';visible:ShelfNavigation.widgetsShown;implicitWidth:34;implicitHeight:28;flat:true;iconSize:15;icon:'notch/grid.svg';accessibleLabel:qsTr('Widgets');selected:panel.page===8;onClicked:panel.selectPage(8)}
                }
            }
            Rectangle{visible:ShelfNavigation.favorites.length>0;implicitWidth:favoriteRow.implicitWidth+12;implicitHeight:36;radius:18;color:'#b51b1b20';border.width:1;border.color:'#20ffffff'
                RowLayout{id:favoriteRow;anchors.centerIn:parent;spacing:6
                    Repeater{model:ShelfNavigation.favorites
                        ShelfButton{required property string modelData;objectName:'navigation-favorite-'+modelData;implicitWidth:34;implicitHeight:28;flat:true;iconSize:16;icon:modelData.startsWith('app:') ? '':'notch/'+(ShelfNavigation.find(modelData)?.icon || 'grid')+'.svg';accessibleLabel:ShelfNavigation.find(modelData)?.title || '';onClicked:ShelfNavigation.activate(modelData)
                            Image{visible:modelData.startsWith('app:');anchors.centerIn:parent;width:18;height:18;source:visible ? IconResolver.forAppId(modelData.substring(4)):'';fillMode:Image.PreserveAspectFit;sourceSize:Qt.size(36,36)}
                        }
                    }
                }
            }
        }
    }
    Connections{target:ShelfNavigation;function onWidgetsShownChanged(){if(!ShelfNavigation.widgetsShown && panel.page===8)panel.selectPage(0)}}
    Connections{target:ShelfState;function onItemsChanged(){if(ShelfNavigation.trayOnlyWithFiles && !ShelfState.items.length && panel.page===6)panel.selectPage(0)}}
    property double navigationSwipeAt:0
    function navigationSwipe(delta){
        if(!ShelfNavigation.gestures || Math.abs(delta)<12 || Date.now()-navigationSwipeAt<400)return
        navigationSwipeAt=Date.now()
        const pages=[0];if(!ShelfNavigation.trayOnlyWithFiles || ShelfState.items.length)pages.push(6);if(ShelfNavigation.widgetsShown)pages.push(8)
        const current=Math.max(0,pages.indexOf(panel.page));panel.selectPage(pages[(current+(delta<0 ? 1:pages.length-1))%pages.length])
    }
    WheelHandler{parent:body;acceptedDevices:PointerDevice.TouchPad;onWheel:event=>{if(Math.abs(event.angleDelta.x)>Math.abs(event.angleDelta.y)){panel.navigationSwipe(event.angleDelta.x);event.accepted=true}else event.accepted=false}}
'''+s[b:];p.write_text(s)
