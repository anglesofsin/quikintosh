# Screen-sharing picker and cursor

Quickintosh replaces only the portal's source-selection UI. The Hyprland portal
still creates and authorizes the actual capture session. Display, window and
workspace identifiers come from the portal-provided source lists. Cancel/close
emits no selection; Share emits the portal's `[SELECTION]` protocol, with the
remember flag only when selected. Region coordinates are converted to the chosen
monitor's local coordinates. Cross-monitor regions use their largest intersecting
monitor, matching the portal's single-output region capture model.

Display snapshots are taken before the picker maps and are temporary private
files; visible window previews are cropped from those snapshots. Hidden-window
and workspace cards use neutral placeholders rather than showing unrelated
screen contents. Previews are static snapshots, not live video. The selector
uses native compositor glass through its dedicated window rule.

The MacTahoe cursor is the Linux Tahoe-style theme by vinceliuice, pinned to
`839848b9a8a38a92a6936e30c4abe35cc6f2546d`, not a claim of extracted Apple assets:
https://github.com/vinceliuice/MacTahoe-icon-theme/tree/main/cursors
Its GPL-3.0 license is installed with the theme. The theme is included in both
NixOS and Arch bundles, with persistent cursor environment configuration.

Validation: isolated nested-compositor rendering and selection response;
five protocol tests (UTF-8 lengths, handles, unknown-source rejection,
negative monitor coordinates, cancellation), four Settings regressions and
ten Arch installer tests. An actual third-party application's sharing session
is a separate end-to-end check and is not started automatically.
