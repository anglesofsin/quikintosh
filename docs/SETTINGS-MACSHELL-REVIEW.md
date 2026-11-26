# Settings: MacShell page review

Reference: [vladbiber/macshell](https://github.com/vladbiber/macshell),
`48f73c94f7e54c2dce3206d3186875f52f139272`, `MacShell/MacDock.qml`.
The existing MIT notice is in `THIRD_PARTY_LICENSES/MacShell-MIT.txt`.

The review uses the reference's compact sidebar, restrained headings, rounded
cards, consistent form rows and clear grouping. It retains Quickintosh's richer
backends; it does not add decorative Apple-only settings or remove working controls.

| Reference pane | Quickintosh destination and review |
| --- | --- |
| General | General: system, language/time, applications and services groups |
| Menu Bar | Menu Bar: visible items first, clock/battery, then background/colors/logo/behavior |
| Dock | Desktop & Dock: live configuration preview, size/magnification group |
| Appearance | Appearance: appearance tiles, theme colors, icon/widget styles, material and performance |
| Behavior | Desktop & Dock: separate behavior group; existing autohide behavior preserved |
| Apps | Desktop & Dock: pinned-app preview, recent-app controls and exclusions retained |
| Wi-Fi | Wi-Fi: enable/join/network cards; scanning and connection dialogs preserved |
| Bluetooth | Bluetooth: adapter/device grouping and pairing retained |
| Network | Network/VPN: service, saved connections and configuration groups |
| Battery | Battery: compact power controls, history and consumption retained |
| Control Center | Control Center: connectivity, sound/display, tools groups |
| Desktop & Dock | Desktop & Dock: preview and dock groups before desktop/widget controls |
| Widgets | Widgets: appearance, surface, correct three-state dimming, gallery and personalization |
| Displays | Displays: arrangement, display selection and advanced controls retained |
| Notifications | Notifications: global settings, banner destination and per-app settings |
| Sound | Sound: incoming calls, notification sound, output/input groups |
| Focus | Focus: profiles, notification rules, schedules and automation retained |
| Lock Screen | Lock Screen: preview first, clock typography, notifications/media, security; font tiles wrap |
| Users | Account / Users & Groups: profile and security sections |
| Keyboard | Keyboard: repeat/delay, layout, shortcuts and restore controls |
| Mouse | Mouse: point/click, scrolling and restore controls |
| Trackpad | Trackpad: gestures/scrolling and restore controls |
| Wallpaper | Wallpaper: display/target, gallery and options retained |
| About | About: system/hardware details and links; no imitation AppleCare fields |

Quickintosh-only pages use the same shared form components: Accessibility,
Dynamic Island, Spotlight, Screenshots, Compositor, Activity, Privacy,
Passwords, Internet Accounts, Printers, Default Applications, Login Items,
Intelligence & Assistant, Game Mode, Updates, Storage, Date & Time,
Language & Region, Sharing, Backups, Shortcuts, App Permissions,
Automatic Locking, Weather and Privacy Indicators.

Additional corrections in this review:

- Screenshot, recording and OCR/translation preferences have separate cards.
  Directory fields have explicit labels and a folder chooser.
- Direct form rows use a 44 px minimum and 13 px labels, matching switches.
- Long legacy pages have a compact section jump control. It scrolls the same
  page rather than constructing another page or changing settings.
- Widget dimming remains an `auto` / `always` / `never` enum. Old boolean values
  from the incorrect switch are normalized.
- A page-owned timer cancels queued refreshes when a page is destroyed.

## Validation

All 48 catalog routes loaded in an isolated nested compositor, with screenshots
of every route reviewed in contact sheets. Missing D-Bus services, absent user
wallpapers/profile and the intentionally absent main shell in that environment
produce availability banners; this is not a full hardware/backend exercise.
No user settings were changed by the visual fixture.

Regression tests verify all Dock property references and lock-screen control
references survive regrouping, all capture preferences remain represented and
the widget dimming enum has all three choices:

```sh
QI_SETTINGS_SOURCE=/path/to/assembled/source/before/settings-review \
  python3 tests/test_settings_review.py
```

This is a design adaptation, not a claim of pixel identity or of implementing
MacShell-specific backends in Quickintosh. Earlier shared Settings work and
Quickshot measurements are recorded in `SETTINGS-QUICKSHOT-VALIDATION.md`.
