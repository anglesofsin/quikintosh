function entries(text) {return String(text || '').split(/[\n,;]/).map(s=>s.trim().toLowerCase()).filter(Boolean)}
function matches(list, value) {return entries(list).includes(String(value || '').trim().toLowerCase())}
function scheduled(p, now) {
 if(!p.schedule)return false
 function minute(s){const v=String(s).match(/^(\d{1,2}):(\d{2})$/);return v && +v[1]<24 && +v[2]<60 ? +v[1]*60 + +v[2]:-1}
 const start=minute(p.start),end=minute(p.end),time=now.getHours()*60+now.getMinutes()
 if(start<0 || end<0 || start===end)return false
 const day=start>end && time<end ? (now.getDay()+6)%7:now.getDay()
 return (p.days || [0,1,2,3,4,5,6]).includes(day) && (start<end ? time>=start && time<end:time>=start || time<end)
}
function permits(p, app, sender, critical, timeSensitive) {
 if(critical && p.allowCritical!==false)return true
 if(timeSensitive && p.timeSensitive)return true
 const named=sender && matches(p.people,sender)
 if(p.peopleMode==='allow' && named)return true
 if(p.peopleMode==='silence' && named)return false
 const found=matches(p.apps,app)
 return p.appMode==='silence' ? !found:found
}
