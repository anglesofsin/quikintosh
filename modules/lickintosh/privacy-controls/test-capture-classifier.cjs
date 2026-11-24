const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');const c={};vm.createContext(c);vm.runInContext(fs.readFileSync(__dirname+'/../settings/capture-classifier.js','utf8').replace('.pragma library',''),c);
const node=(id,cls,props={},state='running')=>({id,info:{state,props:{'media.class':cls,...props}}});
const link=(out,input,state='active')=>({info:{state,props:{'link.output.node':out,'link.input.node':input}}});
const capture=node(4,'Stream/Input/Audio',{'application.name':'WEBRTC VoiceEngine','application.process.binary':'.Discord-wrapped'});
function run(ns){return JSON.parse(JSON.stringify(c.classify(ns)))}
let r=run([node(1,'Audio/Source'),node(2,'',{'media.role':'DSP'}),node(3,'Audio/Source/Virtual'),capture,link(1,2),link(2,3),link(3,4)]);assert.deepEqual(r.mic,['Discord']);assert.deepEqual(r.audio,[]);
r=run([node(3,'Audio/Source',{'stream.capture.sink':'false'}),capture,link(3,4)]);assert.deepEqual(r.mic,['Discord']);
r=run([node(3,'Audio/Sink'),capture,link(3,4)]);assert.deepEqual(r.audio,['Discord']);assert.deepEqual(r.mic,[]);
r=run([node(3,'Audio/Source',{'node.name':'output.monitor'}),capture,link(3,4)]);assert.deepEqual(r.audio,['Discord']);
r=run([node(3,'Audio/Source'),capture,link(3,4,'paused')]);assert.deepEqual(r.details,[]);
r=run([node(3,'Audio/Source'),capture]);assert.deepEqual(r.details,[]);
r=run([node(3,'Audio/Source'),node(4,'Stream/Input/Audio',{'application.name':'WEBRTC VoiceEngine','application.process.binary':'DiscordCanary'}),link(3,4)]);assert.deepEqual(r.mic,['Discord Canary']);
r=run([node(3,'Audio/Source'),node(4,'Stream/Input/Audio',{'application.name':'Discord','application.process.binary':'equibop'}),link(3,4)]);assert.deepEqual(r.mic,['Equibop']);
r=run([node(3,'Video/Source',{'media.role':'Camera'}),node(4,'Stream/Input/Video',{'application.name':'Camera Test'}),link(3,4)]);assert.deepEqual(r.camera,['Camera Test']);
r=run([node(3,'Video/Source',{'node.name':'screen-cast'}),node(4,'Stream/Input/Video',{'application.name':'Screen Test'}),link(3,4)]);assert.deepEqual(r.screen,['Screen Test']);
r=run([node(3,'Audio/Source'),node(4,'Stream/Input/Audio',{'application.name':'Discord'},'suspended'),link(3,4)]);assert.deepEqual(r.details,[]);
r=run([node(3,'Audio/Source'),node(4,'Stream/Input/Audio',{'application.name':'Discord','node.disabled':true}),link(3,4)]);assert.deepEqual(r.details,[]);
console.log('12 capture graph regressions passed');
