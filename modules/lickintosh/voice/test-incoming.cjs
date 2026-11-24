const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const handlers={},sent=[],actions=[];let ring={channelId:'22',ringing:['10']};let joined=null;
class WS{static OPEN=1;constructor(){this.readyState=1;global.socket=this}send(s){sent.push(JSON.parse(s))}close(){}}
const common={UserStore:{getCurrentUser:()=>({id:'10'}),getUser:id=>({id,username:'Caller',avatar:'hash'})},
 VoiceStateStore:{getVoiceStateForUser:()=>({channelId:joined}),getVoiceStatesForChannel:()=>({})},
 ChannelStore:{getChannel:()=>({recipients:['20']})},CallStore:{getAllCalls:()=>ring?{'22':ring}:{}},
 VoiceActions:{selectVoiceChannel:id=>actions.push(['accept',id])},CallActions:{stopRinging:(id,users)=>actions.push(['reject',id,...users])},
 FluxDispatcher:{subscribe:(k,f)=>handlers[k]=f,unsubscribe:()=>{}}};
vm.runInNewContext(fs.readFileSync(__dirname+'/discord-bridge.js','utf8'),{WebSocket:WS,Vencord:{Webpack:{Common:common}},location:{hostname:'discord.com'},setTimeout,clearTimeout,addEventListener:()=>{}});
socket.onopen();assert.equal(sent.at(-1).state,'incoming');assert.equal(sent.at(-1).incomingControls,true);assert.equal(sent.at(-1).channel,'Caller');
socket.onmessage({data:JSON.stringify({type:'control',action:'accept',channelId:'other'})});assert.equal(actions.length,0);
for(const action of ['accept','reject'])socket.onmessage({data:JSON.stringify({type:'control',action,channelId:'22'})});
assert.equal(actions[0][0],'accept');assert.equal(actions[1][0],'reject');
ring=null;handlers.CALL_DELETE();setTimeout(()=>{assert.equal(sent.at(-1).active,false);assert.equal(sent.at(-1).state,'idle');console.log('Incoming call identity, accept/reject, stale target and caller cancellation passed')},60);
