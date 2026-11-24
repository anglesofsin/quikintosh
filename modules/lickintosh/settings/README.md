# Lickintosh Settings

Native Quickshell Settings app inspired by the macOS Tahoe System Settings
organization, with actual Linux services and rice-local preferences.

## Structure and behavior

- 45 searchable routes, grouped sidebar, local account card, back/forward history,
  Ctrl+F search and Alt+Left/Right navigation. Last selected page is remembered.
- Floating window with traffic-light controls, opaque content cards and a Liquid
  Glass sidebar. The backdrop excludes its own process and window capture.
- Existing Wi-Fi, Bluetooth, Battery, Menu Bar, Assistant, Desktop & Dock, Displays,
  Spotlight, Wallpaper, Lock Screen, Dynamic Island, Control Center, Screenshot
  and advanced glass pages retain their real controls.
- New pages expose actual system/hardware information, storage, application
  associations, login items, audio devices, notification policies, Focus schedules,
  accessibility, opt-in foreground-app activity, accounts, Flatpak permissions,
  keyboard/mouse/trackpad controls, printers, backups and file-server bookmarks.
- Slow queries run in three background threads; mutations are serialized. Only
  the visible Sound page polls devices. Storage scans and update checks require
  explicit clicks. Activity tracking and idle locking are off by default.

## Scope and limitations

Preferences live in `~/.config/lickintosh/core/settings-preferences.json`.
`~/.local/state/lickintosh/settings` contains private restoration records and
optional activity totals. Input overrides restore original compositor options
on rice exit. Autostart, Flatpak and printer-default files are snapshotted and
restored; selected Lickintosh overrides reapply on next entry. Application
associations participate in the existing desktop-profile snapshot/restore.
Settings actions reject writes while another shell is selected.

Network connections, physical audio devices and system updates affect the shared
computer and are identified accordingly. System accounts, hostname and time-zone
configuration remain NixOS-managed and are displayed accurately, rather than
presenting nonfunctional switches. Apple Account/iCloud, Touch ID, Apple
Intelligence, Continuity and Apple hardware services are not emulated. Internet
Accounts provides Linux file-server connections; Passwords and Backup launch
Seahorse and Pika Backup. Printers use CUPS and scanning uses Document Scanner.

Flatpak changes apply to newly started applications. Input options depend on
compositor support. No app or website blocking or browser-history collection is
implemented in Screen Time; the page explicitly describes local app durations.

## References

- https://support.apple.com/guide/imac/system-settings-apda966cb8af/2025/mac/26
- https://www.apple.com/os/pdf/All_New_Features_macOS_Tahoe_Sept_2025.pdf
- https://support.apple.com/en-sa/guide/mac-help/mh15217/mac
- https://wiki.hypr.land/configuring/core/config-options/
- https://docs.flatpak.org/en/latest/flatpak-command-reference.html

## Verification

`python3 modules/lickintosh/settings/test_backend.py` checks validation, typed
Lua configuration, input restoration across compositor instances, exact file
restoration, persistent per-rice overrides, escaped NetworkManager fields,
activity bounds and rejection of unsafe server addresses or cross-rice writes.
The rice-manager suite verifies shell-action isolation and restoration order.
All pages are also loaded and inspected in a separate Settings instance before
building and installing the NixOS generation. Hardware mutations, passwords,
locking, logouts and updates are not triggered during automated page checks.

## Interaction polish

The common slider has an inset capsule track, a refractive pill handle, subtle
highlights and a focus ring; Settings and shell panels share it. Settings cards
have consistent content insets. Explanatory footnotes are available from the
page’s Help button instead of interrupting option groups.

AudioFeedback suppresses both the native OSD and island feedback while a volume
panel or Control Center is open, clears previous audio feedback on opening, and
absorbs late audio events for 450 ms after closing. Settings audio actions also
notify the same gate before applying changes. The Dock input mask and hover
handler follow its visible rounded plate, without an invisible halo above it.
