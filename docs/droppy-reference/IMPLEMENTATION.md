# Droppy reference implementation audit

Reference: https://getdroppy.app/features, reviewed 2026-11-27, and user-provided
screenshots. CATALOGUE.json inventories all 71 feature routes found on the page.
A status of implemented-core means the underlying local capability exists;
it does not claim full design or functional parity with the named product.

Implemented local capabilities:

- Persistent right-click shelf, left-click activity expansion; explicit ownership.
- Nautilus/Finder services forward explicitly selected local files to the island
  or floating tray; personal scripts are preserved.
- Files: round toolbar, selection, thumbnails, dimensions/text previews, pinning,
  tracked folders, Quick Look, ZIP/extract, rename, folder copy and native URI drag.
- Global native drag shake opens a cursor-positioned four-target basket. Targets
  add to tray, transform, open files or share through installed LocalSend.
- Transform: images, bounded FFmpeg video conversion/FPS/resize/compression,
  PDF merge/compress/rotate/extract/render, metadata removal, local background
  removal, presets and batch rename. Originals are preserved.
- Clipboard category cards, search, pinning, copy and remove.
- Home inline catalogue, actual slot drag reorder, width adjustment and cancel.
- Searchable Command Center with favorite controls, three grid densities and
  actual launch actions for Calculator, Emoji, Spotlight, applications and Settings.
- Output/input per-application audio, live disk usage and app inventory.
  Explicit uninstall supports user Flatpaks/local shortcuts; Nix apps are read-only.
- Notifications with images, advertised actions and native freedesktop inline reply.
- MPRIS player transport, source choice, seek, volume, lyrics and floating variants.
- Real calendar, notes, focus, weather, stats, camera and idle inhibition widgets.
- Action Ring: single/double/triple layouts, 18 selectable local actions,
  cursor placement, explicit click or paired press/release activation. Default
  Super+Alt+R is installed only when free; existing bindings are preserved.
- Local MCP stdio bridge with separate UI/files/activity permissions, bounded
  requests and no network listener or arbitrary command execution. See MCP.md.
- Quick Terminal runs explicitly submitted commands with bounded output, a stop
  action and a complete terminal launcher for interactive sessions.
- Developer tools: offline JSON/Base64/URL/JWT inspection/UUID/SHA transformations.
- Configurable break reminders, disabled initially, suspended during calls/DND.
- Teleprompter: editable saved script, scrolling speed, text size and mirror mode.
- Explicit Markdown vault selection, read/write and external-edit conflict checks.
- Shared context menus: captured live backdrop, icons, blue selected rows,
  separators and real media-source submenu.

Remaining catalogue work is recorded without concealing it in CATALOGUE.json.
The catalogue extends beyond these modules: action ring,
transcription, translation, account integrations, agent hooks and advanced
Command Center layouts still need implementation or integration review.

Platform boundaries: do not impersonate Droppy Cloud/iCloud/AirDrop or invoke
private Apple APIs. Third-party accounts need a supported provider and user
credentials; no credentials are discovered or copied from app profiles.
Notification reply requires support from the sender. Destructive operations are
never automatic. A compatible Linux alternative is not labelled pixel-identical.

Voice transcription uses local whisper.cpp with the multilingual base model.
Recording is explicit (maximum 60 seconds); file input is normalized locally and
limited to the first five minutes. The microphone job is cancelled on lock or
when its recording view becomes hidden. Temporary audio is removed after work.
Language selection includes automatic, Portuguese and nine other choices.
No audio is uploaded. This does not establish word-perfect transcription.

Personalization uses one inline Home editor from both the pencil and context
menu. Catalogues begin in a deliberate common-use order, then recently used
widgets move to the front. Existing Home slots never reorder automatically.

Playing Next reads the selected player's actual MPRIS TrackList, subscribes to
track events and supports jump, add and remove when advertised. Standard MPRIS
does not define arbitrary queue reordering; no private Spotify API is assumed.
Selection Actions is opt-in; its primary-selection text is transient. Copy/Search
work locally and external search happens only on an explicit click.

Tasks & Agents provides an explicit local job runner and bounded summary history.
Use `quickintosh-run --title "Build" -- your-command`; progress appears in Live
Activities. Interactive agents keep their caller TTY. It does not scrape private
Claude/Codex histories or claim model-token/cost statistics. Exit summaries store
only a chosen title, duration, status and completion timestamp (last 200 jobs).


2026-11-27 follow-up (isolated source; not activated): KDE Connect paired/available device selection and explicit recipient validation with LocalSend fallback; separate 424×470 glass share surface. Backend recipient tests use mocks and never transmit files. Teleprompter imports bounded TXT/MD/PDF/DOCX locally, supports persisted 60–300 WPM, text size/mirroring, and Wayland display idle inhibition while reading. Voice-following/fullscreen exception remains pending. Developer transformations now include HTML/hex, sort/deduplicate lines, counts and UTC timestamps. This is incremental work, not complete feature or visual parity.

Quick Translate: optional explicit Google/Translate Shell online request, ten target languages, original editor/result card, cancel and copy. Source text goes via stdin; no request occurs on selection alone. Worker timeout and process-group cancellation bound provider work. Private QML flow translated the public phrase Good morning into Bom dia; three mocked backend tests cover input validation, stdin routing and provider failure. Local inference, replace-selection and standalone shortcut are pending; no equivalence to Apple Translation is claimed.
