local callbacks,commands={},{}
local point={x=0,y=0}
hl={get_cursor_pos=function()return point end,exec_cmd=function(cmd)table.insert(commands,cmd)end}
hl.timer=function(callback,opts)
 local timer={enabled=true,callback=callback,renewals=0}
 function timer:set_enabled(value)self.enabled=value end
 function timer:set_timeout(_)self.enabled=true;self.renewals=self.renewals+1 end
 table.insert(callbacks,timer);return timer
end
local read=loadfile;loadfile=function(_)return nil end
dofile(arg[1]);loadfile=read
local decay,settle,detector=callbacks[1],callbacks[2],callbacks[3]
local function move(x,y)point={x=x,y=y or 0};detector.callback()end
local function reset()quickintosh_cursor({shake=true,size=31});commands={}end
reset()
for x=0,1200,80 do move(x)end
assert(#commands==0,'straight movement triggered locator')
reset()
for i=1,30 do move(i%2*2)end
assert(#commands==0,'sensor jitter triggered locator')
reset()
for i=1,20 do move(i%2*20)end
assert(#commands==0,'slow reversals triggered locator')
reset()
move(0);move(1000);move(0)
assert(#commands==0,'monitor warp triggered locator')
reset()
for _=1,11 do move(0)end
for _,x in ipairs({0,80,-80,80,-80,80})do move(x)end
assert(commands[#commands]:match(' 78$'),'rapid reversals did not enlarge pointer')
local renewals=settle.renewals
for _,x in ipairs({-80,80,-80,80})do move(x)end
assert(settle.renewals>renewals,'continued gesture did not extend locator')
settle.callback();assert(decay.enabled)
decay.callback();local first=tonumber(commands[#commands]:match('(%d+)$'))
assert(first>31 and first<78,'return was not gradual')
for _=1,12 do if decay.enabled then decay.callback()end end
assert(commands[#commands]:match(' 31$') and not decay.enabled,'pointer was not restored')
quickintosh_cursor({shake=false,size=40})
assert(not detector.enabled and not settle.enabled and not decay.enabled)
assert(commands[#commands]:match(' 40$'))
print('CURSOR_LOCATE_OK')
