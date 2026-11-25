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
slide. The plugin exposes `quickintosh:geometry` as a fallback and observes the
public pre-render event after animation updates. It does not replace rendering
functions, draw into the compositor or change windows. It must match the compositor ABI. The launcher
loads the bundled matching plugin; an incompatible compositor keeps the normal
geometry fallback rather than bypassing the version check. High-frequency geometry polling is replaced by frame notifications when supported;
subscriptions expire automatically, and capture subscriptions pause for closed surfaces.

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

Geometry refresh also runs immediately when captures resume, on every workspace
transition (including consecutive transitions while already moving), and with
the existing stationary inventory pass. A successful native geometry snapshot
is authoritative: a missing window is not drawn from a stale workspace cache.
These rules apply to all surfaces using LiquidGlassBackdrop/GlassWindows,
including Dock, panels, Settings, widgets and Quick Look. Refraction remains a
Quickintosh GPU shader; this does not install Apple's proprietary renderer.

Version 1.1 sends frame snapshots through a private UNIX datagram socket. The
client drains queued events to the latest snapshot, applies an optional explicit
FPS cap, ignores late RPC replies while frame delivery is healthy, and removes
its subscriber socket on exit. A low-frequency heartbeat renews the subscription;
RPC/timer delivery remains available for older or incompatible compositors.
This removes independently timed geometry polling, but does not make two separate
processes render in the same compositor frame: capture, Qt rendering and Wayland
presentation still contribute latency.

Regression validation includes native socket delivery without a QML animation
window: 63 geometry publications uncapped versus 12 with an explicit 30 FPS cap
for the same short event burst. A live read-only probe received 122 compositor
packets in one second during existing desktop activity; this is not a workspace
animation FPS benchmark or a guarantee for other workloads.

Optional theme-service IPC has a bounded timeout and cannot abort shell login or
restart when gsettings/D-Bus is temporarily unresponsive. File profile errors
remain visible. The running shell confirmed `frameSynchronized:true` with all
FPS limits at zero after activation.
