# Live activity rebuild

Requested exceptions: Discord voice, music playback, high CPU satellite, privacy
dot and screenshot retain their existing presentation and service wiring.
New event cards have a separate ActivitySurface and ActivityData adapter; the
previous event layout is hidden rather than used as their visual base. Existing
service state and dispatch remain the source of truth.

Compact measurements: 118 × configured pill height (26 px by default), matching
the default Discord voice width (106 + 12). The standalone review fixes 118×26.
All common compact events use that width; long labels elide instead of enlarging
the pill. Expanded events use a separate 320 px surface. Satellites use existing
stage diameters, with no CPU visual replacement. Expanded notifications can grow
for a supported inline reply. The native CPU component is isolated as a legacy
component, only instantiated for CPU.

Adapters: battery charging/full/low, timers/alarm, recording, network/VPN,
Bluetooth/peripheral, HUDs, jobs/builds/downloads, clipboard, workspace/keyboard,
output route, focus, reminders and weather. Recording stop and timer pause route
to existing services. Notification default action and inline reply use advertised
notification actions, never a simulated remote send. Other event activation
continues through the owning island's existing hit region.

Visual reference: user supplied Droppy activity montage. Only comparisons with a
real supplied counterpart include a Droppy column; absent references are labelled
as absent rather than invented. Native fixtures are explicitly synthetic data.
They do not establish actual device connectivity or zero-lag behavior on hardware.

Battery cards are the deliberate width exception requested during review: the
compact width measures the complete localized label, percent and battery glyph.
The normal compact width stays 118px; battery status expands only as needed.
New non-notification expansions use 320×64 outer dimensions; notification text
uses 320×88 and grows for an attachment or supported inline reply. SF Pro Text
uses 12px compact labels (11px for battery), 12px primary expanded text
and 10px secondary text; notification headings use 14px. VPN connection state is
11px regular above a 12px semibold connection name. These were adjusted after
measuring glyph heights against the supplied reference, normalized by pill height.

New event surfaces suppress the previous rim, sheen, goo joins, sand/water fill,
caps outline, sparks and chime flash. The exclusions still use those effects
according to their existing settings. The generated filled battery and VPN assets
are stored in the source tree with provenance; image-generation imperfections
are not described as exact glyph equivalence.

The gallery includes transfer/cloud visual states with explicit synthetic data.
It does not fabricate live percentage telemetry from KDE Connect or claim a
Droppy Cloud/iCloud implementation. Those providers expose different capabilities.
Only real supported state is displayed by the live adapters. Protected views were
not redesigned; the high-CPU component uses the original code in a conditional
loader. Physical hardware and a macOS Droppy install were not used for testing.

## Evidence and limits

Passed in private nested Wayland compositors:
- 35 compact event variants; satellite/clock/privacy spacing in three alignments,
  plus offsets. This suite ran before the final provider hook; the card geometry
  was unchanged by that hook.
- 31 synthetic cases × four presentations, including long labels, unknown charge,
  rich notification, inline reply and semantic colors; 124 individual comparisons.
- Ten actual assembled expanded event views, saved separately from widget fixtures.
- Repeated dashboard/event handoffs, 20 open/close loops and 12 interrupted reversals;
  an actual left click opens the new event. The final integration run also checks
  activity selection, a Tray arrival and direct Tray opening.
- Thirteen backend tests, including activity kind fallback, finite progress bounds,
  expiry and removal, plus the earlier navigation persistence cases.

One cold private run exceeded its IPC readiness timeout; a separate earlier handoff
run exceeded its 5-second test deadline. Those failed runs were inspected, not
counted as passes. The final instrumented assembled run passed. Software nested
rendering and screenshots do not establish zero latency or absence of every
possible hardware glitch. No live session was activated or rebuilt.

The public shelf activity IPC accepts bounded kinds task/download/share/cloud/launch
and optional progress. Its active event now reaches the compact island and expanded
view. Provider-supplied progress is displayed; absent provider telemetry is not
invented. A newly added Tray item emits a transient count and a click opens Files.
VPN elapsed time starts when this shell observes the connection (it is not a claim
about connection age before shell startup).

Review folder: ~/.local/state/quickintosh/reviews/activity-redesign/INDEX.md.
Original screenshots, generated comparisons and final pass logs are kept locally.

Final screenshots were refreshed after the typography correction. The final
native surface and assembled expansion suites passed again. The gallery contains
31 overview comparisons and 124 individual compact/expanded/left/right comparisons;
left/right fixtures deliberately show the satellite representation. Old/source
comparisons are included only where captured, and Droppy columns only where a real
supplied reference exists. Native captures are not AI mockups.

Follow-up alignment correction: expanded recording puts its dot and timestamp in
one header row, with the recording label beginning under the dot. Meter tracks
are siblings of their icon and value in the same vertically centered row, rather
than occupying a lower row inside the text column. Compact labels can expand the
pill width to their measured contents; equal label/value strings render only once.
Native tests assert meter/icon/value centerlines, recording subtitle/dot alignment,
and duplicate-percentage normalization. The 31 native scenarios and ten assembled
expansions were rendered again after these changes.

Meter audit: all inline activity HUD bars use the single activity-meter row.
Native geometry assertions now check icon/track/value vertical centers in BOTH
compact and expanded presentations, with 0.5px tolerance. The 37-case run passed,
including volume, mute, microphone, microphone mute, brightness, keyboard-light
visual fixture, and volume at 0/100/200%. Player seek and application mixer were
also inspected in source: their dedicated centered/full-row layouts do not use
the old lower-text-column track. Their existing presentation was left intact.
