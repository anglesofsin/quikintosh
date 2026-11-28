# Settings consistency review — 2026-11-27

Changes are prepared in source and a private compositor. They are not activated in the user's session.

The audit covers the 48 catalog routes and the compatibility Glass route. Native screenshots include the top and bottom of every route, the advanced Appearance and Island disclosures, and a notebook Battery fixture. The private session has no real session bus; unavailable audio, keyring and Flatpak services are not evidence of broken hardware on the host.

## Corrections

- General owns About, Default Applications, Login Items and Game Mode; Weather belongs to Widgets. File Servers and App Activity describe the implemented Linux functionality without suggesting unavailable account or website integrations.
- Dedicated widget appearance editing links to Appearance instead of duplicating its style selector. Desktop, Widgets and Island internal links preserve this Settings window's navigation history.
- Unknown combo selections stay unselected. Data fields do not translate paths or user values. Empty Hyprland strings do not display `[[EMPTY]]`.
- Microphone volume includes its percentage. Notification duration, input delays, idle time and interface size have useful units. Unavailable NTP data is not reported as Off.
- Keyboard, Mouse and Trackpad reset only their own input overrides; compositor overrides survive. The reset button is disabled when its page has no override.
- Focus rejects malformed schedule times and empty profile names. Schedule fields follow schedule enablement; timed expiry follows Focus enablement. Evening expiry retains its matching selection.
- Disabled global or application banner policies disable dependent per-app banner controls. Audio and permission handlers guard missing device/app selections.
- Game Mode uses serialized, idempotent backend actions and refreshes its reported state rather than blindly toggling a detached process.
- Island Advanced excludes controls already exposed by dedicated sections. The section index follows disclosure height changes. Generic page navigation resets scroll position.
- Search indexes actual legacy-page control labels and translated terms, handles accents, and keeps existing no-result feedback. Error banners can be dismissed; actions fail clearly if the worker is not ready.
- Common rows have accessibility names/actions, consistent numeric typography, keyboard slider commits and Escape cancellation for text edits. Blur schema labels have English translations.

## Validation and practical limits

Backend tests cover normalization, Game Mode idempotency, validation, state isolation and restoration. Native private UI tests load every route and exercise unknown selections, scoped input reset, invalid Focus time rejection and control-label search. Page captures and comparisons are stored under:

`/home/pg/.local/state/quickintosh/reviews/settings-complete-audit/`

No network connection, account, password, power mode or physical device was changed. Loading and inspecting all pages is not a claim that every hardware-dependent action has been exercised. The audit fixes identified defects; it cannot prove the absence of every possible UI inconsistency.
