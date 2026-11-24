const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const source=fs.readFileSync(__dirname+'/discord-bridge.js','utf8');
const handlers={},sent=[],localListeners=[]; let channel='123',localMute=false,localDeaf=false;
class WS { static OPEN=1; constructor(url) { assert.equal(url,'ws://127.0.0.1:6891/voice');this.readyState=1;global.socket=this; } send(s){sent.push(JSON.parse(s))} close(){} }
const common={
 MediaEngineStore:{getSelfMute:()=>localMute,getSelfDeaf:()=>localDeaf,addChangeListener:f=>localListeners.push(f),removeChangeListener:()=>{}},
 UserStore:{getCurrentUser:()=>({id:'10'}),getUser:id=>({id,globalName:id==='10'?'Self':'Other',avatar:'a_hash'})},
 VoiceStateStore:{getVoiceStateForUser:()=>({channelId:channel}),getVoiceStatesForChannel:()=>({'10':{userId:'10',selfMute:false},'20':{userId:'20',selfMute:false}})},
 ChannelStore:{getChannel:()=>({name:'Test call',guild_id:'30'})},GuildStore:{getGuild:()=>({name:'Test server'})},GuildMemberStore:{getNick:()=>null},
 StreamerModeStore:{enabled:false},ChannelRTCStore:{getSpeakingParticipants:()=>[]},
 FluxDispatcher:{subscribe:(type,f)=>handlers[type]=f,unsubscribe:()=>{}}
};
const context={WebSocket:WS,Vencord:{Webpack:{Common:common}},location:{hostname:'canary.discord.com'},setTimeout:f=>{f();return 1},clearTimeout:()=>{},addEventListener:()=>{}};
// Use a real event queue so coalescing matches renderer behavior.
context.setTimeout=setTimeout;context.clearTimeout=clearTimeout;
vm.runInNewContext(source,context);socket.onopen();
assert.equal(sent.at(-1).client,'canary');assert.equal(sent.at(-1).participants.length,2);
handlers.SPEAKING({userId:'20',speakingFlags:1});
setTimeout(()=>{
 assert.equal(sent.at(-1).participants[1].speaking,true);
 handlers.SPEAKING({userId:'20',speakingFlags:2});
 setTimeout(()=>{
  assert.equal(sent.at(-1).participants[1].speaking,false);
  channel=null;handlers.VOICE_STATE_UPDATES({});
  setTimeout(()=>{assert.equal(sent.at(-1).active,false);assert.equal(sent.at(-1).participants.length,0);console.log('Renderer: join, participants, speaking flags, leave passed');},50);
 },50);
},50);
// Controls are routed only to the channel currently joined in this renderer.
setTimeout(()=>{
 const dispatched=[];common.FluxDispatcher.dispatch=e=>dispatched.push(e);
 channel='456';
 socket.onmessage({data:JSON.stringify({type:'control',action:'mute',channelId:'old'})});
 assert.equal(dispatched.length,0);
 for(const action of ['mute','deaf','disconnect'])socket.onmessage({data:JSON.stringify({type:'control',action,channelId:'456'})});
 assert.deepEqual(dispatched.map(e=>e.type),['AUDIO_TOGGLE_SELF_MUTE','AUDIO_TOGGLE_SELF_DEAF','VOICE_CHANNEL_SELECT']);
 socket.onmessage({data:JSON.stringify({type:'control',action:'unknown',channelId:'456'})});assert.equal(dispatched.length,3);
 console.log('Renderer controls: mute/deaf/leave accepted, stale channel and unknown action rejected');
},250);

// Gateway voice states remain stale: local controls must still update immediately.
setTimeout(()=>{
 localMute=true;localListeners.forEach(f=>f());
 setTimeout(()=>{
  assert.equal(sent.at(-1).participants.find(p=>p.self).muted,true);
  localDeaf=true;localListeners.forEach(f=>f());
  setTimeout(()=>{
   assert.equal(sent.at(-1).participants.find(p=>p.self).deaf,true);
   localMute=false;localDeaf=false;localListeners.forEach(f=>f());
   setTimeout(()=>{
    assert.equal(sent.at(-1).participants.find(p=>p.self).muted,false);
    assert.equal(sent.at(-1).participants.find(p=>p.self).deaf,false);
    console.log('Local audio store: mute, deafen and unmute update without gateway events');
   },50);
  },50);
 },50);
},350);

// Ringing DM has only self voice state; identity comes from channel recipients.
setTimeout(()=>{
 channel='dm-ringing';
 common.ChannelStore.getChannel=()=>({recipients:['10','20']});
 common.VoiceStateStore.getVoiceStatesForChannel=()=>({'10':{userId:'10'}});
 handlers.VOICE_STATE_UPDATES({});
 setTimeout(()=>{
  assert.equal(sent.at(-1).channel,'Other');
  assert.equal(sent.at(-1).image,'https://cdn.discordapp.com/avatars/20/a_hash.png?size=128');
  assert.equal(sent.at(-1).participants.length,1);
  console.log('Ringing DM: recipient name/avatar available before answer; no fake participants');
 },60);
},650);
