# Droppy reference implementation audit

Reference authority: user screenshots 1–23, getdroppy.app/features/file-tray,
/features/now-playing, /features/audio-control, /features/notifications,
/features/cleaner, /docs/transform, /docs/shelf. Research media stays outside Git.

Acceptance matrix:
- [x] Right click: one click opens; second closes; empty activity never cancels it.
- [x] Files: 4 columns, blue selection, thumbnail/name/metadata, round toolbar.
- [ ] Files: pin, tracked folder, safe ZIP extraction, rename, folder drops.
- [ ] Files: outbound URI drag, external URI drop, preview, copy, remove references.
- [ ] Transform: local compression, conversion, resize, rotate, metadata removal,
      PDF merge from images, ZIP; non-destructive outputs; controls typed.
- [x] Clipboard: category tabs, colored/image cards, pin/remove, search/copy.
- [ ] Home: inline editor/catalogue, remove/reorder/resize, real widgets.
- [x] Audio: output/input tabs, per-stream sliders, reset, icons and mute.
- [x] Storage: actual capacity/usage and bounded local-cache cleanup.
- [x] Notifications: sender/icon/image/actions/reply when advertised by app.
- [x] Media: artwork, elapsed/remaining, transport, lyrics/source controls.
- [ ] Both island/notch geometries; native live material and reduced motion.
- [ ] Runtime/private fixture, backend operation tests, screenshot comparisons.

Platform boundary: no fake AirDrop, Droppy Cloud, iCloud or Apple Music private
APIs. Show installed Linux sharing providers only when available. No automatic
uninstall or deletion of user originals. Notification reply is possible only
when the sending app exposes an inline reply action.

Checks indicate an implemented/validated capability, not pixel-identical parity.
See VALIDATION.md for test scope and remaining gaps. Drag gestures and every
platform integration have not been established by backend tests alone.
