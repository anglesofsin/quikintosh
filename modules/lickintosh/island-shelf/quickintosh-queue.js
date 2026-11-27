// Local queue metadata only: no credentials, playback tokens or external requests.
(async function quickintoshQueue(){
 while(!globalThis.Spicetify?.Player || !Spicetify.Queue)await new Promise(r=>setTimeout(r,500));
 const endpoint='http://127.0.0.1:43891/queue';
 const key='@LOCAL_BRIDGE_KEY@';let busy=false;
 function row(provided){
  const track=provided?.contextTrack || provided?.track || provided;
  const meta=track?.metadata || {};const uri=track?.uri || provided?.uri || '';
  let art=meta.image_xlarge_url || meta.image_large_url || meta.image_url || '';
  if(art.startsWith('spotify:image:'))art='https://i.scdn.co/image/'+art.split(':').pop();
  return {uri,title:meta.title || track?.name || '',artist:meta.artist_name || '',art,length:Number(meta.duration || meta.duration_ms || track?.duration?.milliseconds || 0)/1000};
 }
 async function send(){
  if(busy)return;busy=true;
  try{const queue=Spicetify.Queue;const items=(queue?.nextTracks || []).map(row);
   await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json','X-Quickintosh-Key':key},body:JSON.stringify({items}),signal:AbortSignal.timeout(1500)});
  }catch(_){}finally{busy=false;}
 }
 Spicetify.Player.addEventListener('songchange',send);
 setInterval(send,3000);send();
})();
