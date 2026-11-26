# Pointer customization

Mouse Settings includes pointer size (16–96 px), MacTahoe, MacTahoe Dark and
Bibata themes, original/preset/custom RGB colors, and the pointer locator.
The default is 31 px (24 × 1.3 rounded to the nearest whole pixel).

The locator uses a 40 ms Hyprland Lua timer with no position IPC or polling
subprocess. It detects rapid back-and-forth movement in a rolling window, rejects straight
travel, sensor jitter and monitor warps, and enlarges only the cursor. Continued
shaking extends the locator; after 650 ms without the gesture it shrinks gradually.
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

Apple documents rapid back-and-forth movement but does not publish its detector
thresholds or animation curve. This implementation is an approximation, not the
proprietary Apple algorithm: https://support.apple.com/en-ie/guide/mac-help/mchlp2920/mac
