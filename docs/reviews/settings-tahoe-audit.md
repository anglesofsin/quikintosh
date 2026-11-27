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
