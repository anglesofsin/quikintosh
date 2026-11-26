# Finder, GTK and wallpaper colors

Appearance → Finder & GTK has two independent switches, both off by default:
wallpaper colors in Finder/GTK applications, and wallpaper colors for folders and
compatible file icons. Both use the existing Matugen light/dark palette. GTK
keeps the Tahoe layout and glass sidebar; an overlay changes its named colors.
The icon overlay inherits the selected MacTahoe theme and recolors only blue/cyan
material in existing SVG places/MIME artwork, retaining paper, gradients, glyphs,
other color badges and explicitly named alternative folder colors. Application
logos and thumbnail contents are unchanged. Finder and the desktop use the same
generated sources. Turning the switches off restores the original Tahoe themes.

Generated themes alternate between two managed names to notify toolkit caches;
unchanged palettes reuse cached output. The current palette manifest updates the
shell icon resolver without generating work per frame. No source artwork in the
Nix store is edited. Missing or invalid palettes fall back to the original theme.

SF Pro Text is the interface default for GTK/Qt and proportional font fallback;
SF Mono is the monospace and terminal/editor default. SF Pro Display/Rounded
remain available for specialized interface typography; emoji and symbol fonts
are preserved. Fonts are installed system-wide from the existing bundled files.
Apps that implement their own typography or webpage CSS can override system
fonts; this does not rewrite website content.

Validation: opt-in/off, light/dark, unchanged-cache, invalid-palette and color
preservation tests; real installed artwork generated 208 compatible icon names
in approximately one second in a temporary home. Editor JSONC font changes
preserve comments and unrelated preferences. Runtime checks are recorded below
when activation completes.

SVG compatibility correction: replace only color attribute/style values in the
original SVG text, preserving its namespaces, gradient references, filters and
serialization. Do not serialize an ElementTree with generated namespace prefixes.
Bump the generation schema to invalidate old overlays. GTK 4 icon-theme lookup
was exercised directly and selected the generated regular folder SVG; a rendered
preview retained its original lit gradient. Desktop profile IPC now discovers the
standard session D-Bus address if absent from its launch environment, so theme
changes reach running GTK applications as well as configuration files.

Tinted style integration: selecting the existing global Tinted icon/widget style
also enables the shared wallpaper-colored file-icon overlay. Previously that
style went through the shell's app-tile material renderer while GTK stayed on
its original blue folder theme. File icons now use the same recolored original
artwork in both locations, bypassing the dark app-container shader. The separate
GTK interface-color switch remains independent. Outside Tinted, the explicit
file-icon switch retains its existing opt-in behavior. WallpaperTheming watches
the effective choice so changing style applies/restores GTK's icon theme.

Tinted GTK accents: Tinted synchronizes the original Tahoe accent rules too,
without requiring the separate full-interface palette switch. The base theme
contains hard-coded `#0088FF` declarations for sidebar links, selection outlines
and other controls; emit narrowly scoped overrides replacing only these color
declarations with the palette's accent. Preserve other properties and base
resources. The full GTK switch still controls surface/background colors.
Validation: generated GTK 4 stylesheet loaded through GtkCssProvider with zero
parsing messages; targeted accent replacement tests pass.
