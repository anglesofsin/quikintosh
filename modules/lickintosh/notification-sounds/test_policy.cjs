const assert=require('node:assert/strict');
const {permitted}=require('./policy.js');
const base={dnd:false,preview:false,enabled:true,allowed:true,appSound:true,suppress:false,volume:.6};
assert.equal(permitted(base),true);
for(const change of [{replayed:true},{dnd:true},{enabled:false},{allowed:false},{appSound:false},{suppress:true},{volume:0}])assert.equal(permitted({...base,...change}),false);
assert.equal(permitted({...base,preview:true,dnd:true}),false);
assert.equal(permitted({...base,preview:true,enabled:false}),true);
console.log('Notification audio: default, DND, disabled, per-app, suppress hint, muted and preview policy passed');
