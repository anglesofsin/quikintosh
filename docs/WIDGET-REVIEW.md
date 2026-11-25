# Widget review: macOS and expressive stickers

The review uses Apple's [widget guide](https://support.apple.com/en-in/guide/mac-help/-mchl52be5da5/mac), [Tahoe feature inventory](https://images.apple.com/au/os/pdf/All_New_Features_macOS_Tahoe_Sept_2025_AU_Final.pdf), Meta's [Stories typography engineering](https://engineering.fb.com/2022/07/18/developer-tools/building-text-animations-for-instagram-stories/), [sticker reference](https://about.fb.com/news/2024/05/new-stickers-in-instagram-stories/) and [typographic brand system](https://www.meta.com/design-at-meta/blog/the-new-instagram-brand-identity/). These references guide interaction and visual variety; Quickintosh does not claim Apple's app services or Instagram's social features.

| Widget(s) | Review and resulting behavior |
|---|---|
| Clock / Personal Clock | One Clock gallery category, five designs: analog, digital, classic, stacked and minimal. Existing widget IDs, settings and both renderer types remain intact. Additional installed font choices supplement the original six clock styles. |
| World Clock | Replace fixed cities with per-widget city names and validated IANA zones; select 12/24-hour time. |
| Calendar | Locale, Monday or Sunday week start; optional event preview. Existing calendar-provider data remains the source. |
| Tasks | Optional completed-task visibility; existing interactive completion/add/remove actions retained. |
| Notes | Existing add/delete and content editing retained; new per-widget font choice. |
| Weather | Keep shared configured location; optionally hide the location name and location glyph on this widget. Existing hourly/daily forecasts retained. |
| Battery | Existing battery, charging, time estimates and device/resource views retained; optional typography. No simulated unsupported device batteries added. |
| Now Playing | Existing MPRIS controls, metadata, cover and progress retained; optional typography. |
| Music sticker | Optional cover, independent metadata, card/record designs, fonts and audio policy. Pause local music while an external player is playing. |
| Media | Existing folder slideshows, transitions, GIF/video and fit/shape retained. Video remains animated but its audio is muted while external media plays. |
| Styled Text | Real font variety shared with other editors, alongside existing highlights, effects, alignment and animation. |
| Live Lyrics | Shared installed fonts; existing timed MPRIS/LRC synchronization and optional empty state retained. No fabricated lyric or word timing. |
| Timer | Per-widget minute presets, including fractional minutes; existing start/pause/resume/cancel controls retained. |
| Stopwatch | Existing interactive timing retained; optional typography. |
| Focus | Existing real focus controls retained; optional typography. |
| Quote | Optional user quote and author, falling back to the existing daily quote; optional typography. |
| Volume | Existing output controls retained; optional typography. |
| Bluetooth | Existing device/connection/battery views retained; optional typography. |
| Display, Storage, Activity, Microphone, Shortcuts | Existing real system actions/availability retained; optional typography. No invented macOS equivalent or unsupported integration added. |

## Sound arbitration

The existing PipeWire inventory supplies running **output streams**; MPRIS playback state supplies player events. Input/microphone nodes do not count. The shell's own PID, idle/suspended streams, muted streams and notification/event sounds are ignored. No audio is recorded, no other application is paused, and its volume is never changed.

Both policies start enabled and can be disabled independently in each widget. Local music pauses, preserving position; video keeps its visuals and mutes its audio. When external sound ends, the PipeWire path waits 1.2 seconds before resuming. The inventory refresh interval is approximately one second; MPRIS changes can act immediately. If the inventory becomes stale, automatic widget sound stays suppressed until it recovers. Calls with active output streams also take priority.

## Fonts

The original SF choices remain. Ten additional **SIL Open Font License** families are bundled only with this shell: DM Sans, Sora, DM Serif Display, Space Mono, Marck Script, Anton, Oswald, Bungee, Baloo 2 and Poiret One. They offer modern, editorial, handwriting, mono, condensed, display, bubble and deco directions. They are not renamed or represented as Instagram's proprietary fonts. Each font's license, upstream commit, URL and SHA-256 are in `modules/lickintosh/widget-review/fonts/`.

Font selection is available in text/lyrics typography, music title styling and clock styles. Other text-bearing widgets have a font picker in Appearance. A custom installed family can also be entered. Defaults and existing font choices are preserved.
