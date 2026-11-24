import QtQuick
QtObject{
 id:root
 property bool enabled:false
 property bool inside:false
 property bool fired:false
 property int modifiers:0
 property int requiredModifiers:0
 property int delay:200
 property string action:'none'
 readonly property bool matches:(modifiers & requiredModifiers)===requiredModifiers
 signal triggered(string action)
 property Timer dwell:Timer{interval:Math.max(1,root.delay);onTriggered:root.fire()}
 function update(){dwell.stop();if(enabled && inside && !fired && matches && action!=='none')dwell.restart()}
 function fire(){if(enabled && inside && !fired && matches && action!=='none'){fired=true;triggered(action)}}
 function leave(){inside=false;fired=false;dwell.stop()}
 onEnabledChanged:{if(!enabled)leave();else update()}
 onInsideChanged:update()
 onModifiersChanged:update()
 onMatchesChanged:update()
 onRequiredModifiersChanged:update()
 onActionChanged:update()
 onDelayChanged:update()
}
