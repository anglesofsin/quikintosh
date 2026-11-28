# Liquid Glass monitor-edge padding

Native workspace slide moves glass panes partly beyond the monitor. HyprGlass clips the background blit to framebuffer bounds and clears the unused sample padding to transparent black. Blur/refraction reads this padding, producing a dark band on the side crossing the screen edge. This reproduces without Quickintosh's screen-corner overlay.

The new patch extends the nearest valid source texels into the clipped padding, equivalent to clamp-to-edge. In-bounds mapping, blur parameters, glass presets and screen-corner appearance are unchanged. Up to eight small framebuffer copies occur only when the sample intersects a monitor boundary. Completely out-of-bounds samples do not submit invalid blits.

## Validation

Built against the exact running Hyprland ABI. Real private nested compositor comparison uses the previous plugin and candidate plugin with the same flat background, glass window size and positions: center, each screen edge and a corner. It verifies actual window geometry, tests both plugin load/unload paths and captures native workspace slides in both directions.

Measured edge RGB changed from 124 to 178 on left/right and 114 to 178 on top/bottom; 178 matches the pane interior. The in-bounds center remains 178. Assertions require at least 25 levels of edge recovery and no more than 2 levels of in-bounds change.

Captures and metrics:
`/home/pg/.local/state/quickintosh/reviews/glass-screen-edge/`

The Settings consistency source and glass plugin were activated in the current user session, with backups under `active-review/before-settings-complete-*` and `active-review/before-glass-edge-*`. No NixOS system rebuild or compositor restart was performed. The source Nix definition includes the patch for future builds. User-specific terminal/workspace timing still needs observation in the real session; isolated pixel checks do not prove every driver/animation combination.
