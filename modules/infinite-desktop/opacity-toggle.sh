#!/run/current-system/sw/bin/bash
# Toggles the active window between opaque and transparent+blurred
# (Super+Shift+\).
#
# The logic lives in modules/hyprland-lua/hyprland.lua, in the INFINITE_OPACITY
# global: it owns the persisted per-class state and dispatches the `opaque`
# prop, which is the only per-window lever that works in this Hyprland build.
# This script only forwards the call; Lua globals survive across `hyprctl eval`,
# so nothing has to be reconstructed here.
#
# `error()` is the only way to get a value out of `hyprctl eval` -- return
# values from the evaluated chunk are discarded.
exec hyprctl eval 'INFINITE_OPACITY.toggle()'