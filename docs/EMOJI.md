# Emoji picker

Super+. opens Quickintosh's dark frosted emoji panel. When the focused app
exposes its caret through AT-SPI, the arrow anchors at that insertion point.
Apps which do not expose caret geometry fall back to the pointer location;
Wayland does not provide a universal cross-app caret-position API. The panel
height adapts to the room above/below the insertion point. Search supports English and Portuguese names
and keywords, including accent-insensitive matching. Categories, recently used
emoji, keyboard navigation, Escape/outside dismissal and skin tones are available.

Selecting an emoji copies its full Unicode sequence and pastes it into the
original focused window after the panel closes. The helper uses Ctrl+Shift+V for
recognized terminals, Ctrl+V elsewhere. If that window has changed or closed,
it only copies: it never pastes into a different window. An application that
blocks paste can still use the clipboard manually.

The Apple Color Emoji font is fetched from a pinned macOS 26 conversion release.
See modules/lickintosh/emoji/SOURCES.md for provenance and Unicode/CLDR sources.
NixOS fontconfig prefers it for emoji. Arch's installer adds a separate reversible
fontconfig snippet without replacing existing user font settings. Apps which ship
their own emoji images (e.g. Discord) control those images independently; already
running apps may need restarting before a font change becomes visible.

Placement uses a warm helper, bounded accessibility calls and no field-text reads.
The panel retains its delegates while closed and releases its input region at
the start of closing. Its transition is 100 ms (scaled by the shell motion setting).
