# Live glass and desktop behavior

Native window background caching is off by default. It previously retained a stale
background until the window moved. Startup now reapplies the live default, including
when the plugin was already loaded. This preserves the current material.

Settings → Liquid Glass selects a surface (windows, Dock, menu bar, menus,
Control Center, notifications, Spotlight, desktop widgets, widget editor, island,
QuickShot, assistant, power panels or OSD). Material, edge and color controls are
grouped separately from live updates and frame limits. Window-specific rules remain
in Windows & Effects. Per-surface and global reset controls are included. Explicit
native surface customization disables that surface's client glass only after the
compositor confirms application. Native registrations are submitted together so
customizing one surface does not remove the others. Frame limits default to unlimited;
window background caching is optional and may retain a static background.

A desktop widget's Lock Widget menu entry is persistent and checkable. Locked
widgets receive no mouse input and sit below files. They do not reserve widget
placement space. The desktop's Locked Widgets submenu unlocks them without needing
to click through files. The existing icon grid remains available over their area.

The menu bar checks the focused monitor's visible regular and special workspaces,
rather than trusting a retained active-window pointer from another workspace.
An empty desktop therefore owns the Finder menu.

Now-playing audio bars support a horizontal and vertical color gradient. The default
endpoint follows the album-derived color; Dynamic Island settings can disable the
gradient or choose a custom endpoint. Audio heights retain their existing animation.
