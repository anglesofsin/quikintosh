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

## Stage A — icon and page-by-page revision in validation

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
  Browsing the catalogue alone no longer pins the island open.
- Home's playback and navigation controls use generated transparent PNG artwork,
  reviewed at 16, 24 and 32 logical pixels. The six additional generated catalogue
  icons share the same resolver. Existing assets remain for other controls. Progress and elapsed/remaining times share one row.
  Artwork is clipped to its rounded silhouette. Unavailable weather is shown
  explicitly, without a fabricated condition or temperature.

The user rejected the first review: the Fade lacked a convincing glass finish,
icons, item shapes and organization differed. Do not ask for approval of that
same candidate again. The revised material removes the gray base and inherited
dark tint, uses a dedicated native preset and a lower contour threshold. The
catalogue is now separate from Edit Home. Calendar event blocks and a compact
weather layout are included in the revision.

## Evidence and limits

Private UI regressions:

- `test_island_surface_ui.py`: native plugin, Home/Tray/Widgets, unscaled content,
  editor hold/release, return to the 92 × 26 compact silhouette, and native
  resampling counters (677 draws, 677 cache misses, zero cache hits in the
  last completed revised-material run).
- `test_island_morph_ui.py`: the actual Island/IslandWindow owners, 20 repeated
  compact/dashboard handoffs, with no compact surface visible while covered,
  plus disabling the dashboard without losing the compact island.
- `test_island_live_glass.py`: per-frame native resampling and plugin reload.
- `test_native_glass.py`: eight registry/config regressions.
- `island-shelf/test_backend.py`: ten file operation/persistence regressions.

Review artifacts are generated outside the repository, under
`~/.local/state/quickintosh/reviews/droppy-a/`: real captures, a reference/candidate
comparison, logs and a 60 fps encoded compositor recording. The isolated render
uses software graphics; the recording's frame rate is **not** a measurement of
hardware responsiveness. The first screenshots were empty states; the revised
`droppy-a-v2` captures use an explicitly private MPRIS service and marked sample
calendar/weather data. These are test fixtures, not a live forecast or calendar.
The test verifies playback/pause against the real D-Bus service. Reference
artwork/background crops are temporary research artifacts, not shipped assets. Overall pixel parity has not passed and must not be asserted.

The subsequent `droppy-design-audit` candidate adds all thirteen page captures,
three local widget-detail captures, real private clipboard/file-tray fixtures,
a seven-day forecast fixture and populated Notes. The widget regression asserts
actual loaded component names; this caught and corrected a collision between a
`focus` component id and the inherited Item property. Expanded calendar events
and month have separately bounded geometry. Its source, generated-icon sheet,
MPRIS actions and per-page geometry are saved beside the captures. The exact
installed skill inventory is `DESIGN-SKILLS.json`; the visual audit checklist is
`DROPPY-PAGE-DESIGN-AUDIT.md`.

The ordinary portable shell build also exposed an omitted `caelestia-shell`
argument in the NixOS module; this is fixed. That build then encountered inode
exhaustion while copying the icon bank. Source assembly and UI validation use
the already installed, ABI-matched dependency derivation with the changed
modules substituted. A normal portable build is still required before release.

## Remaining milestones

A review: the first candidate was rejected. The revised candidate needs a new
visual comparison and approval before replacing the installed UI.

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

Latest optical review uses 14 AI-generated PNGs and a visible-alpha-bounds resolver. Four playback actions share the reference-style transport row. Calendar lists all actual events in a clipped, scrollable viewport. The exact current test log is saved with the review artifacts. No installation activation has been performed.
