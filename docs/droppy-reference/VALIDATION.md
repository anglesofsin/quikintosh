# Native surface validation

Tests run in an isolated nested compositor and private D-Bus, never on the user's
pointer or Discord profile. Artifacts: ~/.local/state/quickintosh/reviews/droppy-reference-review.

Established evidence:

- 17 temporary-file tests: archive/extraction safety, rename/collision handling,
  folder copies, tracked arrivals, image target size, PDF operations, video FPS,
  presets, transform-job isolation and uninstall guards.
- 9 offline developer/vault/reminder tests: Unicode, hashes, malformed inputs, bounded
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
