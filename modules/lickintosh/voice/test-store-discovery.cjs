const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const sent=[];let socket;const dispatcher={subscribe(){},unsubscribe(){},dispatch(){}};
const stores=[{getName:()=> 'UserStore',getCurrentUser:()=>({id:'10'}),getUser:()=>({id:'10',username:'Self'})},{getName:()=> 'VoiceStateStore',getVoiceStateForUser:()=>({channelId:'123'}),getVoiceStatesForChannel:()=>({})},{getName:()=> 'ChannelStore',getChannel:()=>({name:'Canary call',recipients:[]})},dispatcher];
const req={c:Object.fromEntries(stores.map((s,i)=>[i,{exports:{default:s}}]))};
class WS{static OPEN=1;constructor(){socket=this;this.readyState=1}send(s){sent.push(JSON.parse(s))}close(){}}
const ctx={WebSocket:WS,DiscordNative:{app:{getReleaseChannel:()=> 'canary'}},location:{hostname:'discord.com'},webpackChunkdiscord_app:{push:args=>args[2](req)},setTimeout,clearTimeout,addEventListener(){}};
vm.runInNewContext(fs.readFileSync(__dirname+'/discord-bridge.js','utf8'),ctx);assert(socket);socket.onopen();assert.equal(sent.at(-1).client,'canary');assert.equal(sent.at(-1).active,true);assert.equal(sent.at(-1).channel,'Canary call');console.log('Native Canary identity and independent store discovery passed');
