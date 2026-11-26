local module=dofile('modules/hyprland-lua/remember-floating.lua')
local windows,handlers,writes={}, {},0
local api={dsp={window={float=function(a)return a end,resize=function(a)return a end}}}
function api.get_windows() return windows end
function api.on(name,fn)handlers[name]=fn end
function api.dispatch(a)for _,w in ipairs(windows)do if a.window=='address:'..w.address then w.floating=true;handlers['window.update_rules'](w) end end end
local c=module.install(api,{profile=function()return 'test' end,load=function()return {} end,save=function()writes=writes+1 end,eligible=function(w)return not w.special end,inheritEligible=function(w)return not w.canvas and not w.chooser end})
local function add(id,class,pid,floating,extra)
 local w={address=id,class=class,initial_class=class,pid=pid,floating=floating,fullscreen=0}
 for k,v in pairs(extra or {})do w[k]=v end
 windows[#windows+1]=w;c.open(w);return w
end
add('1','discord',100,true,{special=true})
assert(add('2','discord',100,false).floating,'DevTools inherits scratchpad float')
assert(add('3','discord',101,false).floating,'Same application inherits float')
assert(not add('4','kitty',200,false).floating,'Unrelated app stays tiled')
add('5','electron',300,true)
assert(not add('6','electron',301,false).floating,'Generic Electron class is not application identity')
assert(add('7','devtools',100,false).floating,'Same process with distinct class inherits')
add('8','canvas-app',400,true,{canvas=true})
assert(not add('9','canvas-app',400,false).floating,'Canvas is not a floating preference')
assert(not add('10','discord',100,false,{chooser=true}).floating,'Dedicated chooser rules remain independent')
assert(writes==0,'Inheritance is not persisted as a user change')
print('Floating inheritance cases passed')
