# Player controls and application fullscreen

Changes:

- AI-refined laptop bitmap with heavier white contour and translucent pale screen; optical crop preserves alpha.
- Output icon button enlarged (previous 32px button capped the icon at 20px; the new button allows 28px). Queue/output inset 6px toward the center. Transport spacing uses its actual width to fit compact players.
- Album-colored motion echoes suppressed during media presentation, in addition to the existing rim/glow guards.
- Expanded media no longer acquires exclusive keyboard focus. Reply/password input keeps its own keyboard ownership.
- Alt+F restores `sync_fullscreen` after setting internal maximize/client normal modes. Hyprland's fullscreen-state dispatcher disables synchronization when those modes differ; leaving that override active prevented subsequent client fullscreen requests from filling the display. Restore-on-new-tile receives the same cleanup.

Validation:

- Native isolated Qt/Wayland application receives F, requests fullscreen, then exits; repeated after internal maximize/client normal. Reproduced failure without restoring sync; both cases pass with the fix. This is a protocol/keyboard fixture, not automation of the user's YouTube session.
- Native media/control capture, artwork alpha/bounds checks, and morph regression record the current controls and media contour/focus state.
- Private software rendering does not validate hardware-specific Liquid Glass rendering quality.
