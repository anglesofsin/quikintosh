-- Quickintosh entrypoint: packaged together with modules/infinite-desktop.
-- Arch installs this at ~/.config/quickintosh/hypr/hyprland.lua and rewrites helper paths.
hl.env("XCURSOR_THEME", "MacTahoe-cursors")
hl.env("XCURSOR_SIZE", "31")
hl.env("HYPRCURSOR_THEME", "MacTahoe-cursors")
hl.env("HYPRCURSOR_SIZE", "31")
hl.env("QT_CURSOR_THEME", "MacTahoe-cursors")
hl.env("QT_CURSOR_SIZE", "31")

-- O modulo 'json' nao vem no ambiente Lua do Hyprland por padrao. Este
-- require precisa ser tolerante: um erro aqui aborta o config INTEIRO e o
-- Hyprland entra em emergency mode sem nenhum binding registrado.
-- O uso real (json.decode na leitura de posicoes) ja esta dentro de um pcall,
-- entao json == nil e seguro - apenas pula o reposicionamento.
local json_ok, json_mod = pcall(require, "json")
json = json_ok and json_mod or nil

hl.monitor({
    output   = "",
    mode     = "preferred",
    position = "auto",
    scale    = "auto",
})

hl.config({
    input = {
        kb_layout = "us",
        kb_variant = "intl",
        kb_options = "compose:menu",
        follow_mouse = 1,
        mouse_refocus = true, -- Restore pointer focus without requiring a boundary re-entry.
        touchpad = {
            natural_scroll = true,
            disable_while_typing = true,
            clickfinger_behavior = true,
            tap_to_click = true,
        },
        sensitivity = 0,
        accel_profile = "flat",
    },
    cursor = {
        inactive_timeout = 3,
    },
    general = {
        gaps_in = 5,
        gaps_out = 10,
        border_size = 0,

        layout = "dwindle",
        resize_on_border = true,
        extend_border_grab_area = 15,
        hover_icon_on_border = true,
    },
    scrolling = {
        wrap_focus = 1,
        wrap_swapcol = 1,
    },
    decoration = {
        rounding = 12,
        rounding_power = 2,
        active_opacity = 1.0,
        inactive_opacity = 0.9,

        -- Hyprland 0.56 trocou misc:dim_special (bool, off) por
        -- decoration:dim_special (float, default 0.2): abrir a special
        -- escurece o resto da tela, e o dim aparece na transmissao.
        dim_special = 0,
        fullscreen_opacity = 1.0,
        shadow = {
            enabled = true,
            -- A wide, soft, low-alpha shadow. A high alpha with a small range
            -- reads as a hard outline rather than a drop shadow.
            range = 40,
            render_power = 4,
            color = "rgba(00000080)",
        },
        -- Blur is global on this build: there is no positive per-window blur
        -- field (only `no_blur` to opt out). Windows with compositor opacity
        -- < 1 get blurred; the rules below keep kitty/browsers/Discord under it.
        blur = {
            enabled = true,
            size = 16,
            passes = 5,
            vibrancy = 0.1696,
            noise = 0.01,
            contrast = 0.9,
            brightness = 1.0,
            popups = true,
            popups_ignorealpha = 0.5,
        },
    },
    misc = {
        disable_hyprland_logo = true,
        disable_splash_rendering = true,
        mouse_move_enables_dpms = true,
        enable_swallow = true,
        swallow_regex = "^(kitty)$",
    },
    animations = {
        enabled = true,
    },
})

hl.curve("wind",   { type = "bezier", points = { {0.05, 0.9}, {0.1, 1.05} } })
hl.curve("winIn",  { type = "bezier", points = { {0.1, 1.1},  {0.1, 1.1}  } })
hl.curve("winOut", { type = "bezier", points = { {0.3, -0.3}, {0, 1}      } })
hl.curve("linear", { type = "bezier", points = { {0.0, 0.0},  {1.0, 1.0}  } })
hl.curve("emphasizedDecel", { type = "bezier", points = { {0.05, 0.7}, {0.1, 1} } })
hl.curve("emphasizedAccel", { type = "bezier", points = { {0.3, 0}, {0.8, 0.15} } })

hl.animation({ leaf = "windows",     enabled = true, speed = 6,  bezier = "wind",   style = "slide" })
hl.animation({ leaf = "windowsOut",  enabled = true, speed = 6,  bezier = "winOut", style = "slide" })
hl.animation({ leaf = "windowsMove", enabled = true, speed = 4,  bezier = "wind" })
hl.animation({ leaf = "fade",        enabled = true, speed = 4,  bezier = "wind" })
hl.animation({ leaf = "fadeDim",     enabled = true, speed = 6,  bezier = "winIn" })
hl.animation({ leaf = "workspaces",  enabled = true, speed = 5,  bezier = "wind" })
hl.animation({ leaf = "border",      enabled = true, speed = 10, bezier = "default" })
hl.animation({ leaf = "borderangle", enabled = true, speed = 8,  bezier = "default" })
hl.animation({
    leaf = "specialWorkspaceIn",
    enabled = true,
    speed = 2.8,
    bezier = "emphasizedDecel",
    style = "slidevert"
})
hl.animation({
    leaf = "specialWorkspaceOut",
    enabled = true,
    speed = 1.2,
    bezier = "emphasizedAccel",
    style = "slidevert"
})

local hyprCanvasPlugin = "@HYPR_CANVAS_PLUGIN@"
local hyprCanvasLoad = hl.plugin and hl.plugin.load
local hyprCanvasOk, hyprCanvasErr = pcall(function()
    if type(hyprCanvasLoad) ~= "function" then
        error("hl.plugin.load is unavailable")
    end
    hyprCanvasLoad(hyprCanvasPlugin)
end)
if not hyprCanvasOk then
    local log = io.open("/tmp/hypr-canvas-load-error.log", "a")
    if log then
        log:write(os.date("%Y-%m-%d %H:%M:%S"), " ", tostring(hyprCanvasErr), "\n")
        log:close()
    end
end

local m = "SUPER"
local rice = "/run/current-system/sw/bin/rice-shell"
local playerctl = "/run/current-system/sw/bin/playerctl"
local function riceAction(name)
    return hl.dsp.exec_cmd(rice .. " action " .. name)
end
local shellActions = {}
local capabilities = io.popen(rice .. " capabilities --lua")
if capabilities then
    local chunk = load(capabilities:read("*a"), "shell capabilities", "t", {})
    capabilities:close()
    if chunk then local ok, result = pcall(chunk); if ok then shellActions = result end end
end
local shortcutOverrides = {}
if shellActions["switcher-next"] then
    hl.config({misc={focus_on_activate=true}})
    local config = os.getenv("XDG_CONFIG_HOME") or (os.getenv("HOME") .. "/.config")
    local shortcuts = io.open(config .. "/lickintosh/core/shortcuts.tsv", "r")
    if shortcuts then
        for line in shortcuts:lines() do
            local label, binding = line:match("^([^%c]+)	([%w_+ :%-]+)$")
            if label then shortcutOverrides[label] = binding end
        end
        shortcuts:close()
    end
end
local function configurableBind(key, dispatcher, options)
    hl.bind(shortcutOverrides[options.description] or key, dispatcher, options)
end
local function shellBind(key, action, options)
    if shellActions[action] then configurableBind(key, riceAction(action), options) end
end

-- The shared binding value keeps press/release paired when customized.
if shellActions["switcher-next"] then
local ringKey = shortcutOverrides["Action Ring"] or (m .. " + ALT + R")
hl.bind(ringKey, hl.dsp.exec_cmd("quickintosh ipc call actionRing show"), {description="Action Ring"})
hl.bind(ringKey, hl.dsp.exec_cmd("quickintosh ipc call actionRing release"), {description="Action Ring release",release=true})
end

-- 1. Window Management
hl.bind(m .. " + Q", hl.dsp.window.close(), { description = "Close window" })
hl.bind(m .. " + F", hl.dsp.window.fullscreen(), { description = "Toggle fullscreen" })
-- Keep the layout node in place. Internal maximize fills the work area while
-- client mode stays normal, preserving rounded client chrome and titlebars.
hl.workspace_rule({workspace="f[1]",gaps_out=0,float_gaps=0})
local function toggleDecoratedZoom()
    local w = hl.get_active_window()
    if not w or not w.address then return end
    local selector = "address:" .. w.address
    local maximized = w.fullscreen == 1
    hl.dispatch(hl.dsp.window.fullscreen_state({internal=maximized and 0 or 1,client=0,action="set",layout_aware=false,window=selector}))
    -- fullscreen_state decouples modes and turns sync off. Restore sync only
    -- for subsequent app requests (YouTube F), without changing this geometry.
    hl.dispatch(hl.dsp.window.set_prop({prop="sync_fullscreen",value="1",window=selector}))
    hl.dispatch(hl.dsp.window.tag({tag=(maximized and "-" or "+").."quickintosh-maximized",window=selector}))
end
local function restoreMaximizedForNewTile(w)
    if not w or w.floating or not w.workspace then return end
    for _,other in ipairs(hl.get_workspace_windows(w.workspace)) do
        if other.address ~= w.address and other.fullscreen == 1 then
            hl.dispatch(hl.dsp.window.fullscreen_state({internal=0,client=0,action="set",layout_aware=false,window="address:"..other.address}))
            hl.dispatch(hl.dsp.window.set_prop({prop="sync_fullscreen",value="1",window="address:"..other.address}))
            hl.dispatch(hl.dsp.window.tag({tag="-quickintosh-maximized",window="address:"..other.address}))
        end
    end
end
configurableBind("ALT + F", toggleDecoratedZoom, {description="Toggle maximize"})
hl.bind(m .. " + T", hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-focus-toggle.sh"), { description = "Toggle float / canvas focus mode" })
hl.bind(m .. " + Z", hl.dsp.window.pin({ action = "toggle" }), { description = "Toggle pin" })
hl.bind(m .. " + SHIFT + left",  hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-move-window.sh left"), { description = "Move window left" })
hl.bind(m .. " + SHIFT + right", hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-move-window.sh right"), { description = "Move window right" })
hl.bind(m .. " + SHIFT + up",    hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-move-window.sh up"), { description = "Move window up" })
hl.bind(m .. " + SHIFT + down",  hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-move-window.sh down"), { description = "Move window down" })
hl.bind(m .. " + mouse:272", hl.dsp.window.drag(), { mouse = true, description = "Move window (mouse)" })
hl.bind(m .. " + mouse:273", hl.dsp.window.resize(), { mouse = true, description = "Resize window (mouse)" })

-- 2. Workspaces
for i = 1, 9 do
    hl.bind(m .. " + " .. i, hl.dsp.focus({ workspace = i }), { description = "Workspace " .. i })
    hl.bind(m .. " + SHIFT + " .. i, hl.dsp.window.move({ workspace = i }), { description = "Move window to workspace " .. i })
end
hl.bind(m .. " + TAB",          hl.dsp.focus({ workspace = "e+1" }), { description = "Next workspace" })
hl.bind(m .. " + SHIFT + TAB",  hl.dsp.focus({ workspace = "e-1" }), { description = "Previous workspace" })

-- 3. Launching
hl.bind(m .. " + Return", hl.dsp.exec_cmd("kitty"), { description = "Kitty terminal" })
hl.bind(m .. " + H", hl.dsp.exec_cmd("zen"), { description = "Zen browser" })
hl.bind(m .. " + E", hl.dsp.exec_cmd("rice-file-manager"), { description = "Rice file manager" })

-- 4. Active desktop shell (capabilities are reloaded on each explicit switch)
if shellActions["switcher-next"] then
    configurableBind(m .. " + P", hl.dsp.global("lickintosh:spotlight"), { description = "Spotlight" })
    configurableBind("ALT + P", hl.dsp.global("lickintosh:launchpad"), { description = "Launchpad" })
elseif shellActions["launchpad"] then
    shellBind(m .. " + P", "launchpad", { description = "Launchpad" })
    shellBind("ALT + SPACE", "spotlight", { description = "Spotlight" })
else
    shellBind(m .. " + P", "launcher", { description = "Launcher" })
end
shellBind(m .. " + period", "emoji", { description = "Emoji picker" })
shellBind(m .. " + SHIFT + Return", "command-runner", { description = "Command runner" })
if shellActions["screenshot-fullscreen"] then
    configurableBind(m .. " + V", hl.dsp.global("lickintosh:clipboard"), { description = "Clipboard history" })
else
    shellBind(m .. " + V", "clipboard", { locked = true, description = "Clipboard history" })
end
shellBind(m .. " + C", "control-center", { description = "Control center" })
shellBind(m .. " + B", "bar-toggle", { description = "Toggle bar" })
shellBind(m .. " + SHIFT + B", "dock-toggle", { description = "Toggle dock" })
shellBind(m .. " + I", "settings", { description = "Open shell settings" })
shellBind(m .. " + Escape", "session", { description = "Session menu" })
shellBind(m .. " + L", "lock", { description = "Lock screen" })
if not shellActions["screenshot-fullscreen"] then
    shellBind(m .. " + slash", "keybinds", { description = "Show keys" })
end
shellBind(m .. " + bracketright", "keybinds", { description = "Show keys" })
hl.bind(m .. " + backslash", hl.dsp.exec_cmd(rice .. " toggle"), { description = "Toggle active shell" })
-- The transparency toggle, and the only per-window opacity control that exists
-- here. It runs INSIDE the compositor, on the keypress: it used to be an
-- `exec_cmd` into a shell script that called `hyprctl eval` back into this same
-- Lua, which put a bash process, a hyprctl process and a second Lua entry point
-- between the key and the window.
--
-- There used to be gradual alpha/blur controls here too (Super+SHIFT+[ ], 0 and
-- Super+ALT+[ ], 0). They were removed: this Hyprland build has no gradual
-- per-window blur prop at all (`blur`, `blur_size`, `blur_popacity` are all
-- "Invalid prop name"), so half the shortcuts could not do what they said and
-- the whole thing read as broken. The toggle is the control that works.
--
-- No toast: the window itself is the feedback, and a notification on every
-- toggle is noise on a key you press often. The toggle result still goes to
-- the log, which is where it is useful.
local function opacityToggle()
    pcall(INFINITE_OPACITY.toggle)
end

hl.bind(m .. " + SHIFT + backslash", opacityToggle, { description = "Toggle active window transparency" })
hl.bind(m .. " + SHIFT + F5", hl.dsp.exec_cmd(rice .. " restart"), { description = "Restart active shell" })

shellBind(m .. " + ALT + I", "ai", { description = "Shell AI assistant" })
shellBind(m .. " + ALT + G", "game-mode", { description = "Toggle shell game mode" })
shellBind(m .. " + ALT + K", "keep-awake", { description = "Toggle keep awake" })
shellBind(m .. " + ALT + P", "profiles", { description = "Shell profiles" })
shellBind(m .. " + ALT + U", "notch-active", { description = "Activate notch item" })
shellBind(m .. " + ALT + N", "notch-info", { description = "Notch information" })

-- Lickintosh's switcher consumes ALT release itself. Use the native protocol
-- to preserve press/release events (do not wrap these in an exec command).
if shellActions["switcher-next"] then
    hl.bind("ALT + Tab", hl.dsp.global("quickshell:switcher-next"), { description = "Next application" })
    hl.bind("ALT + SHIFT + Tab", hl.dsp.global("quickshell:switcher-prev"), { description = "Previous application" })
end

-- 5. Desktop & Display
hl.bind(m .. " + SPACE", hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-toggle.sh"), { description = "Toggle infinite desktop" })
shellBind(m .. " + SHIFT + W", "wallpaper-picker", { description = "Wallpaper panel" })
hl.bind(m .. " + ALT + W", hl.dsp.window.move({ workspace = "special:public", follow = false }), { description = "Move window to stream scratchpad" })
shellBind(m .. " + SHIFT + D", "theme-mode", { description = "Toggle dark mode" })
shellBind(m .. " + SHIFT + N", "nightlight", { description = "Toggle night light" })
shellBind(m .. " + SHIFT + M", "dpms-off", { description = "Turn off monitors" })
shellBind(m .. " + SHIFT + E", "desktop-widgets", { description = "Edit desktop widgets" })

-- 6. Screenshots & Recording
shellBind(m .. " + SHIFT + S", "screenshot-region", { description = "Screenshot menu (freeze, select: Copy/Save/Editor/OCR/Lens)" })
shellBind(m .. " + O", "screen-toolkit", { description = "Capture / Quickshot" })
shellBind(m .. " + SHIFT + O", "ocr", { description = "OCR (region selector)" })
shellBind(m .. " + SHIFT + P", "annotate-fullscreen", { description = "Fullscreen markup/annotation" })

-- PrintScreen: instant fullscreen screenshot to ~/Pictures + clipboard
if shellActions["screenshot-fullscreen"] then
    shellBind("Print", "screenshot-fullscreen", { description = "Capture display under pointer (save + clipboard)" })
else
    hl.bind("Print", hl.dsp.exec_cmd("/home/pg/scripts/screenshot-fullscreen.sh"), { description = "Fullscreen screenshot (instant, to Pictures + clipboard)" })
end

-- Replay buffer
hl.bind("CTRL + SUPER + R", hl.dsp.exec_cmd("replay save"), { description = "Save replay buffer (last 60s)" })



-- 7. Notifications & Audio
shellBind(m .. " + SHIFT + U", "dnd", { description = "Toggle do not disturb" })
shellBind("XF86AudioRaiseVolume", "volume-up",    { repeating = true, description = "Volume up" })
shellBind("XF86AudioLowerVolume", "volume-down",    { repeating = true, description = "Volume down" })
shellBind("XF86AudioMute", "volume-mute",  { locked = true, description = "Mute audio" })
hl.bind("XF86AudioPlay",        hl.dsp.exec_cmd(playerctl .. " play-pause"), { locked = true, description = "Play / pause media" })
hl.bind("XF86AudioPause",       hl.dsp.exec_cmd(playerctl .. " play-pause"), { locked = true, description = "Play / pause media" })
hl.bind("XF86AudioNext",        hl.dsp.exec_cmd(playerctl .. " next"),       { locked = true, description = "Next media track" })
hl.bind("XF86AudioPrev",        hl.dsp.exec_cmd(playerctl .. " previous"),   { locked = true, description = "Previous media track" })
shellBind("XF86MonBrightnessUp", "brightness-up", { repeating = true, description = "Brightness up" })
shellBind("XF86MonBrightnessDown", "brightness-down", { repeating = true, description = "Brightness down" })

hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), { locked = true, description = "Mute microphone" })

-- 8. Zoom
hl.bind(m .. " + equal", hl.dsp.exec_cmd("/home/pg/scripts/zoom.sh in"), { description = "Zoom in" })
hl.bind(m .. " + minus", hl.dsp.exec_cmd("/home/pg/scripts/zoom.sh out"), { description = "Zoom out" })
hl.bind(m .. " + 0", hl.dsp.exec_cmd("/home/pg/scripts/zoom.sh reset"), { description = "Reset cursor zoom" })
hl.bind(m .. " + SHIFT + 0", hl.dsp.exec_cmd("/home/pg/scripts/canvas-zoom-reset.sh"), { description = "Reset canvas zoom" })
-- Canvas zoom is handled directly by the hypr-canvas plugin:
-- SUPER + scroll zooms the rendered workspace; SUPER + middle click resets it.




-- 9. Infinite Desktop Navigation
hl.bind(m .. " + left",   hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-nav-left.sh"), { description = "Focus window left / pan by mode" })
hl.bind(m .. " + right",  hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-nav-right.sh"), { description = "Focus window right / pan by mode" })
hl.bind(m .. " + up",     hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-nav-up.sh"), { description = "Focus window up / pan by mode" })
hl.bind(m .. " + down",   hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-nav-down.sh"), { description = "Focus window down / pan by mode" })
hl.bind(m .. " + ALT + left",   hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-pan.sh left"), { description = "Canvas pan left" })
hl.bind(m .. " + ALT + right",  hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-pan.sh right"), { description = "Canvas pan right" })
hl.bind(m .. " + ALT + up",     hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-pan.sh up"), { description = "Canvas pan up" })
hl.bind(m .. " + ALT + down",   hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-pan.sh down"), { description = "Canvas pan down" })
hl.bind(m .. " + R", hl.dsp.exec_cmd("touch /tmp/infinite-desktop-center-active"), { description = "Center active window" })
hl.bind(m .. " + SHIFT + mouse:272", hl.dsp.exec_cmd("touch /tmp/infinite-desktop-pan-mode"), { mouse = true, description = "Pan mode (mouse drag)" })

-- 10. Scrolling Layout (mode-specific binds, safe in any mode)
hl.bind(m .. " + SHIFT + equal", hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-colresize.sh +conf"), { description = "Scrolling: widen column" })
hl.bind(m .. " + SHIFT + minus", hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-colresize.sh -conf"), { description = "Scrolling: narrow column" })

-- 11. Utilities
hl.bind(m .. " + Y", hl.dsp.exec_cmd("/home/pg/scripts/toggle-borders.sh"), { description = "Toggle window borders" })
hl.bind(m .. " + S", hl.dsp.exec_cmd("/home/pg/scripts/toggle-special-scratchpad.sh"), { description = "Toggle scratchpad (special workspace)" })
hl.bind(m .. " + W", hl.dsp.exec_cmd("/home/pg/scripts/toggle-special-public.sh"), { description = "Toggle stream scratchpad (top slide)" })
hl.bind(m .. " + D", hl.dsp.exec_cmd("/home/pg/scripts/toggle-special-right.sh"), { description = "Toggle right scratchpad (slide from right)" })
hl.bind(m .. " + A", hl.dsp.exec_cmd("/home/pg/scripts/toggle-special-left.sh"), { description = "Toggle left scratchpad (slide from left)" })
hl.bind(m .. " + ALT + D", hl.dsp.window.move({ workspace = "special:right", follow = false }), { description = "Move window to right scratchpad" })
hl.bind(m .. " + ALT + A", hl.dsp.window.move({ workspace = "special:left", follow = false }), { description = "Move window to left scratchpad" })
hl.bind(m .. " + CTRL + H", hl.dsp.exec_cmd("/home/pg/scripts/toggle-stream-hide.sh hide"), { description = "Stream: hide active special workspace" })
hl.bind(m .. " + CTRL + S", hl.dsp.exec_cmd("/home/pg/scripts/toggle-stream-hide.sh show"), { description = "Stream: show active special workspace" })
shellBind(m .. " + N", "notifications", { description = "Notification center" })
hl.bind(m .. " + CTRL + left", hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-scroll-sidemove.sh left"), { description = "Scrolling: move window to own column on the left" })
hl.bind(m .. " + CTRL + right", hl.dsp.exec_cmd("/home/pg/scripts/infinite-desktop-scroll-sidemove.sh right"), { description = "Scrolling: move window to own column on the right" })
hl.bind(m .. " + ALT + S", hl.dsp.window.move({ workspace = "special:special", follow = false }), { description = "Move window to scratchpad" })

hl.bind(m .. " + U", hl.dsp.exec_cmd("hyprpicker -a"), { description = "Color picker" })

hl.window_rule({
    name = "float-pavucontrol",
    match = { class = "pavucontrol" },
    float = true,
})

hl.window_rule({
    name = "float-blueman",
    match = { class = "blueman-manager" },
    float = true,
})

hl.window_rule({
    name = "float-calculator",
    match = { class = "org.gnome.Calculator" },
    float = true,
})

hl.window_rule({name="quickintosh-finder-portal-dialog",match={class="^org[.]gnome[.]Nautilus$",title="^Finder — .*"},float=true,center=true,focus_on_activate=true,opacity="1.0 1.0",tag="+hyprglass_enabled"})
hl.window_rule({name="quickintosh-finder-file-chooser",match={class="^org[.]quickintosh[.]Finder[.]FileChooser$"},float=true,center=true,focus_on_activate=true,opacity="1.0 1.0",tag="+hyprglass_enabled"})

hl.window_rule({
    name = "float-xdg-portal",
    match = { class = "xdg-desktop-portal-gtk" },
    float = true,
})

hl.window_rule({
    name = "float-pip",
    match = { title = "Picture-in-Picture" },
    float = true,
})

-- Catch-all: every window is transparent and blurred unless a later rule says
-- otherwise. Rule order matters -- the engine walks its rule list front to back
-- and a later match overwrites an earlier one -- so this must stay ABOVE the
-- per-app rules below, which exist only to tune a few known classes.
hl.window_rule({
    name = "opacity-default",
    match = { class = ".*" },
    opacity = "0.90 0.85",
})

hl.window_rule({
    name = "opacity-kitty",
    match = { class = "kitty" },
    -- Kept just under 1 only because the compositor blur pass is skipped for
    -- fully-opaque windows; the visible transparency comes from kitty's own
    -- background_opacity, so these two multiply rather than add.
    opacity = "0.99 0.98",
})

-- `class` is matched as a regex against the WM_CLASS Hyprland reports, which is
-- NOT always the name of the binary. Measured on this machine:
--   zen       -> "zen"                       (Zen, ~/.nix-profile/.../zen.desktop)
--   helium    -> "helium"                    (Helium, same place)
--   chromium  -> "org.chromium.Chromium"     (flatpak; NOT "chromium")
--   discord   -> "discord"                   (all three: stable, PTB, Canary)
-- These apps have no background_opacity of their own, so the compositor value is
-- the whole thing.
--
-- The `.*(...).*` wrapper is deliberate: whether Hyprland anchors class matching
-- is not something I could reproduce from the live compositor, and the two
-- readings disagree on whether `(zen|helium|chromium)` matches
-- "org.chromium.Chromium". This pattern matches the same set of classes under
-- BOTH readings, so it does not depend on the answer.
hl.window_rule({
    name = "opacity-browsers",
    match = { class = ".*(zen|helium|chromium).*" },
    opacity = "0.77 0.75",
})

hl.window_rule({
    name = "opacity-discord",
    match = { class = ".*([Dd]iscord).*" },
    opacity = "0.77 0.75",
})

hl.window_rule({
    name = "opacity-nautilus",
    match = { class = "org.gnome.Nautilus" },
    -- Finder surfaces provide their own alpha; do not fade every file/icon.
    opacity = shellActions["switcher-next"] and "1.0 1.0" or "0.97 0.93",
})

-- Preview pixels stay opaque; HyprGlass draws behind the translucent chrome.
if shellActions["switcher-next"] then
    hl.window_rule({name="quickintosh-floating-tray",match={title="^Quickintosh File Tray$"},float=true,center=true,opacity="1.0 1.0",tag="+hyprglass_enabled"})
    hl.window_rule({name="quickintosh-floating-player",match={title="^Quickintosh Floating Player$"},float=true,center=true,opacity="1.0 1.0",tag="+hyprglass_enabled"})
    hl.window_rule({name="quickintosh-share-picker",match={title="^Quickintosh Screen Sharing$"},float=true,center=true,opacity="1.0 1.0",tag="+hyprglass_enabled"})
    hl.window_rule({name="lickintosh-settings",match={class="^org[.]lickintosh[.]Settings$"},float=true,opacity="1.0 1.0",tag="+hyprglass_enabled"})
    hl.window_rule({name="lickintosh-quick-look",match={title="^(Lickintosh|Quickintosh) Quick Look.*"},float=true,center=true,stay_focused=true,focus_on_activate=true,no_anim=false,animation="popin 88%",opacity="1.0 1.0",tag="+hyprglass_enabled"})
end

hl.layer_rule({
    name = "blur-noctalia",
    match = { namespace = "^noctalia-(bar-.+|notification|dock.*|panel|attached-panel|osd|window-switcher)$" },
    blur = true,
    ignore_alpha = 0.5,
})

hl.layer_rule({
    name = "blur-noctalia-bg",
    match = { namespace = "^noctalia-background-.*$" },
    blur = true,
    ignore_alpha = 0.5,
})

hl.layer_rule({
    name = "no-anim-selector",
    match = { namespace = "noctalia-shell:regionSelector" },
    no_anim = true,
})

hl.layer_rule({
    name = "blur-caelestia",
    match = { namespace = "^caelestia-.*$" },
    blur = true,
    ignore_alpha = 0.5,
})


hl.layer_rule({ name = "eqsh-glass", match = { namespace = "^eqsh(:.*)?$" }, blur = true, blur_popups = true, ignore_alpha = 0.2 })
hl.layer_rule({ name = "eqsh-noanim", match = { namespace = "^eqsh(:.*)?$" }, no_anim = true })

local workspaceStateDir = os.getenv("HOME") .. "/.local/state/infinite-desktop"
os.execute('mkdir -p "' .. workspaceStateDir .. '"')

-- ---------------------------------------------------------------------------
-- Per-class opacity choice, persisted (Super+Shift+\)
-- ---------------------------------------------------------------------------
-- `opaque` is the only per-window lever that actually does anything in this
-- Hyprland build: setting it to 1 forces alpha to 1.0 and also disables the
-- window's blur, so it is exactly the "opaque" half of the toggle. The `opacity`
-- prop is accepted but inert, and `alpha` is not a valid prop name at all.
--
-- The choice is stored per CLASS, not per address: an address dies with the
-- window and Hyprland hands the same value back to an unrelated window later,
-- so keying by address cannot survive a close, let alone a reboot. A class is
-- the coarsest key that still identifies "this app" across reboots, and
-- ~/.local/state is persistent.
local opaqueClassesFile = workspaceStateDir .. "/opaque-classes"

local function loadOpaqueClasses()
    local set = {}
    local f = io.open(opaqueClassesFile, "r")
    if not f then return set end
    for line in f:lines() do
        local class = line:gsub("%s+", "")
        if class ~= "" then set[class] = true end
    end
    f:close()
    return set
end

local function saveOpaqueClasses(set)
    -- Sorted so the file is stable and diffable; unordered table pairs would
    -- shuffle the lines on every press.
    local classes = {}
    for class in pairs(set) do classes[#classes + 1] = class end
    table.sort(classes)
    local f = io.open(opaqueClassesFile, "w")
    if not f then return end
    for _, class in ipairs(classes) do
        f:write(class, "\n")
    end
    f:close()
end

local opaqueClasses = loadOpaqueClasses()

-- Dispatched on every window of the class, not just the focused one: the user
-- may have several windows of the same app open, and the choice is about the
-- app. A `set_prop` also outranks any window rule (it is written at a higher
-- priority), so this survives a mode change re-applying the rules.
--
-- A transparent window needs nothing written to it: dropping `opaque` hands it
-- back to the catch-all `opacity = "0.90 0.85"` window rule, which is exactly
-- what every other window in the session gets.
local function applyPersistedOpaque(class)
    if type(class) ~= "string" or class == "" then return end
    local isOpaque = opaqueClasses[class] and 1 or 0
    for _, w in ipairs(hl.get_windows()) do
        if w and w.address and w.class == class then
            hl.dispatch(hl.dsp.window.set_prop({
                prop = "opaque",
                value = isOpaque,
                window = "address:" .. w.address,
            }))
        end
    end
end

-- Returns the class of the active window, or errors. Every entry point below
-- starts here: these shortcuts only ever mean something about the window the
-- user is actually looking at.
local function activeClass()
    local w = hl.get_active_window()
    local class = w and w.class
    if type(class) ~= "string" or class == "" or not w.address then
        error("INFINITE_OPACITY: no active window", 0)
    end
    return class
end

-- The state file is the single source of truth, re-read on every press.
--
-- It used to be read once at config load and kept in a Lua table, so the table
-- could describe a state that no longer existed on disk after an outside edit.
-- It is one line per opaque app; re-reading costs nothing.
local function refreshState()
    opaqueClasses = loadOpaqueClasses()
end

INFINITE_OPACITY = {
    -- Called from the in-process keybinds. Globals survive across `hyprctl
    -- eval`, which is what lets this live in the config instead of a script.
    toggle = function()
        refreshState()
        local class = activeClass()
        opaqueClasses[class] = not opaqueClasses[class] or nil
        saveOpaqueClasses(opaqueClasses)
        applyPersistedOpaque(class)
        error(string.format("INFINITE_OPACITY: %s -> %s", class,
            opaqueClasses[class] and "opaque" or "transparent"), 0)
    end,
}

local function readModeFile(path)
    local f = io.open(path, "r")
    if not f then return nil end
    local mode = f:read("*all"):gsub("%s+", "")
    f:close()
    if mode == "tiled" or mode == "canvas" or mode == "scrolling" then return mode end
    return nil
end

local function workspaceStateKey(ws)
    if ws.special then return ws.name end
    return tostring(ws.id)
end

local function readWorkspaceMode(ws)
    if not ws or (not ws.id and not ws.special) then return "tiled" end

    local path = workspaceStateDir .. "/state-" .. workspaceStateKey(ws)
    local mode = readModeFile(path)
    if mode then return mode end

    -- Migrate the old negative-ID files while the old ID still maps to this
    -- special workspace. Names are stable across Hyprland restarts; IDs are not.
    if ws.special and ws.id then
        mode = readModeFile(workspaceStateDir .. "/state-" .. tostring(ws.id))
        if mode then
            local out = io.open(path, "w")
            if out then
                out:write(mode .. "\n")
                out:close()
            end
            return mode
        end
    end

    return "tiled"
end

local function workspaceSelector(ws)
    if ws.special then return ws.name end
    return tostring(ws.id)
end

local function setWorkspaceModeRule(ws)
    if not ws or (not ws.id and not ws.special) then return false end
    local mode = readWorkspaceMode(ws)
    local layout = mode == "scrolling" and "scrolling" or "dwindle"
    local rule = { workspace = workspaceSelector(ws), layout = layout }
    if layout == "scrolling" then rule.layout_opts = { direction = "right" } end
    hl.workspace_rule(rule)
    return ws.tiled_layout ~= layout
end

local canvasManagedTag = "infinite-desktop-canvas"

local function hasWindowTag(w, tag)
    if not w or not w.tags then return false end
    for _, current in ipairs(w.tags) do
        if current == tag then return true end
    end
    return false
end

local function applyWindowMode(w, ws)
    local addr = w and w.address
    if not addr or not ws or (not ws.id and not ws.special) then return end

    if w.class == "org.quickintosh.Finder.FileChooser" or (w.class == "org.gnome.Nautilus" and (w.title or ""):match("^Finder — ")) then return end
    local mode = readWorkspaceMode(ws)
    if mode == "canvas" then
        if w.floating or w.fullscreen ~= 0 then return end
        hl.dispatch(hl.dsp.window.tag({tag = "+" .. canvasManagedTag, window = "address:" .. addr}))
        hl.dispatch(hl.dsp.window.float({action = "enable", window = "address:" .. addr}))
        hl.dispatch(hl.dsp.window.set_prop({prop = "border_size", value = 0, window = "address:" .. addr}))
        os.execute("mkdir -p /tmp/infinite-desktop-new")
        local marker = io.open("/tmp/infinite-desktop-new/" .. addr, "w")
        if marker then marker:close() end

        local safe_key = ws.special and ws.name or tostring(ws.id)
        safe_key = safe_key:gsub("/", "_"):gsub(":", "_")
        local pos_file = os.getenv("HOME") .. "/.local/state/infinite-desktop/canvas-positions/canvas-positions-" .. safe_key .. ".json"
        local pos_f = io.open(pos_file, "r")
        if pos_f then
            local data = pos_f:read("*all")
            pos_f:close()
            local ok, positions = pcall(function() return json.decode(data) end)
            if ok and positions then
                for _, pos in pairs(positions) do
                    if pos.at and pos.size then
                        hl.dispatch(hl.dsp.window.move({x = pos.at[1], y = pos.at[2], window = "address:" .. addr}))
                        hl.dispatch(hl.dsp.window.resize({x = pos.size[1], y = pos.size[2], window = "address:" .. addr}))
                        break
                    end
                end
            end
        end
    else
        local managed = hasWindowTag(w, canvasManagedTag)
        if managed then
            hl.dispatch(hl.dsp.window.float({action = "disable", window = "address:" .. addr}))
            hl.dispatch(hl.dsp.window.tag({tag = "-" .. canvasManagedTag, window = "address:" .. addr}))
        end
        if mode == "scrolling" and (managed or not w.floating) then
            hl.dispatch(hl.dsp.window.set_prop({prop = "border_size", value = 0, window = "address:" .. addr}))
        end
    end
end

local function hiddenSpecialWorkspaces()
    local hidden = {}
    local f = io.open(workspaceStateDir .. "/stream-hidden", "r")
    if not f then return hidden end
    for name in f:lines() do
        if name:sub(1, 8) == "special:" then hidden[name] = true end
    end
    f:close()
    return hidden
end

local function syncWindowStreamVisibility(w, ws, hidden)
    local addr = w and w.address
    if not addr then return end
    ws = ws or w.workspace
    local hide = ws and ws.special and hidden[ws.name] or false
    hl.dispatch(hl.dsp.window.set_prop({
        prop = "no_screen_share",
        value = hide and "1" or "0",
        window = "address:" .. addr,
    }))
end

local function restoreWorkspaceMode(ws)
    if setWorkspaceModeRule(ws) then
        -- Re-evaluate the algorithm for an already-created workspace.
        hl.config({ scrolling = { direction = "right" } })
    end
end

-- Persistence is isolated by shell. Canvas/scratchpad transitions are layout
-- policy, not the user's preference for an application's ordinary windows.
local rememberFloating = dofile(os.getenv("HOME") .. "/.config/hypr/remember-floating.lua")
local floatingMemory = rememberFloating.install(hl, {
    profile = function()
        local f = io.open(os.getenv("HOME") .. "/.local/state/nixos-rice/active-shell", "r")
        local shell = f and f:read("*line") or "default"
        if f then f:close() end
        return (shell or "default"):gsub("[^%w_-]", "_")
    end,
    load = function(profile) return rememberFloating.read(workspaceStateDir .. "/floating-apps-" .. profile) end,
    save = function(profile, values) rememberFloating.write(workspaceStateDir .. "/floating-apps-" .. profile, values) end,
    -- Runtime inheritance also covers windows spawned from scratchpads; it
    -- never writes a special-workspace default into persistent preferences.
    inheritEligible = function(w)
        local ws = w.workspace
        return ws and readWorkspaceMode(ws) ~= "canvas" and not hasWindowTag(w, canvasManagedTag)
            and w.class ~= "org.quickintosh.Finder.FileChooser"
            and not (w.class == "org.gnome.Nautilus" and (w.title or ""):match("^Finder — "))
    end,
    eligible = function(w)
        local ws = w.workspace
        return w.class ~= "org.quickintosh.Finder.FileChooser" and not (w.class == "org.gnome.Nautilus" and (w.title or ""):match("^Finder — ")) and ws and not ws.special and readWorkspaceMode(ws) ~= "canvas"
            and not hasWindowTag(w, canvasManagedTag) and w.fullscreen == 0
    end,
})

hl.on("window.open", function(w)
    local ws = w and w.workspace
    if not ws then return end
    applyWindowMode(w, ws)
    applyPersistedOpaque(w.class)
    floatingMemory.open(w)
    restoreMaximizedForNewTile(w)
    syncWindowStreamVisibility(w, ws, hiddenSpecialWorkspaces())
end)

hl.on("window.move_to_workspace", function(w, ws)
    -- no_screen_share is a window property. Recompute it from the destination
    -- so a window leaving a hidden special workspace becomes visible at once.
    applyWindowMode(w, ws)
    syncWindowStreamVisibility(w, ws, hiddenSpecialWorkspaces())
end)

hl.on("workspace.created", function(ws)
    restoreWorkspaceMode(ws)
end)

hl.on("workspace.active", function(ws)
    restoreWorkspaceMode(ws)
end)

hl.on("workspace.special_active", function(ws, _monitor)
    if ws then restoreWorkspaceMode(ws) end
end)

-- Restore all persisted rules on load/reload. Explicit dwindle rules also
-- clear a stale scrolling rule when a workspace was last left tiled/canvas.
local refreshLayouts = false
for id = 1, 20 do
    local path = workspaceStateDir .. "/state-" .. tostring(id)
    local mode = readModeFile(path)
    if mode then
        local layout = mode == "scrolling" and "scrolling" or "dwindle"
        local rule = { workspace = tostring(id), layout = layout }
        if layout == "scrolling" then rule.layout_opts = { direction = "right" } end
        hl.workspace_rule(rule)
    end
end

local hidden = hiddenSpecialWorkspaces()
for _, ws in ipairs(hl.get_workspaces()) do
    if setWorkspaceModeRule(ws) then refreshLayouts = true end
    for _, w in ipairs(hl.get_workspace_windows(ws)) do
        applyWindowMode(w, ws)
        applyPersistedOpaque(w.class)
        syncWindowStreamVisibility(w, ws, hidden)
    end
end
if refreshLayouts then hl.config({ scrolling = { direction = "right" } }) end

local function activeRiceShell()
    local f = io.open("/home/pg/.local/state/nixos-rice/active-shell", "r")
    if not f then return "noctalia" end
    local shell = f:read("*line") or "noctalia"
    f:close()
    return shell
end

local activeShell = activeRiceShell()
if activeShell == "noctalia" or activeShell == "noctalia-legacy" then
    pcall(dofile, "/home/pg/.config/hypr/noctalia/noctalia-colors.lua")
end

hl.on("hyprland.start", function()
    hl.exec_cmd("hyprctl setcursor MacTahoe-cursors 31")
    hl.exec_cmd("/run/current-system/sw/bin/rice-shell start")
    hl.exec_cmd("touch /tmp/borders-off-global")
    hl.exec_cmd("kdeconnect-indicator")
    hl.exec_cmd("systemctl --user start nixos-fake-graphical-session.target")
end)

-- Noctalia colour templates must not override Caelestia while it is active.
if activeShell == "noctalia" or activeShell == "noctalia-legacy" then
    require("noctalia").apply_theme()
end

-- These panels already animate in QML before unmapping. Avoid a second
-- compositor animation and a redundant full-screen exit snapshot.
hl.layer_rule({
    name = "quickintosh-panel-owned-animation",
    match = { namespace = "^quickshell:(applemenu|globalmenu|statusmenu|cc|notifcenter|spotlight)$" },
    no_anim = true,
})

-- Capture/pinned-image overlays manage their own animation and image geometry.
hl.layer_rule({
    name = "no-anim-lickintosh-capture",
    match = { namespace = "^lickintosh:(capture|capture-flash|pinned-capture)$" },
    no_anim = true,
})

-- Lickintosh keeps its window geometry styling separate from other rices.
do
    local file = io.open(os.getenv("HOME") .. "/.local/state/nixos-rice/active-shell", "r")
    local shell = file and file:read("*all"):match("^%s*(.-)%s*$") or ""
    if file then file:close() end
    if shell == "lickintosh" then hl.config({ decoration = { rounding = 20 } }) end
end

if shellActions["switcher-next"] then
    hl.layer_rule({name="quickintosh-capture-chrome",match={namespace="^quickintosh-(quickshot-controls|sharing-panel|status-popover)$"},
        no_anim=true,blur=true,ignore_alpha=0.20})
    hl.layer_rule({name="quickintosh-island-surface",match={namespace="^quickintosh-island-dashboard$"},no_anim=true,blur=true,ignore_alpha=0.004})
    if hl.plugin.hyprglass then
        local glass = hl.plugin.hyprglass
        glass.config({ enabled = true, default_preset = "pomme", layers = { enabled = true } })
        glass.layer("quickintosh-quickshot-controls", { mask_mode="contour", mask_threshold=0.18 })
        glass.preset("quickintosh-island", {inherits="pomme",blur_strength=0.65,bevel_strength=0.18,specular_strength=0.22,dark={brightness=1.0,contrast=1.0,tint_color=0x00000000},light={brightness=1.0,contrast=1.0,tint_color=0x00000000}})
        glass.layer("quickintosh-island-dashboard", {preset="quickintosh-island",mask_mode="contour",mask_threshold=0.004,live_resample=true})
        glass.layer("quickintosh-sharing-panel", { mask_mode="contour", mask_threshold=0.18 })
        glass.layer("quickintosh-status-popover", { mask_mode="contour", mask_threshold=0.18 })
        glass.preset("quickintosh-dock", {inherits="pomme",blur_strength=0.65,bevel_strength=0.18,specular_strength=0.22,dark={brightness=1.0,contrast=1.0,tint_color=0x00000000},light={brightness=1.0,contrast=1.0,tint_color=0x00000000}})
        glass.layer("quickshell:dock", { preset="quickintosh-dock", mask_mode="contour", mask_threshold=0.015, live_resample=true })
        glass.config({layers={live_resample_fps=0},windows={background_cache=false,live_resample=true,live_resample_fps=0}})
    end
end

-- Emoji chrome stays in the client render pass; native contour glass would
-- also refract its dense colored glyphs. Compositor blur keeps text sharp.
hl.layer_rule({name="quickintosh-emoji-picker",match={namespace="^quickintosh-emoji-picker$"},no_anim=true,blur=true,ignore_alpha=0.20})

-- The transparent Quick Look click shield has no visible entrance/exit motion.
hl.layer_rule({name="lickintosh-quicklook-modal",match={namespace="^lickintosh-quicklook-modal$"},no_anim=true})

-- Native pointer locator and persistent user customization.
dofile(os.getenv("HOME").."/.config/hypr/cursor-locate.lua")

-- Keep desktop SDR output stable when applications enter fullscreen: do not
-- trigger monitor picture-mode switching from app content-type hints.
hl.config({render={send_content_type=false,cm_auto_hdr=0}})

-- Calculator owns its translucent chrome; the compositor supplies live glass.
hl.window_rule({name="quickintosh-calculator",match={title="^Quickintosh Calculator$"},float=true,center=true,focus_on_activate=true,opacity="1.0 1.0",tag="+hyprglass_enabled"})

-- Profiles must be declared inside the real reload: hyprglass queues preset/layer
-- declarations and commits them only after config.reloaded, not hyprctl eval.
if shellActions["switcher-next"] then
    local state = os.getenv("XDG_STATE_HOME") or (os.getenv("HOME") .. "/.local/state")
    local materialPath = state .. "/lickintosh/settings/native-glass-config.lua"
    local materialFile = io.open(materialPath, "r")
    if materialFile then materialFile:close();dofile(materialPath) end
end
