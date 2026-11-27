# Droppy page-by-page visual audit

Visual authority: the user's selected Droppy references and black/Fade surface,
not a generic web design recipe. SF Pro remains the font. Do not replace it with
fonts recommended by generic skills. Desktop mouse/keyboard density takes
precedence over mobile examples in installed skills.

49 design skills are installed locally; source paths are in DESIGN-SKILLS.json.
Applied workflows: Qt UI Design, Icon System, Critique Typography, Spacing
System, Design QA Checklist. Qt's deterministic QML lint is used as a separate
code check. Third-party design scripts are not authority to change the user's
references, install web runtimes or restart the user's graphical session.

| Page | Observed mismatch in previous capture/source | Revision / verification required |
|---|---|---|
| Home | Narrow metadata, outline navigation, inconsistent playback silhouettes | AI-generated PNG navigation/playback; title/artist/time scale and progress thickness compared at native size |
| Media | Old four-column panel with separate sound card | Reuse the compact actual media composition; remove unrelated card; capability-gated real controls |
| File tray | Dark boxes around thumbnails, bulky action text | Transparent thumbnail tiles, compact actions, 176px cells; originals stay untouched |
| Clipboard | Vertical text rows; image/color content not presented as cards | Horizontal 220px preview cards, type header, length metadata, real search and copy |
| Widgets | Catalogue and editor previously mixed | Separate icon grid and four-slot editor; use one spacing/color/type system |
| Calendar | Centered three-day widget rather than events | Date/week header, semantic event blocks; month grid for wider layout |
| Weather | Old three-column forecast; scattered scales and very large art | Compact current/hourly card and separate weekly row; actual availability and locale formatting |
| System | Four unrelated resource columns | CPU and RAM with live rings, histories and actual values; resource watch only while visible |
| Audio | Full-width text buttons and long sliders | Compact filled volume rows and mute affordance; actual PipeWire streams |
| Notifications | Nonuniform headings and dismiss control | Shared typography, rounded stack and icon-only accessible dismiss; real actions retained |
| Camera | Explanatory cards and preference toggle inside preview | Single preview/empty state and explicit camera start; stop on page unload |
| Lyrics | Centered thin text and harsh dark inactive lines | Shared SF Pro scale, left-aligned primary line and quieter neighbors; blank option preserved |
| Focus | Old reset/play/skip cluster | Focus/Break, duration ruler and actual timer state; no fake ticking data |
| Notes | Old mixed form nested in Home | Compact saved-note list and dedicated editor; preserve unfinished edit by holding island open |
| Stay Awake | Unrelated large heading and controls | Shared tokens; actual idle-inhibition actions and failure message retained |
| Live activities | Generic dark list boxes | Shared transparent surfaces/type/icons; actual available sources only |
| Floating player/tray | Gray translucent backing unlike island | Neutral transparent base; remaining vertical media/lyrics composition comparison still required |
| Command Center | Not yet present as a local island page | Existing Control Center is not claimed to be Droppy Command Center; still a separate plan item |

## Acceptance evidence

Each actual page must load without QML errors, overflow or missing icons. Capture
at native logical size, compare with its own official reference, and test empty,
loading and populated states where relevant. A montage is a navigation aid, not
proof of visual equality. AI output is not pixel-identity evidence; inspect each
PNG at its displayed size. Do not claim the complete design identical while
unreviewed states or missing functions remain.

## Image assets

The PNGs in `modules/lickintosh/island-shelf/icons/ai/` are generated with the
built-in image generation tool, with transparent backgrounds. Existing PNGs
are copied intact; no procedural SVG/Canvas drawings substitute for these new
icons. Sources/prompts are recorded in `icons/ai/provenance.json` before delivery.
Temporary official screenshots are research references, not distributed assets.

## Optical icon correction

PNG canvas dimensions are not glyph dimensions. The generated pause canvas is
1536 × 1024; most other glyph canvases are near-square. The first raw-image
comparison exposed a pause only about 18 px high despite a 34 px nominal item.
`ShelfIcon` now centers/scales the visible alpha bounds (threshold 128) while
preserving image aspect ratio and leaving every generated PNG unchanged.
Playback targets are 38 px wide for previous/next and 36 px for play/pause;
navigation targets are 16 px. The pop-out laptop is also an AI-generated PNG; four transport actions now share an evenly spaced row. Each asset decodes at its DPI-scaled display size,
not at its full source resolution. The primary Home title is 22 px, artist 18 px,
and time labels 14 px. These measurements are review targets, not proof of
pixel identity with every Droppy state.

The private render fixture installs its own icon-search paths and Qt6ct theme
configuration. A nonempty system-file icon is asserted before captures, so an
isolated test HOME cannot silently make a file tile look incomplete.

Final optical candidate: all thirteen pages, three widget details and editor captured; surface regression passed with 1,928 native draws and zero layer cache hits. The private hardware services are intentionally unavailable: camera/audio populated device states still require separate validation. This is not full Droppy feature/design parity.
