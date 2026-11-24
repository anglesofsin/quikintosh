.pragma library
function bounds(a) {
 if(a.tool==='text')return {x:a.x,y:a.y,w:Math.max(30,a.text.split('\n').reduce((n,s)=>Math.max(n,s.length),0)*a.fontSize*.65),h:a.text.split('\n').length*a.fontSize*1.3}
 if(a.tool==='pen'){let xs=a.points.map(p=>p.x),ys=a.points.map(p=>p.y);return {x:Math.min.apply(null,xs)-5,y:Math.min.apply(null,ys)-5,w:Math.max.apply(null,xs)-Math.min.apply(null,xs)+10,h:Math.max.apply(null,ys)-Math.min.apply(null,ys)+10}}
 return {x:Math.min(a.x,a.x2),y:Math.min(a.y,a.y2),w:Math.abs(a.x2-a.x),h:Math.abs(a.y2-a.y)}
}
function contains(a,x,y) {const b=bounds(a);return x>=b.x-6 && x<=b.x+b.w+6 && y>=b.y-6 && y<=b.y+b.h+6}
function move(a,dx,dy) {const out=JSON.parse(JSON.stringify(a));if(out.points)out.points=out.points.map(p=>({x:p.x+dx,y:p.y+dy}));if(out.x!==undefined){out.x+=dx;out.y+=dy}if(out.x2!==undefined){out.x2+=dx;out.y2+=dy}return out}
function paint(ctx,items,canvas) {
 for(const a of items) {
  ctx.save();ctx.strokeStyle=a.color;ctx.fillStyle=a.color;ctx.lineWidth=a.size;ctx.lineCap='round';ctx.lineJoin='round';ctx.beginPath()
  const x=a.x,y=a.y,dx=a.x2-x,dy=a.y2-y
  if(a.tool==='arrow') {
   ctx.moveTo(x,y);ctx.lineTo(a.x2,a.y2);ctx.stroke()
   const angle=Math.atan2(dy,dx),head=Math.max(12,a.size*4)
   ctx.beginPath();ctx.moveTo(a.x2,a.y2);ctx.lineTo(a.x2-head*Math.cos(angle-.5),a.y2-head*Math.sin(angle-.5));ctx.lineTo(a.x2-head*Math.cos(angle+.5),a.y2-head*Math.sin(angle+.5));ctx.closePath();ctx.fill()
  } else if(a.tool==='rect')ctx.strokeRect(Math.min(x,a.x2),Math.min(y,a.y2),Math.abs(dx),Math.abs(dy))
  else if(a.tool==='ellipse') {const b=bounds(a);ctx.ellipse(b.x,b.y,b.w,b.h);ctx.stroke()}
  else if(a.tool==='pen') {a.points.forEach((p,i)=>{if(i)ctx.lineTo(p.x,p.y);else ctx.moveTo(p.x,p.y)});ctx.stroke()}
  else if(a.tool==='text') {ctx.font=a.fontSize+'px "SF Pro Text"';ctx.textBaseline='top';a.text.split('\n').forEach((line,i)=>ctx.fillText(line,a.x,a.y+i*a.fontSize*1.3))}
  else if(a.tool==='highlight'){const b=bounds(a);ctx.globalAlpha=.3;ctx.fillRect(b.x,b.y,b.w,b.h)}
  else if(a.tool==='mosaic' || a.tool==='blur') {const b=bounds(a);if(a.path && canvas.isImageLoaded(a.path))ctx.drawImage(a.path,b.x,b.y,b.w,b.h);else if(a.path)canvas.loadImage(a.path);else {ctx.fillStyle='#66777777';ctx.fillRect(b.x,b.y,b.w,b.h)}}
  ctx.restore()
 }
}
