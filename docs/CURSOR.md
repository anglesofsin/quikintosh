# Pointer customization

Mouse Settings includes pointer size (16–96 px), MacTahoe, MacTahoe Dark and
Bibata themes, original/preset/custom RGB colors, and the pointer locator.
The default is 31 px (24 × 1.3 rounded to the nearest whole pixel).

The locator uses [hypr-dynamic-cursors](https://github.com/VirtCode/hypr-dynamic-cursors),
pinned to `2a8d0b735328d874a78ca93b2f201649f712a74a` and built against the exact
bundled compositor. Rotation, stretch and tilt are disabled. The native shake
detector compares travelled distance with its bounding diagonal (inspired by
KDE's shake detector), requires sustained oscillation and increases magnification
while the gesture continues. The native animation engine interpolates growth and
restoration; cursor themes are not reloaded per frame. User controls include
maximum enlargement, growth speed, sensitivity and hold duration. Disabling the
feature also disables the plugin's effects.

Preferences are persisted through SettingsPreferences inputOverrides; the runtime
validates and separates them from ordinary Hyprland options. The effective Lua
configuration lives at ~/.config/quickintosh/cursor.lua and is read at compositor
startup/reload. Tint variants are generated once per theme/color and cached under
~/.local/share/icons, preserving alpha, frames, hotspots and light outlines.

Apple documents rapid back-and-forth movement, but does not publish its detector
thresholds or curve. This is not Apple's proprietary algorithm:
https://support.apple.com/en-ie/guide/mac-help/mchlp2920/mac

Validation of the native integration used a nested instance of the exact installed
Hyprland binary. The plugin loaded, survived configuration reload and reported
no configuration errors. A forced magnification exercised intermediate animated
values; injected back-and-forth motion in that isolated instance produced 280
scale samples spanning 1×–4× and returned to 1×. Warps were enabled only in that
fixture because nested Wayland input is classified as warped motion. Live
configuration ignores warps and leaves shake IPC disabled. These are functional
and interpolation checks, not a benchmark of the user's physical monitor FPS.

## High-resolution magnification

MacTahoe and MacTahoe Dark now include separate `-HD` Hyprcursor themes packed
from upstream SVG paths, including shape aliases, click hotspots and animation
frames. The normal cursor remains the existing Xcursor theme, retaining its
normal size and shape. The native magnifier reads the separate vector theme at
twice the configured maximum size (capped at 512 px), instead of stretching the
small normal cursor texture. Bilinear sampling replaces nearest-neighbor scaling.
Themes load asynchronously and are adopted on the next render once ready,
without requiring a subsequent pointer-shape change. Changing maximum size
refreshes the cached resolution once; mouse motion does not rebuild themes.
Custom color variants also retain vector SVGs and metadata in their HD cache.
Unavailable application-provided custom cursors keep their own image rather than
being replaced with an unrelated fallback cursor.

Validation rendered arrow/text/hand at 33 and 264 px through libhyprcursor in both
MacTahoe themes, including all 13 wait/progress animation frames. The nested
compositor loaded the 264 px vector theme asynchronously (169 ms in this software
fixture), completed animated magnification and recorded progressive shake values
from 1× to 4×. This measures functionality, not physical-monitor frame rate.
