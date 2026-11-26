-- Native locator: bounded rolling gesture history, no position IPC/daemon.
local current={size=31,theme='MacTahoe-cursors',shake=true,scale=2.5,sensitivity=1}
local timer,settle,shrink,history,tick,lastSize,visual,large
local function apply(size)
    size=math.floor(size+.5)
    if size==lastSize then return end
    lastSize=size
    hl.exec_cmd('hyprctl setcursor '..current.theme..' '..size)
end
local function restore()
    large=false
    shrink:set_enabled(true)
end
quickintosh_cursor=function(options)
    for key,value in pairs(options or {}) do current[key]=value end
    current.size=math.max(16,math.min(96,tonumber(current.size) or 31))
    current.scale=math.max(1.5,math.min(4,tonumber(current.scale) or 2.5))
    current.sensitivity=math.max(.5,math.min(2,tonumber(current.sensitivity) or 1))
    if not tostring(current.theme):match('^[%w_-]+$') then current.theme='MacTahoe-cursors' end
    large=false;history={};tick=0;visual=current.size;lastSize=nil
    if settle then settle:set_enabled(false) end
    if shrink then shrink:set_enabled(false) end
    apply(current.size)
    if timer then timer:set_enabled(current.shake~=false) end
end
shrink=hl.timer(function()
    visual=visual+(current.size-visual)*.48
    if math.abs(visual-current.size)<1.5 then visual=current.size;shrink:set_enabled(false) end
    apply(visual)
end,{timeout=75,type='repeat'})
shrink:set_enabled(false)
settle=hl.timer(function() settle:set_enabled(false);restore() end,{timeout=650,type='repeat'})
settle:set_enabled(false)
timer=hl.timer(function()
    local p=hl.get_cursor_pos()
    if not p then return end
    tick=tick+1
    history[#history+1]={x=p.x,y=p.y,t=tick}
    while #history>13 do table.remove(history,1) end
    if #history<4 then return end
    local turns,total,stroke=0,0,0
    local axisX,axisY=0,0
    for i=2,#history do
        local a,b=history[i-1],history[i]
        local x,y=b.x-a.x,b.y-a.y
        local distance=math.sqrt(x*x+y*y)
        -- Ignore sensor noise and monitor warps; don't mistake a jump for shake.
        if distance>600 then history={b};return end
        if distance>3 then
            total=total+distance
            if stroke>=14/current.sensitivity and (x*axisX+y*axisY)<-.35*distance then
                turns=turns+1;stroke=0
            end
            if stroke==0 or (x*axisX+y*axisY)>=0 then
                axisX,axisY=x/distance,y/distance
            end
            stroke=stroke+distance
        end
    end
    local first,last=history[1],history[#history]
    local elapsed=math.max(.04,(last.t-first.t)*.04)
    local displacement=math.sqrt((last.x-first.x)^2+(last.y-first.y)^2)
    if turns>=3 and total>150/current.sensitivity and total/elapsed>650/current.sensitivity and displacement<total*.6 then
        if not large then
            large=true;shrink:set_enabled(false)
            visual=current.size*current.scale;apply(visual)
        end
        -- Keep the locator visible while shaking, rather than timing out mid-gesture.
        settle:set_timeout(650)
    end
end,{timeout=40,type='repeat'})
local file=os.getenv('HOME')..'/.config/quickintosh/cursor.lua'
local load=loadfile(file)
if load then local ok,value=pcall(load);if ok and type(value)=='table' then quickintosh_cursor(value) else quickintosh_cursor({}) end else quickintosh_cursor({}) end
