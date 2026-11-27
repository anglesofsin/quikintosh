# Native surface validation

Tests run in an isolated nested compositor and private D-Bus, never on the user's
pointer or Discord profile. Artifacts: ~/.local/state/quickintosh/reviews/droppy-reference-review.

Established evidence:

- 17 temporary-file tests: archive/extraction safety, rename/collision handling,
  folder copies, tracked arrivals, image target size, PDF operations, video FPS,
  presets, transform-job isolation and uninstall guards.
- 10 offline developer/vault/reminder/preference tests: Unicode, hashes, malformed inputs, bounded
  data, JWT inspection, persisted script, safe vault paths and edit conflicts.
- Actual native URI drag, five-reversal shake, basket appearance and Transform
  drop: /tmp/qi-native-drag-check4.log.
- Native NotificationReplied signal with exact fixture reply text:
  /tmp/qi-native-notification-check.log. No message was sent to a real person.
- Local background segmentation produced an actual alpha image.
- Geometry 1.2.0 policy tests and private current-compositor ABI loading passed.
- Fifteen pages, Home editor hold, actual slot reorder, MPRIS commands, three
  floating player modes, notch/island geometry and native glass drawing passed
  in /tmp/qi-reference-release-qa-v2.log.

The complete v8 run passed in /tmp/qi-reference-release-qa-v8.log, including
toolkit execution through the actual QML/backend channel and the notch seam
correction. A focused release run separately covers the new reminder module
and editor holds in the final source.
Tab-selection timing measures synchronous selection, not end-to-end frame latency.
Video capture shutdown is allowed 45 seconds to flush the software test encoder.
The test checks all QML diagnostics for missing assets and runtime exceptions.

No claim is made of full 71-feature parity or pixel identity across all screens.

Notch seam: explicit one-pixel corner overlap, no body border in attached-notch
mode. Focused native validation passed in /tmp/qi-notch-seam-final-v2.log and
the screenshot was visually inspected before activation.

Follow-up audio validation: actual radius clipping replaces rectangular clipping;
the central divider was removed. Two synthetic stream levels (68% and 100%) were
rendered in a private compositor, with adaptive height. The render fixture is
not evidence of actual PipeWire gain control; that existing path was unchanged.
Evidence: /tmp/qi-audio-sized-final-v2.log, audio-rounded-fill.png.

The local command runner executed printf through its actual QML process bridge.
14 developer/terminal/Finder/vault tests and six MCP permission/protocol tests
passed. The stdio MCP initialization, tool discovery and read-only status call
also succeeded against the running shell. No external MCP client was modified.

Local speech inference processed the official public whisper.cpp JFK sample in
14.42 seconds in the backend test, then again through QML without microphone
capture. Evidence: /tmp/qi-transcribe-validation.json and
/tmp/qi-transcribe-ui-final.log. Input audio never came from the user's call.

Action Ring: three native layouts (220/320/412 px), actual shelf action routing,
paired Hyprland press/release registration, and early-release cancellation passed
in /tmp/qi-action-ring-shortcut-final.log. References were inspected textually;
the official detail image returned HTTP 403. No pixel-identity claim is made.

The microphone capture/stop protocol also passed using a private PulseAudio
null-sink monitor, never a real microphone or the user's call. Evidence:
/tmp/qi-private-recording-validation.json. The test server has its own session
and socket and is shut down afterward.

The full local workflow run /tmp/qi-editor-queue-release.log passed: delayed
TrackAdded signal updates, jump/add/remove requests, transient Wayland primary
selection/copy, app confirmation UI and toolkit/camera/notch rendering. The
private_mpris_queue fixture separately verifies delayed queue changes on D-Bus.
Latest personalization adds explicit recency-order and actual reorder assertions.
App-data review/uninstall runs in an isolated worker so scanning and package
operations cannot block the shelf backend. No actual uninstall was tested.

Personalization: /tmp/qi-personalization-final.log passed the actual widget drag,
recent-order assertion, inline editor screenshot and the supported local module
flows. The visual review additionally separated editor handles from widget titles.

The white edge fragments were editor chrome: an overhanging outline and vertical
resize handles. The outline now stays inside its slot with low contrast; the
resize action has a contained circular affordance. Editor content has a separate
top inset, keeping drag handles clear of track titles.

Follow-up editor refinement removes the ellipsis buttons entirely: reorder has a
small horizontal grip, resizing a narrow edge grip, both with larger invisible
hit targets. The obsolete catalogue slot editor is removed; pencil routes to
the same inline Home editor. No separate personalization flow remains.

/tmp/qi-job-history-final.log passed the updated editor drag and Tasks & Agents
page alongside the other local workflows. 23 backend tests include real process
exit forwarding with a private IPC stub and metadata-only job summaries.
