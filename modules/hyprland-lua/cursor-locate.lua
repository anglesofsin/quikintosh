-- Locate the pointer without spawning a position-polling daemon.
local current={size=31,theme='MacTahoe-cursors',shake=true,scale=2.5,sensitivity=1}
local timer,restore,last,dx,dy,turns,travel,ticks,large
local function apply(size)
    hl.exec_cmd('hyprctl setcursor '..current.theme..' '..math.floor(size))
end
quickintosh_cursor=function(options)
    for key,value in pairs(options or {}) do current[key]=value end
    current.size=math.max(16,math.min(96,tonumber(current.size) or 31))
    current.scale=math.max(1.5,math.min(4,tonumber(current.scale) or 2.5))
    current.sensitivity=math.max(.5,math.min(2,tonumber(current.sensitivity) or 1))
    if not tostring(current.theme):match('^[%w_-]+$') then current.theme='MacTahoe-cursors' end
    large=false;turns=0;travel=0;ticks=0;last=nil;dx=0;dy=0
    apply(current.size)
    if timer then timer:set_enabled(current.shake~=false) end
end
restore=hl.timer(function() large=false;apply(current.size);restore:set_enabled(false) end,{timeout=1100,type='repeat'})
restore:set_enabled(false)
timer=hl.timer(function()
    local p=hl.get_cursor_pos()
    if not p then return end
    if last then
        local x,y=p.x-last.x,p.y-last.y
        local distance=math.sqrt(x*x+y*y)
        if distance>3 and distance<350 then
            travel=travel+distance
            if (math.abs(x)>5 and x*dx<0) or (math.abs(y)>5 and y*dy<0) then turns=turns+1 end
            if math.abs(x)>5 then dx=x end
            if math.abs(y)>5 then dy=y end
            if turns>=4 and travel>220/current.sensitivity then
                if not large then large=true;apply(current.size*current.scale) end
                restore:set_timeout(1100);turns=0;travel=0;ticks=0
            end
        end
    end
    last=p;ticks=ticks+1
    if ticks>14 then turns=0;travel=0;ticks=0 end
    if not large then restore:set_enabled(false) end
end,{timeout=40,type='repeat'})
local file=os.getenv('HOME')..'/.config/quickintosh/cursor.lua'
local load=loadfile(file)
if load then local ok,value=pcall(load);if ok and type(value)=='table' then quickintosh_cursor(value) else quickintosh_cursor({}) end else quickintosh_cursor({}) end
