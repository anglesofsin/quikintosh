# Rendering and responsiveness

Settings → Appearance → Rendering & Performance controls the shell renderer,
frame limits, preparation of closed panels, animations and effect quality.

The default Native refresh rate profile adds no FPS limit to Qt rendering or
live window captures. Vsync, the compositor, display refresh rate and GPU still
determine the delivered frame rate. Balanced and Power saving are optional;
Custom permits separate interface, glass and geometry limits. Zero selects
Automatic. Limits do not affect applications outside Quickintosh.

Glass uses a small read-only Hyprland plugin to obtain current animated window
positions and workspace viewports. Normal Hyprland client IPC supplies target
positions, which cannot represent every intermediate frame of a workspace
slide. The plugin registers only `quickintosh:geometry`; it does not hook the
renderer or change windows. It must match the compositor ABI. The launcher
loads the bundled matching plugin; an incompatible compositor keeps the normal
geometry fallback rather than bypassing the version check. Geometry queries
stop after motion settles, and capture subscriptions pause for closed surfaces.

Live widget dragging is the default. Cached drag previews are available for
slower GPUs. Widget edits are merged per frame and snapshots retain delegate
identity. Clock measurement is independent of every resize pointer event, and
snapshot widgets never reuse textures from a different window.

The renderer setting requires an explicit shell restart; the other controls
apply live. Turning off animations, blur, glass, shadows or looping effects is
independent of the FPS controls. Lower texture resolution reduces GPU work.
Prepared panels trade memory for faster repeated opening.

Frame diagnostics are optional and disabled by default. They report actual Qt
present intervals for active shell windows, with a bounded sample buffer. Idle
windows are not an FPS benchmark. `quickintosh ipc call frames status` exposes
the same data without opening a panel.

Validation: isolated Wayland output at 60 Hz, animated test window: 57.9 FPS
without an additional cap; 29.9 FPS with a 30 FPS cap. These software-rendered
test results validate the pacing controls, not guaranteed performance on other
hardware. The matching geometry plugin was loaded and returned valid viewport
rectangles on the author's 239.997 Hz compositor. Regression tests cover widget
edit coalescing, clock metric reuse during resizing, current-geometry offsets,
workspace clipping, and capture shutdown without binding loops.

Workspace motion regression fixes: the geometry expression is preserved through
shell scaling, so the image and its viewport use the same current coordinates.
Retained closed panels disconnect from geometry publications; they keep their
cached texture without dirtying their scene on every workspace frame. With the
native geometry reader available, motion no longer also refreshes the complete
Hyprland client model repeatedly on the QML animation clock.

Startup packaging includes the profile script, its Quick Look MIME module and
Finder stylesheet in the same source directory. This avoids a missing-module
failure before shell startup on a fresh login.
