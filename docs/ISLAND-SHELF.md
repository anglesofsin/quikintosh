# Island shelf

Right-click the island to open its shelf. Home combines the chosen modules;
Widgets opens a visual editor with a catalogue, four selectable positions, width presets, ordering controls and an Appearance tab. The editor stays open until Done or Escape; ordinary shelf pages still collapse after leaving. Menus and sliders temporarily suspend collapse. Settings → Dynamic Island starts with illustrated Dynamic Island/Notch choices, materials and dimensions. Arrange on shelf exposes drag
handles and width handles; Done leaves edit mode. Files accepts local file drops.
Removing files from the tray only removes references, never originals. ZIP and
converted static images are new uniquely named files in Downloads. Pinned
references survive Clear. Large or animated conversions report an error instead
of silently changing media semantics.

The external-link controls open the independent player or file tray. The player
has Mini, Player and Lyrics layouts. Lyrics use the same provider as desktop
widgets; unavailable lyrics are blank by default. Audio exposes PipeWire playback
streams; only explicit slider/mute input changes their audio. Stay Awake creates
a timed idle inhibitor and releases it on expiry, Stop or shell exit.

Dynamic Island settings include display shape, shelf dimensions/material,
optional hover opening, hover/collapse delays, animation duration, navigation,
widget choices and widths, player size and blank lyrics. Reduce motion and reduce
transparency retain precedence. Fullscreen privacy and lock visibility remain
owned by the existing island. Independent windows close when the session locks.

## Local integration

A local tool may publish a bounded, expiring activity without executing code in
the shell:

```sh
quickintosh ipc call shelf activity '{"id":"my-build","title":"Building","subtitle":"Compiling sources","progress":0.45,"ttl":60}'
quickintosh ipc call shelf open 11
quickintosh ipc call shelf activity '{"id":"my-build","remove":true}'
quickintosh ipc call shelf status
```

The API accepts at most 32 activities. Titles/subtitles and duration are bounded;
progress is clamped to 0–1. Activities expire instead of leaving stale build
status after their producer exits. No subprocess commands are accepted as action
payloads. Activity cards appear on the Activities page; this API does not claim
automatic integration with all coding tools.

`addFiles` accepts a base64-encoded JSON list of absolute paths/file URIs. `open`
accepts page ids 0–12. Files and clipboard workers run separately from rendering;
there is no global directory crawl, screen capture loop or idle clipboard scan.
The tray stores references under `~/.local/state/quickintosh/island-shelf` with a
private directory and atomic writes. Clipboard reads the existing Spotlight store.

See [research and parity ledger](research/DROPPY-2026-11-26.md) for platform limits.

Animated wallpaper palettes use the first decoded video/GIF frame, cached by file
path, modification time and size. Wallpaper Options includes playback enable,
pause on battery and pause in fullscreen, plus Restore playback defaults. Defaults
retain playback enabled, pause on battery disabled and pause in fullscreen enabled.
No frame-rate limit or resolution reduction is added by default.
