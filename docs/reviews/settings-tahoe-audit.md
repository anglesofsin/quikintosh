# Settings and Island transition review

The Dynamic Island settings route failed because ShelfAppearance instantiated Switch without importing Qt Quick Controls. It now imports Basic and uses the existing Tahoe switch dimensions and accent. The settings page groups shape/material, navigation, contextual icons, media, dashboard, calls/privacy, and advanced controls; existing advanced schema controls remain available through disclosure.

The Island stage previously became transparent whenever dashboardCover was set. Independent dashboard unmapping and collapse scheduling could expose a frame with neither surface painted. Keep the primary stage painted beneath the dashboard throughout the handoff, and re-evaluate completion when its body geometry settles. Interaction ownership remains unchanged.

Shared Settings improvements apply across the catalog: centered bounded content, consistent card insets, wrapped long read-only values, sufficient slider-unit width, stable path-row layout ownership, guarded empty wallpaper previews, route-specific errors cleared when navigating, and a retry action for component load failures.

## Verification

- Real Qt/Quickshell Settings captures in private nested Hyprland: 48 catalog pages plus the compatibility `glass` route (which resolves to Appearance). Every route loads after the fix. Captures include lower sections for 12 routes.
- Native Island tests: 20 open/close cycles, 12 interrupted reversals, event expansion, file arrival, right-click shell toggle, and media/voice/timer handoffs. Frame instrumentation detects no uncovered dashboard handoff frames.
- Structural checks preserve settings actions, FolderDialog behavior, advanced control groups, and supported call presentation values.
- Source-only Nix assembly; no OS rebuild or changes to network, accounts, credentials, or application data.

Visual artifacts are outside the repository at `/home/pg/.local/state/quickintosh/reviews/settings-tahoe-audit/INDEX.md`, including individual before/after comparisons and seven contact sheets. Hardware-dependent states in the screenshots belong to the private session; this does not validate changing Wi-Fi, Bluetooth, audio hardware, authentication, or every real-world timing scenario.

## Second pass: Battery and page consistency

The approved player and icon polish was activated at the user's request before starting this Settings pass. The new Settings changes are prepared separately for review.

Battery is rebuilt using the same SF Pro type and Tahoe cards/rows as the rest of Settings. It distinguishes a desktop on external power from a notebook with a battery; shows real connected devices from UPower/KDE Connect; preserves low-power rules, health, supported charge-limit controls, energy consumers and screen-activity history. History uses bounded bar delegates instead of QtGraphs. Empty battery graphs are hidden on devices without an internal battery or recorded history. Unsupported charge-limit and unknown health data do not produce empty controls. Hardware changes are never performed during review.

All 48 catalog pages plus the compatibility Glass route are recaptured in a private compositor. The notebook capture additionally uses explicit private fixture data to exercise actual charge, health, history and connected-device layouts. Generic Settings pages receive the same slim scrollbar treatment as legacy pages. Wi-Fi's disconnect click area is no longer a directly anchored child of RowLayout, removing an undefined-layout warning while preserving its action and leaving the Details button accessible.

Artifacts: `/home/pg/.local/state/quickintosh/reviews/settings-second-review/INDEX.md` (before/after for each route), plus `after/battery-notebook.png` for the private notebook fixture. These fixtures do not claim the desktop has a laptop battery.
