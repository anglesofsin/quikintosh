-- Continuous native scaling. Theme reloads happen only on preference changes.
local current={size=31,theme='MacTahoe-cursors',shake=true,scale=4,sensitivity=1,speed=1.7,timeout=900}
local previousTheme,previousSize,previousResolution
local ok,reason=pcall(function()
    hl.plugin.load('@CURSOR_LOCATOR_PLUGIN@')
end)
if not ok then
    local log=io.open(os.getenv('HOME')..'/.local/state/quickintosh-cursor-error.log','a')
    if log then log:write(tostring(reason),'\n');log:close() end
end
quickintosh_cursor=function(options)
    for key,value in pairs(options or {}) do current[key]=value end
    current.size=math.max(16,math.min(96,tonumber(current.size) or 31))
    current.scale=math.max(1.5,math.min(8,tonumber(current.scale) or 4))
    current.sensitivity=math.max(.5,math.min(2,tonumber(current.sensitivity) or 1))
    current.speed=math.max(.3,math.min(5,tonumber(current.speed) or 1.7))
    current.timeout=math.max(200,math.min(3000,tonumber(current.timeout) or 900))
    if not tostring(current.theme):match('^[%w_-]+$') then current.theme='MacTahoe-cursors' end
    local resolution=math.min(512,math.ceil(current.size*current.scale*2))
    if previousTheme~=current.theme or previousSize~=current.size or previousResolution~=resolution then
        hl.exec_cmd('hyprctl setcursor '..current.theme..' '..math.floor(current.size+.5))
        previousTheme,previousSize,previousResolution=current.theme,current.size,resolution
    end
    if hl.plugin and hl.plugin.dynamic_cursors then
        hl.config({plugin={dynamic_cursors={
            enabled=current.shake~=false,mode='none',ignore_warps=true,
            shake={enabled=current.shake~=false,effects=false,ipc=false,
                threshold=6/current.sensitivity,base=1.15,speed=current.speed,
                influence=.12,limit=current.scale,timeout=current.timeout},
            hyprcursor={enabled=true,nearest=0,resolution=resolution,fallback="clientside"}
        }}})
    end
end
local file=os.getenv('HOME')..'/.config/quickintosh/cursor.lua'
local load=loadfile(file)
if load then local valid,value=pcall(load);if valid and type(value)=='table' then quickintosh_cursor(value) else quickintosh_cursor({}) end else quickintosh_cursor({}) end
