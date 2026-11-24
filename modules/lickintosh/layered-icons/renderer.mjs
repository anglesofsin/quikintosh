// Local layered renderer. Artwork stays on this machine; no remote API or AI calls.
import {createServer} from 'node:http';
import {readFile,writeFile,mkdir,mkdtemp,rm,stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {join,extname,resolve} from 'node:path';
import {tmpdir,setPriority} from 'node:os';
import {createInterface} from 'node:readline';
const cache=process.env.HOME+'/.cache/lickintosh/icon-composer',dist=process.argv[2],chrome=process.argv[3],python=process.argv[4],converter=process.argv[5];
await mkdir(cache,{recursive:true});
let index={};try{index=JSON.parse(await readFile(join(cache,'index.json'),'utf8'))}catch{}
let browser,server,ws,profile,id=0,pending=new Map(),idle,queue=[],busy=false,software=false;
const emit=o=>process.stdout.write(JSON.stringify(o)+'\n');
function cdp(method,params={}){return new Promise((accept,reject)=>{const n=++id;const t=setTimeout(()=>{pending.delete(n);reject(Error('Renderer command timed out'))},60000);pending.set(n,{accept,reject,t});ws.send(JSON.stringify({id:n,method,params}))})}
async function evaluate(expression){const data=await cdp('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(data.exceptionDetails)throw Error(data.exceptionDetails.exception?.description || data.exceptionDetails.text);return data.result.value}
async function call(method,args){return evaluate(`window.liquidComposer[${JSON.stringify(method)}](${JSON.stringify(args)})`)}
async function stop(){
 clearTimeout(idle);const oldProfile=profile,oldBrowser=browser;profile=null;browser=null;
 for(const p of pending.values()){clearTimeout(p.t);p.reject(Error('Renderer stopped'))}pending.clear();
 if(ws){ws.close();ws=null}if(server){server.close();server=null}
 if(oldBrowser){await new Promise(ok=>{const t=setTimeout(ok,2000);oldBrowser.once('exit',()=>{clearTimeout(t);ok()});try{process.kill(-oldBrowser.pid,'SIGTERM')}catch{oldBrowser.kill()}})}
 if(oldProfile)await rm(oldProfile,{recursive:true,force:true,maxRetries:5,retryDelay:100}).catch(()=>{});
}
async function start(){try{await boot()}catch(error){if(software)throw error;software=true;await stop();await boot()}}
async function boot(){
 if(ws?.readyState===1)return;
 server=createServer(async(req,res)=>{try{const relative=decodeURIComponent((req.url || '/').split('?')[0]);const file=resolve(dist,'.'+(relative==='/' ? '/index.html':relative));if(!file.startsWith(resolve(dist)+'/'))throw Error('path');let data=await readFile(file);if(extname(file)==='.js'){data=Buffer.from(data.toString().replace('Math.max(a,Math.min(2048,Math.max(1024,a*2)))','Math.max(a,512)').replace('Math.max(1024,Math.min(2048,Math.round((g??pl)*w)))','512'))}res.setHeader('Content-Type',({'.js':'text/javascript','.html':'text/html','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.woff2':'font/woff2'})[extname(file)] || 'application/octet-stream');res.end(data)}catch{res.statusCode=404;res.end()}});
 await new Promise(ok=>server.listen(0,'127.0.0.1',ok));
 profile=await mkdtemp(join(tmpdir(),'lickintosh-icon-composer-'));
 const env={...process.env};delete env.DISPLAY;delete env.WAYLAND_DISPLAY;
 browser=spawn(chrome,['--headless=new','--remote-debugging-port=0','--remote-debugging-address=127.0.0.1','--user-data-dir='+profile,'--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-extensions',...(software ? ['--use-angle=swiftshader','--enable-unsafe-swiftshader']:['--use-angle=vulkan','--enable-features=Vulkan','--disable-vulkan-surface']),'about:blank'],{env,detached:true,stdio:['ignore','ignore','ignore']});
 try{setPriority(browser.pid,10)}catch{}
 let port;
 for(let i=0;i<150;i++){try{port=(await readFile(join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];break}catch{await new Promise(ok=>setTimeout(ok,100))}}
 if(!port)throw Error('Headless icon renderer could not start');
 const pages=await (await fetch('http://127.0.0.1:'+port+'/json/list')).json();
 ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
 ws.onmessage=e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(p){clearTimeout(p.t);pending.delete(m.id);m.error ? p.reject(Error(m.error.message)):p.accept(m.result)}};
 await new Promise((ok,no)=>{ws.onopen=ok;ws.onerror=no});
 await cdp('Page.enable');await cdp('Page.navigate',{url:'http://127.0.0.1:'+server.address().port+'/?agent'});
 for(let i=0;i<150;i++){if(await evaluate('!!window.liquidComposer'))break;await new Promise(ok=>setTimeout(ok,100))}
 await evaluate('window.liquidComposer.ready');
}
async function convert(source){return new Promise((ok,no)=>{const p=spawn(python,[converter,source],{stdio:['ignore','pipe','pipe']});let out='',err='';p.stdout.on('data',s=>out+=s);p.stderr.on('data',s=>err+=s);p.on('error',no);p.on('exit',code=>code ? no(Error(err.trim() || 'Unsupported layered artwork')):ok(JSON.parse(out)))})}
async function render(job){
 const begin=performance.now();let source=job.source.replace(/^file:\/\//,'');source=decodeURIComponent(source);
 const data=await readFile(source),fingerprint=createHash('sha256').update(data).update(JSON.stringify({...job,key:'',source:''})).update('layer-composer-v5').digest('hex'),output=join(cache,fingerprint+'.png');
 try{await stat(output);return {key:job.key,path:output,cached:true,ms:Math.round(performance.now()-begin)}}catch{}
 const art=await convert(source),recipe=art.recipe;
 await start();
 // Validate original outer-path geometry before treating it as the container.
 // SVG coordinates and paths are preserved; no logo tracing is performed.
 if(art.backgroundCandidate && recipe.layers.length>1){
  const candidate=recipe.layers.at(-1);
  const background=await evaluate(`(()=>{const host=document.createElement('div');host.style.cssText='position:fixed;left:-10000px;visibility:hidden';host.innerHTML=${JSON.stringify(candidate.src)};document.body.append(host);try{const svg=host.firstElementChild,b=svg.lastElementChild.getBBox(),v=svg.viewBox.baseVal;return b.width/v.width>.8&&b.height/v.height>.8&&b.x<=v.x+v.width*.12&&b.y<=v.y+v.height*.12}finally{host.remove()}})()`);
  if(background)recipe.layers.pop();
 }

 if(art.layers<1)throw Error('No separable foreground layers');
 const appearance=job.appearance || 'dark',palette=job.palette || {},dark=job.dark;
 if(appearance==='tinted'){
  recipe.background={colors:[palette.container || (dark ? '#242429':'#e6e6ed'),palette.container || (dark ? '#242429':'#e6e6ed')]};
  for(const layer of recipe.layers){layer.fill={type:'solid',color:palette.ink || (dark ? '#eeeeee':'#222222')};layer.liquidGlass={enabled:true,specular:true,refraction:{enabled:true},translucency:{enabled:true,value:80},shadow:{enabled:true,value:15}}}
 }else if(appearance==='dark'){
  recipe.background={colors:['#252528','#101012']};
  for(const layer of recipe.layers)if(layer.inkDark)layer.fill={type:'solid',color:art.brand || '#f2f2f7'};
 }
 for(const layer of recipe.layers){delete layer.inkDark;if(layer.liquidGlass){layer.liquidGlass.specularIntensity=Math.round((job.strength ?? 1)*45);layer.liquidGlass.shadow={enabled:true,value:12}}}
 await start();
 const mode=appearance==='clear' ? (dark ? 'clearDark':'clear'):'default';
 let files;
 for(let attempt=0;attempt<2;attempt++){
  await call('apply',recipe);
  files=await call('export',{sizes:[256],modes:[mode],format:'png'});
  if(await evaluate('window.liquidComposer.state().webgl')==='active')break;
  if(software || attempt===1)throw Error('WebGL material renderer unavailable');
  software=true;await stop();await start();
 }
 const png=Buffer.from(files[0].base64,'base64');if(png.length<200)throw Error('Empty rendered icon');
 await writeFile(output+'.tmp',png);await import('node:fs/promises').then(fs=>fs.rename(output+'.tmp',output));
 await writeFile(join(cache,fingerprint+'.recipe.json'),JSON.stringify({source,artLayers:art.layers,recipe,appearance,dark},null,2));
 return {key:job.key,path:output,cached:false,layers:art.layers,ms:Math.round(performance.now()-begin)};
}
async function drain(){if(busy)return;busy=true;clearTimeout(idle);while(queue.length){const job=queue.shift();try{const result=await render(job);index[result.key]=result.path;await writeFile(join(cache,'index.json'),JSON.stringify(index));emit({type:'rendered',...result})}catch(error){emit({type:'error',key:job.key,message:String(error.message).slice(0,1200)});await stop()}}busy=false;idle=setTimeout(()=>stop(),12000)}
createInterface({input:process.stdin}).on('line',line=>{try{const job=JSON.parse(line);if(job.action==='quit'){stop().finally(()=>process.exit(0));return}if(queue.length<128){queue.push(job);drain()}else emit({type:'error',key:job.key,message:'Icon generation queue full; original artwork retained'})}catch{}}).on('close',()=>stop().finally(()=>process.exit(0)));
process.on('SIGTERM',()=>stop().finally(()=>process.exit(0)));emit({type:'ready',index});
