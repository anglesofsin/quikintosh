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
