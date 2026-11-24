# Tahoe icon renditions and material schemas

Light and dark resolve immutable downloaded files. No inversion or procedural
light/dark conversion is performed. The Apple system artwork is mirrored by
MiaowCham/macOS_Tahoe_Themes_for_MDF, which attributes its official directories
to Apple's macOS Tahoe Design Resources. Linux application counterparts use
Scrimas/MacOS-Like; those are adaptations, not Apple originals. Both repositories
are revision/hash pinned in rice.nix. bank.py indexes their aliases separately.

Tinted and Clear use persistent fast-renderer.py, with Pillow/NumPy/librsvg.
Native monochrome renditions supply surface relief for Apple system icons.
For authored SVGs, explicit container/shadow/rim geometry is separated from
foreground geometry before rasterization. Flattened sources use a contrast mask
fallback. Alpha, foreground, shadow, rim and directional-relief fields are stored
once as a versioned material schema; palette-only changes recomposite those fields
in linear light. No Chromium, WebGL or network service runs at runtime.

Dock, Launchpad tile, application grid, desktop and Spotlight share one reactive
resolver. Palette, appearance and style changes invalidate the output key. Old
queued jobs are cancelled, and stale results are never activated. Generated files
stay cached and original/native icons remain visible during the first preparation.
System symbols and media thumbnails are excluded. Desktop names and aliases are
normalized. This remains an independent compositor, not Apple's proprietary one.
