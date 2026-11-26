# Workspace backdrop settling

Reported symptom: a dark strip remains in part of the Dock glass when switching
from a workspace containing Zen to an empty desktop.

The existing glass compositor retains captured windows and interpolated geometry.
The correction makes settled live workspace membership authoritative, explicitly
refreshes monitor/window geometry when the fast transition period ends, and
invalidates all three offscreen texture stages after settled inventory updates.
During the transition, precise rendered geometry remains authoritative so the
outgoing window continues moving smoothly instead of disappearing early.

Validation: the assembled QML loaded in an isolated nested compositor, and four
window-to-empty-workspace cycles completed without QML errors. The simplified
fixture did not reproduce the user's wallpaper/glass appearance faithfully, so
this is a lifecycle check, not proof of visual equivalence with the reported
Zen scenario. Verify the actual Zen-to-empty-desktop transition after activation.

Follow-up for a flash during the transition: retain a window's last complete
capture texture during workspace switches, while continuing frame-synchronized
positioning and clipping. Do not restart the screencopy stream on its intentional
pause; resume and request a fresh frame after the workspace interval. This hold
is scoped to workspace changes, not ordinary window movement. It can briefly
freeze video content in the reflected window texture during the switch; it does
not freeze the Dock animation or its geometry. The isolated fixture remains a
lifecycle test; physical GPU/Zen visual verification is still required.

Native compositor path: when the matching Hyprglass layer renderer is available,
the Dock now disables its reconstructed screencopy backdrop and uses native
contour glass on `quickshell:dock`. The compositor samples the actual scene,
including workspace animation frames. The Python loader registers the layer
also on first boot, after plugin loading; Lua registers it on config reload.
The existing reconstruction remains a compatibility fallback. Native layer
resampling runs at the compositor rate, without a 30 FPS backdrop cap.

Fullscreen SDR stability: disable automatic HDR switching (`render.cm_auto_hdr=0`)
and monitor content-type hints (`render.send_content_type=false`). These can
change the entire output on fullscreen entry; this is a mitigation for the
reported monitor-wide washed-out flash, not a confirmed hardware diagnosis.
Do not change SDR brightness, saturation, or the user's sRGB output profile.

An isolated native-layer fixture completed three fullscreen/workspace cycles
without config errors and rendered a uniform Dock surface on the empty desktop.
Physical monitor picture-mode changes cannot be established in the nested
Wayland test; verify Discord fullscreen on the user's monitor after activation.

Dock material refinement: remove the white client wash (26% white), replacing
it with a restrained 19% black contour surface. Use a Dock-only Pomme-derived
preset with a smaller blur radius, neutral tint, restored contrast, and a weaker
bevel/specular rim. Window and other panel glass presets are unchanged.

Neutral material follow-up: lower the client black overlay from 19% to 3%,
remove the preset's extra black tint and contrast boost, and lower only the
Dock's contour threshold to 0.015 so the lighter surface still defines a complete
pane. The native path has no external client shadow to include in this contour.
