# Droppy implementation and visual review

The user approved visual checkpoints before replacing the installed interface.
The complete project is **not finished**. Stage A is a review candidate; B–E
remain required. Do not equate a successful source build with deployment or
claim full Droppy parity from the captures below.

## Stage 0 — special-workspace desktop ownership

The running Hyprland publishes some special workspaces using `address`, `name`
and `type`, with no numeric `id`. The old numeric-only policy misidentified these
workspaces. DesktopFocus now compares complete descriptors, prioritizes the
visible special workspace, and immediately consumes its socket close event.
Both older numeric and newer named event formats are covered.

`test_desktop_special_focus_ui.py` opens and closes a real special workspace 30
times on a private compositor, checks the GlobalMenuService state on every
transition, and requires 60 actual `activespecialv2` events. The regression passed.
It has not yet been activated on the user's installed shell.

## Stage A — candidate implemented

- Home, File Tray and Widgets share the existing dashboard window. A compact
  three-icon navigator follows its geometry below the island; its input region
  belongs to that same window.
- Home width adapts to the selected widgets, bounded by the display and the
  user's width setting. Content no longer scales a 1050 px layout down to fit.
- Black, Glass and live Fade reuse the native material pipeline. Default Home
  cards are transparent; its default size is 1140 × 216 logical pixels.
- Droppy, Classic and Custom interaction presets are wired. Droppy opens on
  hover/click; Classic preserves the activity click and dashboard right click.
- Page changes fade out before switching content and fade in afterwards.
- The editor owns an explicit open hold. Leaving the editor releases that hold;
  merely moving the pointer outside while configuring does not collapse it.
- Home's media controls use the existing Tahoe symbolic icon bank, at larger sizes.
  Artwork is clipped to its rounded silhouette. Unavailable weather is shown
  explicitly, without a fabricated condition or temperature.

## Evidence and limits

Private UI regressions:

- `test_island_surface_ui.py`: native plugin, Home/Tray/Widgets, unscaled content,
  editor hold/release, return to the 92 × 26 compact silhouette, and native
  resampling counters (418 draws, 418 cache misses, zero cache hits in the
  last isolated run).
- `test_island_morph_ui.py`: the actual Island/IslandWindow owners, 20 repeated
  compact/dashboard handoffs, with no compact surface visible while covered,
  plus disabling the dashboard without losing the compact island.
- `test_island_live_glass.py`: per-frame native resampling and plugin reload.
- `test_native_glass.py`: seven registry/config regressions.
- `island-shelf/test_backend.py`: ten file operation/persistence regressions.

Review artifacts are generated outside the repository, under
`~/.local/state/quickintosh/reviews/droppy-a/`: real captures, a reference/candidate
comparison, logs and a 60 fps encoded compositor recording. The isolated render
uses software graphics; the recording's frame rate is **not** a measurement of
hardware responsiveness. Test screenshots have no music, calendar events or
weather data. Populated media/calendar/weather designs still require stage B/D
comparison. Overall pixel parity has not passed and must not be asserted.

The ordinary portable shell build also exposed an omitted `caelestia-shell`
argument in the NixOS module; this is fixed. That build then encountered inode
exhaustion while copying the icon bank. Source assembly and UI validation use
the already installed, ABI-matched dependency derivation with the changed
modules substituted. A normal portable build is still required before release.

## Remaining milestones

A review: approve or revise this direction before replacing the installed UI.

B: populated media, filled playback controls, floating player, capability-aware queue/lyrics, concurrent
live activities, and their reference/candidate interaction tests.

C: file tray and clipboard workflows, widget catalogue and in-place editing,
including complete mouse/keyboard/drag-and-drop tests and visual review.

D: local modules, settings, Command Center and lock-screen integrations. Audit
all requested features individually. Optional model downloads remain opt-in;
account/key integrations and Apple-only cloud features remain excluded.

E: native hardware latency/frame-time/background-resampling validation,
multimonitor and fractional scaling, installed-session regression, normal Nix
build, final activation and GitHub delivery.
