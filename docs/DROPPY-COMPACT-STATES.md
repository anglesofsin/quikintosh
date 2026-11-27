# Compact island and satellite review

Reference: https://getdroppy.app/features/live-activities and
https://getdroppy.app/features/dynamic-island . This revision covers existing
local activities; it does not fabricate new providers or claim Apple-only APIs.

## Composition

The central pill owns the foreground activity. The left satellite keeps the
existing priority order (call, launch, download, printing, task, timer, reminder,
system). The right satellite retains concurrent media. Privacy is a separate
status indicator after the rightmost rendered edge, not a slot inside either
activity. The same source owns clicks and the existing expanded/shelf handoff.

Privacy previously used a cached collapsed central-pill width. It ignored the
right media satellite and could lag behind geometry changes. It now follows the
transformed union of the surface and visible right satellite, including their
scale, squash, magnetic displacement and entry/exit springs. Target spacing is
8 logical pixels, clamped inside the monitor; edge rounding can reduce this to
6 pixels. Its existing semantic colour and fullscreen handoff remain unchanged.
No new poller, screenshot capture or continuously running frame timer is added.

## Compact profile

Droppy uses a black compact base, restrained content colour and no old coloured
flash halos/fill-wave decorations. Classic and Custom retain those options.
SF Pro Text uses tabular digits. An unavailable/disabled clock does not reserve
an invisible clock column. Persistent local activities retain an icon when the
clock is disabled; timer duration comes from the actual Timers owner, recording
duration from CaptureState. No invented progress or timer is displayed.

Event and side-slot symbols use the existing shared icon resolver, including the
AI-generated music/calendar/bell/camera/clipboard icons. Artwork remains circular
and rotating according to existing settings. Existing operation handlers and
provider priorities are preserved.

## Verification scope

`test_island_compact_ui.py` renders the real compact components in a private
compositor for 35 supported demo event types and 8 left-slot types. Its test-only
overrides hold the surface compact, force privacy active and toggle the two
satellite springs. These overrides are not installed in the product. The gap is
checked throughout transitions in center/left/right alignments, including exit.
The screenshot test does not activate real microphone/camera, calls, recordings
or downloads. Demo labels belong to the existing demo provider; they are not
real notifications. Availability of a renderer is not proof of provider parity.

The compact call no longer reserves the optional wall-clock column when that
clock is off (72px content instead of 106px). The timer/recording indicator hides
the unrelated wall clock while active, preventing two centered labels from
painting over one another. The expanded call remains unchanged.

The final review was repeated after the disk inode cleanup. Concurrent disk I/O
can delay the external test CLI; its command timeout is not a production latency
threshold. Functional correctness and visual geometry checks remain separate
from hardware FPS/latency certification.

Alignment uses one bounded x position instead of opposing conditional anchors.
The old anchors could stretch the stage to most of the monitor and lose its
width binding after a left/right/center switch. The regression now checks the
stage remains bounded by its contents, returns to the actual center and keeps
privacy in bounds at -200/0/+200 offsets. A small right-edge reserve accommodates
spring overshoot. Generated raster glyphs use a colourization layer only for
chromatic tint; neutral glyphs retain the direct image path. The rendered alarm
is checked for its actual semantic-colour pixels.

## Completed candidate validation

The final candidate passed on the private nested compositor:

- 35 compact event renderers and 8 left-slot renderers.
- 64 stored scenarios including alignment and -200/0/+200 offsets.
- 146 sampled intermediate frames: minimum privacy gap **8 logical pixels**.
- Stage width bounded by its actual content after each alignment change.
- Actual rendered alarm glyph passed the chromatic pixel assertion.
- Forced idle state did not introduce the legacy idle character.
- 20 real compact/dashboard handoffs and disabled-dashboard fallback passed.
- Eight native glass tests and ten shelf backend tests passed separately.

Evidence: `~/.local/state/quickintosh/reviews/droppy-design-audit/compact/`,
including `geometry.json`, `validation-final.log` and `compact-contact-final.png`.
Demo values and unavailable provider fallback states are explicitly test fixtures.
The wallpaper and pointer visible behind the private captures belong to the
isolated compositor. These tests do not certify every real hardware/provider
combination, fractional DPI or pixel identity with Droppy. This candidate is not
activated in the user's session. Approval of expanded pages is not treated as
approval of these newly revised compact surfaces.
