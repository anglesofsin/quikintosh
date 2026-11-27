# Media and expanded surface polish

The shared expanded dashboard now renders its rounded body through an antialiased multisampled layer. Home widgets clip to their own rounded cards only when cards are enabled, preventing accidental clipping of calendar headers and explanatory footers in the unframed layout. Activity subtitles tolerate absent optional data. Battery detail excludes disconnected or invalid unnamed entries rather than displaying empty device rings.

Now Playing hides the audio meter when playback is paused and uses ArtTint to derive its color from the current cover. Calendar separates the red weekday and white date, with the month red and today highlighted. Generated replacement PNGs provide white Home, Tray and Widgets symbols and a white laptop with silver screen fill; optical bounds center the unmodified generated bitmaps at 16/24/32px.

Playing Next includes the active player header and transport, followed by actual upcoming tracks. MPRIS metadata is ordered according to TrackList rather than the arbitrary order returned by GetTracksMetadata; current and preceding entries are excluded from the displayed upcoming section. Player metadata changes and list changes refresh the queue. Visible observers share the subscription, avoiding a hidden/closing component disabling another visible queue. Refreshes reuse existing subscriptions.

Floating Player keeps three sizes, a square cover, inline Playing Next, synced lyrics and audio controls, volume, shuffle/repeat options, and an album-derived bottom gradient. The cover plays supplied GIF/WebP/APNG artwork while playing and pauses when hidden or paused. The integration does not obtain Spotify Canvas videos; animated art remains dependent on what the source supplies. Existing LyricsState remains responsible for available synced/plain lyrics.

Screenshots always present the existing transient expanded screenshot card, including its incoming animation, even when other events have auto-expansion disabled. The expanded screenshot does not linger as a separate compact activity.

## Spotify queue integration

An optional Spicetify extension reports only upcoming track metadata to an authenticated loopback HTTP endpoint. It never reads or transfers Spotify credentials. The endpoint binds 127.0.0.1, restricts origin and request size, authenticates with a per-user bridge key, and expires snapshots after 15 seconds. MPRIS still controls playback; selecting a Spotify item uses its URI through OpenUri. The Spotify bridge queue is read-only for editing.

This machine had an installed Spicetify CLI but a stale missing mutable Spotify path. A local copy of the already installed Nix Spotify runtime preserves its existing Default theme; only the queue extension is injected. The local launcher and user desktop entry select that runtime. Existing Spicetify extension settings are retained. Backups are in `~/.local/state/quickintosh/island-shelf/`. The local bridge key is not part of this repository or the Nix store.

The real Spotify process was reloaded and playback state restored. Production IPC confirmed provider `spicetify`, supported true, 40 upcoming tracks. No account credentials or private track content were copied into tests or documentation.

## Validation and artifacts

- Private native compositor: 20 expansion/collapse cycles, 12 interrupted reversals, media/voice/timer handoff, screenshot with auto-expansion disabled, 14 primary tabs and 18 widget detail views. No uncovered handoff frames.
- Native media fixture: playing/paused, real MPRIS queue, calendar, battery states including invalid/disconnected devices, icons at real sizes, six floating-player size/content combinations; mouse activation of queue toggle, lyrics and outputs.
- Real private D-Bus TrackList add/remove/jump and delayed TrackAdded notifications.
- Four bridge tests: normalization/scope/expiry, installation idempotency, rejected malformed snapshots, actual authenticated loopback HTTP with origin/token checks.
- 46 native captures and side-by-side reference comparisons: `/home/pg/.local/state/quickintosh/reviews/media-polish/INDEX.md`.

References: https://getdroppy.app/features/floating-player ; https://getdroppy.app/features/playing-next ; https://spicetify.app/docs/development/api-wrapper/properties/queue . Test fixtures are isolated; a successful screenshot does not establish parity with every Droppy feature or all player/provider combinations.

## Follow-up — prepared only, not activated

User requested no live activation. The follow-up removes the media expansion stroke and glow, fixes expanded media content to its final target geometry throughout the surface morph, and normalizes the transparent margins of existing AI-generated PNGs so tint effects cannot clip translated artwork. ShelfButton fits artwork inside a padded content box. Focus start/reset buttons use explicit equal dimensions and the existing generated reset symbol. The exact supplied laptop bitmap replaces the previous generated laptop; the export's low interior alpha is restored to opaque white while retaining its silhouette. Navigation now correctly selects the already generated bold Tray/Widgets assets.

Floating Player uses the shared live ShelfPanelMaterial with a black-to-transparent covering gradient, instead of a color sampled from album artwork. Private tests can validate composition and interaction; hardware screencopy is unavailable in the software nested compositor and uses the material fallback there. No live shell restart, application restart or system activation was performed for this follow-up.

## Staged island choreography and player follow-up

Prepared only; no live activation for this follow-up. A 560ms reversible presentation timeline derives distinct core, left/right activity and privacy phases. On hiding, lateral activity retracts before privacy fades/moves right and the core contracts; showing grows the core before sequential left/right detachment and the final privacy fade. Side activity springs use a 380ms response and increased damping. Reduced Motion bypasses the timeline duration. Privacy handoff also fades instead of disappearing through an instantaneous visible change.

Media appearance waits 2000ms after playback begins; loss of player or pause cancels the pending arrival. Existing manual playback controls remain immediate. ShelfMedia, shared by compact expanded content, Home, Queue and Floating Player, adds a clipped, hover-only looping title marquee with a resting pause. The lyrics badge remains immediately beside the visible title viewport.

The media expansion excludes Sheen and IslandRim, in addition to the previously excluded stroke/glow. Floating material and its clipping parent share a 28px corner radius; backdrop scale is at least 1 and blur scale at least .5 to avoid coarse sampling. This changes the rendering configuration but private software tests cannot verify every hardware pixelation case.

Screenshot compact content is explicitly hidden and its filename cleared from the compact label, while the expanded screenshot card and incoming animation remain. The capture fallback no longer creates a generic filename notification inside an enabled island when the screenshot activity is disabled. If the whole island is disabled, the existing external notification fallback remains.

The laptop's original supplied interior alpha is preserved, undoing the previous opaque-white interior. The toolbar tray uses the user's `Minimalist White Inbox Tray Icon.png`, normalized only to its optical bounds; the original remains untouched.

Validation: native stage phase ordering at 0.6 and 0.95, 20 full handoffs and 12 interrupted reversals without uncovered frames, explicit screenshot compact-label/visibility assertions, native hover marquee motion, all floating player modes and queue/lyrics/output controls. Captures remain under the media-polish and player-final-polish review directories. The hardware glass path is not fully exercised in the private software compositor.

Further native checks exercise the 2-second arrival against a private real MPRIS player (still absent at 1 second, present after at least 1.8 seconds). The material excludes Quickshell's own PID from the window capture inventory, preventing the floating player from feeding its own glass back into itself. This is a concrete self-capture prevention fix; reproducing every reported pixelation case still needs the real GPU capture path.
