# Contextual activity icons

Automatic mode defaults on when no preference is saved. The engine uses explicit
kind, status, channel and device metadata; it never guesses the application or
hardware from the visible title. Unknown metadata retains the event symbol or a
neutral Bluetooth/fallback symbol. Rules are pure JavaScript with no polling,
network requests, image generation or blocking work in the render path.

Selection order: known event symbol → device/channel → per-event override →
confirmed state (error before completion) → optional per-state override. Completion
comes from a confirmed result or provider progress, not a text string containing
100%. Unknown/invalid symbols fall back to an allowlisted icon. Missing notification
badge images fall back while loading or on failure, rather than leaving an empty
badge. Controls retain action-specific symbols; recording and battery indicators
retain their essential identities and safety colors. Discord voice, music, high
CPU, privacy dot and screenshot presentation are not replaced by this policy.

Settings → Dynamic Island → Activity icons:
- automatic mode; state priority; device matching;
- status colors/monochrome and notification app badges;
- compact, expanded, meter and side indicator sizes;
- completion/error/pause/disconnection symbol overrides;
- collapsible per-event symbol overrides and restore defaults.

Preferences persist atomically through the existing shelf backend. Schema, allowed
symbols and size limits come from icon_policy.json. Python rejects invalid types,
nonfinite sizes and unsafe icon paths. JavaScript defends against malformed saved
preferences as well. Slider drags save on release, not once per motion event.
Ring satellites clamp symbol size to preserve space around the progress ring.
Expanded VPN geometry preserves its optical adjustment.

Validation: Node executes 450 kind/state/presentation combinations plus explicit
priority, invalid input, size, metadata and override cases. Backend tests cover
persistence and validation. Native private QML tests change options through the
backend, verify priority and per-state overrides, render Settings, and click Restore
defaults. HUD geometry regression tests also run in compact and expanded modes.
No live activation or Nix rebuild was performed.

Assembly verifies that every selectable symbol has a real generated PNG or bundled
SVG. There are no selectable missing-file placeholders. If a generated asset fails
to decode at runtime, ShelfIcon falls back to a bundled vector (VPN → shield,
filled battery → battery). Unknown mouse/device artwork uses a neutral Bluetooth
symbol instead of falsely displaying headphones. The backend also preserves an
explicit provider status; failed status wins even when progress reports 100%.

Per-event overrides are collapsed initially to keep the page usable. State icon
choices, four size profiles and the automatic switches stay visible. Native tests
verify live binding updates without changing the event, state override persistence,
Restore defaults, and an intentionally broken generated-image fallback. Existing
HUD centerline tests passed again with the new policy enabled by default.
