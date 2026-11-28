# Liquid Glass monitor-edge padding

Native workspace slide moves glass panes partly beyond the monitor. HyprGlass clips the background blit to framebuffer bounds and clears the unused sample padding to transparent black. Blur/refraction reads this padding, producing a dark band on the side crossing the screen edge. This reproduces without Quickintosh's screen-corner overlay.

The new patch extends the nearest valid source texels into the clipped padding, equivalent to clamp-to-edge. In-bounds mapping, blur parameters, glass presets and screen-corner appearance are unchanged. Up to eight small framebuffer copies occur only when the sample intersects a monitor boundary. Completely out-of-bounds samples do not submit invalid blits.

## Validation

Built against the exact running Hyprland ABI. Real private nested compositor comparison uses the previous plugin and candidate plugin with the same flat background, glass window size and positions: center, each screen edge and a corner. It verifies actual window geometry, tests both plugin load/unload paths and captures native workspace slides in both directions.

Measured edge RGB changed from 124 to 178 on left/right and 114 to 178 on top/bottom; 178 matches the pane interior. The in-bounds center remains 178. Assertions require at least 25 levels of edge recovery and no more than 2 levels of in-bounds change.

Captures and metrics:
`/home/pg/.local/state/quickintosh/reviews/glass-screen-edge/`

The Settings consistency source and glass plugin were activated in the current user session, with backups under `active-review/before-settings-complete-*` and `active-review/before-glass-edge-*`. No NixOS system rebuild or compositor restart was performed. The source Nix definition includes the patch for future builds. User-specific terminal/workspace timing still needs observation in the real session; isolated pixel checks do not prove every driver/animation combination.

## Follow-up: outgoing workspace, 2026-11-27

The user clarified that the artifact affects the departing terminal, while the incoming terminal looks normal. Live counters collected over nine real workspace changes (1/2/3) show every glass draw receiving a fresh sample, with no deferred resamples in those intervals. Thus the evidence does not support simply saying the plugin turns glass off on invisible workspaces.

A second patch widens repaint damage to the monitor at workspace activation and while the window's workspace offset/alpha animates. This refreshes the framebuffer beneath outgoing as well as incoming panes, instead of relying on narrower translated window damage. It does not keep hidden workspaces rendering at idle. The original edge-padding fix remains included.

Private regression covers two tiled panes moved to an invisible workspace, with the plugin loaded while they are hidden (no prior pane samples), followed by cold entry, repeated entry/exit slides and settled pixels. Candidate: 79 glass draws, 79 fresh samples, zero deferred samples; zero monitor frames over the final idle measurement. The previous version also passed the cold-entry sample-count check; the private test does not reproduce or prove removal of the user's exact outgoing artifact. Real-session confirmation was requested after activation.

Candidate library: `/nix/store/bnd098x4dhcmpwhvkpg2phh31rh9lpxd-hyprglass-1.1.0/lib/hyprglass.so`.
Live trace and native captures: `/home/pg/.local/state/quickintosh/reviews/glass-workspace-reentry/`.
