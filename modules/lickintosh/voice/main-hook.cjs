/* Local metadata companion; no client credentials or messages are accessed. */
const {app,webContents} = require('electron');
const fs=require('node:fs'),path=require('node:path');
if(app && !app.__lickintoshVoiceCompanion){
 app.__lickintoshVoiceCompanion=true;
 const attached=new WeakSet();
 function inject(contents){
  if(contents.isDestroyed())return;
  try{
   const url=new URL(contents.getURL());
   if(url.protocol!=='https:' || !['discord.com','canary.discord.com','ptb.discord.com'].includes(url.hostname))return;
   const source=fs.readFileSync(path.join(__dirname,'discord-bridge.js'),'utf8');
   const name=app.getName().toLowerCase();const client=name.includes('canary')?'canary':name.includes('ptb')?'ptb':name.includes('equibop')?'equibop':'stable';
   contents.executeJavaScript('globalThis.__lickintoshVoiceClient='+JSON.stringify(client)+';\n'+source).catch(()=>{});
  }catch{}
 }
 function attach(contents){
  if(attached.has(contents))return;attached.add(contents);
  contents.on('did-finish-load',()=>inject(contents));
  contents.on('dom-ready',()=>inject(contents));
  if(!contents.isLoading())inject(contents);
 }
 app.on('web-contents-created',(_event,contents)=>attach(contents));
 app.whenReady().then(()=>{for(const contents of webContents.getAllWebContents())attach(contents)});
 const repair=setInterval(()=>{for(const contents of webContents.getAllWebContents()){attach(contents);inject(contents)}},15000);
 repair.unref();app.once('will-quit',()=>clearInterval(repair));
}
