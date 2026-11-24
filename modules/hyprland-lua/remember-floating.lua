-- Learn explicit floating transitions, never the default state of a new window.
local M = {}
function M.read(path)
    local values, file = {}, io.open(path, "r")
    if file then
        for line in file:lines() do
            local class, width, height = line:match("^(.-)\t(%d+)\t(%d+)$")
            class = class or line
            if class ~= "" and not class:find("[%c]") then
                width, height = tonumber(width), tonumber(height)
                values[class] = width and height and width >= 64 and height >= 64
                    and {width = width, height = height} or true
            end
        end
        file:close()
    end
    return values
end
function M.write(path, values)
    local classes = {}
    for class, enabled in pairs(values) do if enabled then classes[#classes + 1] = class end end
    table.sort(classes)
    local file = assert(io.open(path .. ".tmp", "w"))
    for _, class in ipairs(classes) do
        local value = values[class]
        if type(value) == "table" then file:write(class, "\t", value.width, "\t", value.height, "\n")
        else file:write(class, "\n") end
    end
    file:close()
    assert(os.rename(path .. ".tmp", path))
end
function M.install(api, options)
    local previous, restoring, profiles = {}, {}, {}
    local function classOf(w)
        local class = w.initial_class
        if not class or class == "" then class = w.class end
        if type(class) ~= "string" or class == "" or class:find("[%c]") then return nil end
        return class
    end
    local function preferences()
        local profile = options.profile()
        if not profiles[profile] then profiles[profile] = options.load(profile) end
        return profiles[profile], profile
    end
    local function snapshot(w)
        if not w or not w.address then return end
        local _, profile = preferences()
        previous[w.address] = {floating = w.floating, profile = profile}
    end
    local controller = {}
    local focused = api.get_active_window and api.get_active_window() or nil
    function controller.rememberSize(w)
        if not w or not w.address or not w.floating or restoring[w.address] or not options.eligible(w) then return end
        local values, profile = preferences()
        local old, class = previous[w.address], classOf(w)
        if not old or old.profile ~= profile or not class or not values[class] then return end
        local size = w.size
        if not size or not size.x or not size.y then return end
        local width, height = math.floor(size.x), math.floor(size.y)
        if width < 64 or height < 64 or width > 32768 or height > 32768 then return end
        local value = values[class]
        if type(value) == "table" and value.width == width and value.height == height then return end
        values[class] = {width = width, height = height}
        options.save(profile, values)
    end
    function controller.open(w)
        snapshot(w)
        if not w or not w.address or not options.eligible(w) then return end
        local class, values = classOf(w), preferences()
        if class and values[class] then
            local value = values[class]
            restoring[w.address] = true
            if not w.floating then api.dispatch(api.dsp.window.float({action = "enable", window = "address:" .. w.address})) end
            if type(value) == "table" then
                api.dispatch(api.dsp.window.resize({x = value.width, y = value.height, window = "address:" .. w.address}))
            end
            restoring[w.address] = nil
            snapshot(w)
        end
    end
    function controller.changed(w)
        if not w or not w.address then return end
        local old = previous[w.address]
        snapshot(w)
        local values, profile = preferences()
        if not old or old.profile ~= profile or old.floating == w.floating or restoring[w.address] or not options.eligible(w) then return end
        local class = classOf(w)
        if not class then return end
        local enabled = w.floating and true or nil
        if values[class] == enabled then return end
        values[class] = enabled
        options.save(profile, values)
    end
    function controller.closed(w)
        controller.rememberSize(w)
        if w and w.address then
            previous[w.address] = nil; restoring[w.address] = nil
            if focused and focused.address == w.address then focused = nil end
        end
    end
    for _, w in ipairs(api.get_windows()) do snapshot(w) end
    api.on("window.update_rules", controller.changed)
    api.on("window.close", controller.closed)
    api.on("window.active", function(w)
        if focused and (not w or focused.address ~= w.address) then controller.rememberSize(focused) end
        focused = w
    end)
    api.on("hyprland.shutdown", function()
        for _, w in ipairs(api.get_windows()) do controller.rememberSize(w) end
    end)
    return controller
end
return M
