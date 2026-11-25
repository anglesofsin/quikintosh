// Inspect playback state only: no audio samples or changes to another app.
function activeOutputs(data,ownPid){
 const apps=[]
 for(const node of data || []){
  const info=node.info || {},p=info.props || {}
  if(p['media.class']!=='Stream/Output/Audio' || info.state!=='running')continue
  if(String(p['application.process.id'] || '')===String(ownPid))continue
  if(['notification','event','alert'].includes(String(p['media.role'] || '').toLowerCase()))continue
  if(!p['application.process.id'] && /quickshell|quickintosh/i.test(String(p['application.name'] || p['node.name'] || '')))continue
  const params=info.params?.Props || []
  if(params.some(v=>v.mute===true || Array.isArray(v.channelVolumes) && v.channelVolumes.length && v.channelVolumes.every(n=>n<=0)))continue
  apps.push(String(p['application.name'] || p['node.description'] || p['node.name'] || 'Audio'))
 }
 return Array.from(new Set(apps))
}
