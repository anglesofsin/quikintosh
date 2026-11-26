# Emoji picker

Super+. opens Quickintosh's emoji panel next to the pointer. The panel follows
the system light/dark appearance. Search supports English and Portuguese names
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
