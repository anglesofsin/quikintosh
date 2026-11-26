local commands,config={},nil
hl={plugin={dynamic_cursors={},load=function(_)end},exec_cmd=function(cmd)table.insert(commands,cmd)end,config=function(value)config=value.plugin['dynamic_cursors']end}
local read=loadfile;loadfile=function(_)return nil end
dofile(arg[1]);loadfile=read
assert(commands[#commands]:match(' 31$'))
assert(config.mode=='none' and config.shake.enabled and not config.shake.effects)
assert(config.shake.base<config.shake.limit and config.shake.speed>0,'growth must be progressive')
assert(config.shake.threshold==6,'gesture should require sustained shaking')
local n=#commands
quickintosh_cursor({sensitivity=2,speed=2.2,timeout=1100})
assert(config.shake.threshold==3 and config.shake.limit==4 and config.shake.speed==2.2 and config.shake.timeout==1100)
assert(#commands==n,'adjusting dynamics must not reload cursor theme')
quickintosh_cursor({scale=5})
assert(config.hyprcursor.enabled and config.hyprcursor.resolution==310 and config.hyprcursor.nearest==0)
assert(#commands==n+1,'resolution must refresh when maximum enlargement changes')
quickintosh_cursor({shake=false})
assert(not config.enabled and not config.shake.enabled)
quickintosh_cursor({shake=true,size=40})
assert(config.enabled and commands[#commands]:match(' 40$'))
print('CURSOR_NATIVE_CONFIG_OK')
