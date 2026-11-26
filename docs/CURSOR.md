# Pointer customization

Mouse Settings includes pointer size (16–96 px), MacTahoe, MacTahoe Dark and
Bibata themes, original/preset/custom RGB colors, and the pointer locator.
The default is 31 px (24 × 1.3 rounded to the nearest whole pixel).

The locator uses a 40 ms Hyprland Lua timer with no position IPC or polling
subprocess. It detects repeated direction reversals and sufficient travel in a
short window, enlarges only the cursor, and restores it after 1.1 seconds.
Disabling the feature disarms the timer. Magnification and sensitivity are
configurable. This does not change desktop zoom.

Cursor preferences are persisted through SettingsPreferences inputOverrides;
the runtime validates and separates them from ordinary Hyprland options.
The effective configuration is written to ~/.config/quickintosh/cursor.lua
and read on compositor startup/reload. Tint variants are generated once per
theme/color, cached under ~/.local/share/icons and retain alpha, frames,
hotspots and light outlines. No cursor pixels are regenerated on mouse motion.

Validation: synthetic shake/restoration/disabled-timer Lua regression,
Xcursor alpha/outline/alias regression, isolated Settings page loading.
