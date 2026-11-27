# Expanded media revision

References: https://getdroppy.app/features/now-playing and
https://getdroppy.app/features/floating-player . Official images were inspected
as layout references, not distributed as product assets.

`ShelfMedia` is the shared presentation for the dedicated shelf Media page,
expanded activity MediaCard and floating player. Home's small widget retains its
existing composition. The floating Mini mode uses horizontal artwork/metadata;
Player and Lyrics use a portrait cover above metadata, progress, filled transport
and capability-gated volume. Lyrics remains a separately loaded actual provider.
The wrapper keeps the existing close/move/mode controls and native material.
No artwork shader, wallpaper screenshots or extra network poller were added.

Controls use the generated PNG glyphs already reviewed. SF Pro Display/Text,
neutral secondary labels and a thin 5px progress track replace the old animated
radial player composition. Unsupported transport and seek actions are disabled;
volume is displayed only when MPRIS supports it. Demo metadata is read-only.
Position watching is acquired while mapped and released on unmap/destruction.
Seek/volume drags retain the shelf interaction hold.

Validation is kept in the private compositor with a private MPRIS D-Bus fixture.
Source assembly is not deployment. Screenshot and functional evidence must be
recorded before claiming this revision visually accepted or installed.

## Evidence and limits

Private compositor validation covers activity density, Mini, Player and Lyrics
window geometries; MPRIS play/pause, seek availability and volume; editor hold,
collapse and native glass draws without cached frames. Captures and the test log
are stored under `~/.local/state/quickintosh/reviews/droppy-expanded-player`.
The artwork in this fixture is deliberately low resolution; production artwork
uses the MPRIS URL with a 700px decoding limit. Lyrics availability depends on
the real provider, so the blank-when-unavailable preference is preserved.

This is a layout and integration check in a software-rendered nested compositor,
not a host FPS benchmark or a claim of complete Droppy parity. The host shell
has not been replaced by this review build.
