pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.rosa.services
Singleton {
    id: root
    IpcHandler{
        target:"voice"
        function status():string{return JSON.stringify({enabled:root.enabled,active:root.active,client:root.active ? root.call.client:"",external:root.active && root.call.external===true,metadataClients:Object.keys(root.clients).filter(k=>root.clients[k].active && !root.clients[k].external),controls:root.controlsAvailable,error:root.error})}
    }
    property bool enabled: false
    property bool restartReady: true
    property var clients: ({})
    property var generic: null
    property string error: ""
    readonly property var call: {
        const order = ["canary","ptb","stable","equibop"]
        const preferred = IslandConfig.s("voiceClient")
        if (preferred !== "auto") { order.splice(order.indexOf(preferred),1); order.unshift(preferred) }
        for (const name of order) {
            const c = clients[name]
            if (IslandConfig.s("voice" + name.charAt(0).toUpperCase() + name.slice(1)) && c && c.active
                && (!IslandConfig.s("voicePrivacy") || !c.streamer)) return c
        }
        return IslandConfig.s("voiceGeneric") ? generic : null
    }
    readonly property bool active: enabled && call !== null
    readonly property var participants: {
        if (!active) return []
        return call.participants.filter(p => (p.self ? IslandConfig.s("voiceSelf") : IslandConfig.s("voiceOthers")))
    }
    readonly property string title: !active ? "" : IslandConfig.s("voiceNames") ? call.channel : "Voice call"
    readonly property int speakingCount: participants.filter(p => p.speaking && !p.muted).length
    readonly property var speaker: {
        const speaking=participants.filter(p=>p.speaking && !p.muted)
        return speaking.length ? speaking[0] : null
    }
    readonly property string image: active && call.image ? call.image : speaker ? speaker.avatar : ""
    readonly property bool controlsAvailable: active && call.controls === true && !!call.session
    readonly property bool selfMuted: active && call.participants.some(p=>p.self && p.muted)
    readonly property bool selfDeaf: active && call.participants.some(p=>p.self && p.deaf)
    property string callKey: active ? call.client+":"+(call.channelId || call.channel) : ""
    property double observedAt: Date.now()
    onCallKeyChanged: observedAt=Date.now()
    readonly property string duration: {
        const seconds=Math.max(0,Math.floor((durationClock.date.getTime()-(active && call.joinedAt ? call.joinedAt : observedAt))/1000))
        return (seconds>=3600 ? Math.floor(seconds/3600)+":" : "")+String(Math.floor(seconds/60)%60).padStart(2,"0")+":"+String(seconds%60).padStart(2,"0")
    }
    SystemClock { id:durationClock; precision:SystemClock.Seconds; enabled:root.active && IslandConfig.s("voiceDuration") }
    function control(action) {
        if(!controlsAvailable || ["mute","deaf","disconnect"].indexOf(action)<0) return
        Quickshell.execDetached(["@VOICE_PYTHON@",Quickshell.shellDir+"/rosa/voice-bridge.py","control",call.session,call.channelId,action])
    }
    Process {
        id: process
        running: root.enabled && root.restartReady
        command: ["@VOICE_PYTHON@", Quickshell.shellDir + "/rosa/voice-bridge.py"]
        stdout: SplitParser { onRead: line => {
            try { const data=JSON.parse(line); root.clients=data.clients || {}; root.generic=data.generic || null; root.error=data.error || "" }
            catch (_) { root.error="Invalid voice bridge event" }
        } }
        onExited: { root.clients=({}); root.generic=null; if(root.enabled) { root.restartReady=false; retry.restart() } }
    }
    Timer { id: retry; interval:5000; onTriggered: root.restartReady=true }
    onEnabledChanged: if(!enabled) { retry.stop(); restartReady=true; clients=({}); generic=null; error="" }
}
