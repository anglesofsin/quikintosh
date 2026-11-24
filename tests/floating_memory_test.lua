local module = dofile('modules/hyprland-lua/remember-floating.lua')
local handlers, windows, saved, profile, writes = {}, {}, {}, 'lickintosh', 0
local api = {dsp = {window = {float = function(value) return value end, resize = function(value) return value end}}}
function api.get_windows() return windows end
function api.on(name, callback) handlers[name] = callback end
function api.dispatch(action)
    for _, w in ipairs(windows) do
        if action.window == 'address:' .. w.address then
            if action.action then w.floating = true; handlers['window.update_rules'](w)
            else w.size={x=action.x,y=action.y} end
        end
    end
end
local controller = module.install(api, {
    profile = function() return profile end,
    load = function(key) saved[key] = saved[key] or {}; return saved[key] end,
    save = function() writes = writes + 1 end,
    eligible = function(w) return not w.canvas and not w.special end,
})
local function window(address, class, floating)
    local w = {address=address, class=class, initial_class=class, floating=floating,size={x=640,y=480}}
    windows[#windows+1]=w; controller.open(w); return w
end
local finder=window('1','org.gnome.Nautilus',false)
assert(writes==0)
finder.floating=true; controller.changed(finder)
assert(saved.lickintosh['org.gnome.Nautilus'] and writes==1)
finder.size={x=900,y=620}
controller.closed(finder)
local reopened=window('2','org.gnome.Nautilus',false)
assert(reopened.size.x==900 and reopened.size.y==620)
assert(reopened.floating and writes==2, 'Restore must not learn itself')
reopened.floating=false; controller.changed(reopened)
assert(not saved.lickintosh['org.gnome.Nautilus'])
assert(not window('3','org.gnome.Nautilus',false).floating)
local auto=window('4','automatic-dialog',true)
assert(not saved.lickintosh['automatic-dialog'], 'Default float is not a user transition')
auto.canvas=true; auto.floating=false; controller.changed(auto)
assert(not saved.lickintosh['automatic-dialog'])
finder.floating=false; controller.changed(finder)
finder.floating=true; controller.changed(finder)
profile='noctalia-legacy'
assert(not window('5','org.gnome.Nautilus',false).floating, 'Profiles must be isolated')
controller.changed(finder)
assert(not saved['noctalia-legacy']['org.gnome.Nautilus'], 'Switching profile must not learn old state')
profile='lickintosh'
local resized=window('8','focus-size',false)
resized.floating=true;controller.changed(resized)
handlers['window.active'](resized)
resized.size={x=780,y=540}
handlers['window.active'](nil)
assert(saved.lickintosh['focus-size'].width==780 and saved.lickintosh['focus-size'].height==540)
local path=os.tmpname();module.write(path,{['class.with.spaces']=true,['org.gnome.Nautilus']={width=900,height=620}})
assert(module.read(path)['class.with.spaces']);assert(module.read(path)['org.gnome.Nautilus'].width==900);os.remove(path)
print('Floating memory: learn, restore size, reset, dialog/canvas exclusion, profile isolation and disk roundtrip passed')
