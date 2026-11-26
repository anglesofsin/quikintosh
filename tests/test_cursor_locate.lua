local callbacks,commands={},{}
local point={x=0,y=0}
hl={get_cursor_pos=function()return point end,exec_cmd=function(cmd)table.insert(commands,cmd)end}
hl.timer=function(callback,opts)
 local timer={enabled=true,callback=callback}
 function timer:set_enabled(value)self.enabled=value end
 function timer:set_timeout(_)self.enabled=true end
 table.insert(callbacks,timer);return timer
end
local read=loadfile
loadfile=function(_)return nil end
dofile(arg[1])
loadfile=read
assert(commands[#commands]:match(' 31$'))
local detector=callbacks[2]
for _,x in ipairs({0,100,-100,100,-100,100})do point={x=x,y=0};detector.callback()end
assert(commands[#commands]:match(' 77$'),'shake did not enlarge pointer')
callbacks[1].callback()
assert(commands[#commands]:match(' 31$'),'pointer size was not restored')
quickintosh_cursor({shake=false,size=40})
assert(not detector.enabled,'disabled detector is still scheduled')
assert(commands[#commands]:match(' 40$'))
print('CURSOR_LOCATE_OK')
