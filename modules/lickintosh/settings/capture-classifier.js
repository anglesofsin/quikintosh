.pragma library
function truth(value){return value===true || value===1 || value==='true' || value==='1'}
function classify(nodes) {
 const result={mic:[],camera:[],screen:[],audio:[],details:[]},byId={},incoming={}
 if(!Array.isArray(nodes))return result
 for(const n of nodes)byId[String(n.id)]=n
 for(const n of nodes){const p=n.info?.props || {};if(n.info?.state==='active' && p['link.input.node']!==undefined && byId[String(p['link.output.node'])]){const id=String(p['link.input.node']);(incoming[id] || (incoming[id]=[])).push(byId[String(p['link.output.node'])])}}
 function props(n){return n?.info?.props || {}}
 function audioKind(n,seen){
  if(!n || seen[String(n.id)])return ''
  seen[String(n.id)]=true
  const p=props(n),kind=String(p['media.class'] || ''),name=String(p['node.name'] || '')
  if(truth(p['stream.capture.sink']) || p['device.class']==='monitor' || /\.monitor$/.test(name) || kind==='Audio/Sink')return 'audio'
  if(kind==='Stream/Output/Audio' && p['media.role']!=='DSP')return 'audio'
  // Effects and virtual microphones can have several DSP nodes between the
  // consumer and the physical input. Follow the active graph, not a node name.
  for(const source of incoming[String(n.id)] || []){const found=audioKind(source,seen);if(found)return found}
  return kind.startsWith('Audio/Source') ? 'mic':''
 }
 for(const node of nodes){
  const info=node.info || {},p=props(node),kind=p['media.class'] || ''
  if(info.state!=='running' || truth(p['node.disabled']) || !kind.startsWith('Stream/Input/'))continue
  const client=props(byId[String(p['client.id'])]),binary=String(p['application.process.binary'] || client['application.process.binary'] || ''),raw=String(p['application.name'] || client['application.name'] || binary || p['node.name'] || '')
  if(/cava|lickintosh.*spectrum/i.test(raw+' '+binary))continue
  let name=raw || 'Application'
  if(/equibop/i.test(binary+' '+raw))name='Equibop'
  else if(/discord|discord_capture/i.test(binary+' '+raw))name=/canary/i.test(binary+' '+raw) ? 'Discord Canary':/ptb/i.test(binary+' '+raw) ? 'Discord PTB':'Discord'
  else if(/webrtc|voiceengine|recstream/i.test(raw) && binary)name=binary.replace(/^\./,'').replace(/-wrapped$/,'')
  const id=String(p['application.id'] || client['application.id'] || binary || name).replace(/^\./,'').replace(/-wrapped$/,'').toLowerCase()
  for(const source of incoming[String(node.id)] || []){
   const sp=props(source);let category=''
   if(kind==='Stream/Input/Audio')category=truth(p['stream.capture.sink']) ? 'audio':audioKind(source,{})
   else if(kind==='Stream/Input/Video')category=/camera|v4l2|libcamera/i.test([sp['media.role'],sp['node.name'],sp['api.v4l2.path']].join(' ')) ? 'camera':'screen'
   if(!category)continue
   if(!result[category].includes(name))result[category].push(name)
   if(!result.details.some(d=>d.id===id && d.kind===category))result.details.push({id:id,app:name,kind:category})
  }
 }
 return result
}
