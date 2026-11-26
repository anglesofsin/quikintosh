# Shell responsiveness and animated backdrops

This change preserves render limits, animation timing, shaders, materials and
visual geometry. It addresses measured or reproduced work rather than selecting
a reduced-effects profile.

* Icon renderer replies are merged once per event-loop turn. A burst of 1,000
  generated icons retains all results with one reactive map publication instead
  of 1,000. Dock image decoding is asynchronous.
* IPC validates a cached process before scanning `/proc`. PID exit, replacement
  or a different config invalidates that cache; the resolver retains its original
  fallback and does not launch a shell.
* Dock reveal state is released after menus and drops. A bounded recovery check
  runs only while an obstructed dock remains revealed without an active menu,
  stack or drag. Pointer position outside the dock clears stale hover state.
* Reconstructed Liquid Glass now forwards the desktop player's actual video
  frames through Qt's QVideoSink. Backdrops have no independent decoder, playback
  clock, seek timer, screenshot loop or image-file encoding. The implicitly
  shared QVideoFrame retains the video's pixels and timestamps; hidden backdrops
  release their relay. Pausing, looping and changing the wallpaper therefore
  affect the source and glass together.
* Dock occlusion uses one authoritative monitor snapshot, rather than mixing
  workspace identities from different update streams. An in-flight monitor query
  queues a follow-up instead of losing the last change. While automatic hiding
  is enabled, a two-second inventory refresh repairs missed workspace events;
  normal event-driven updates remain immediate.

The native dock compositor path is retained. Reconstructed shaders for widgets
and panels remain the same. A live video layer was verified behind those shaders
in a private nested compositor, without moving any windows.

Diagnostics also found repeated Discord Canary tray property failures and swap
usage. These observations do not establish every source of intermittent stalls.
This change does not hide those diagnostics, restart Discord, clear swap, reduce
video resolution or lower FPS. Long-running live performance still depends on
media decoding, the graphics driver and other host load.

Video forwarding follows Qt's documented [QVideoSink API](https://doc.qt.io/qt-6/qvideosink.html)
and [shared QVideoFrame semantics](https://doc.qt.io/qt-6/qvideoframe.html).
The native test checks timestamps across 120 frames, destination replacement,
source detachment and source destruction. Separate Qt windows still present on
independent render cycles; shared decoding removes playback drift, not the
compositor's normal frame scheduling.

Validation for shared video: Nix build and native CTest passed. A synthetic
30 FPS video was rendered behind glass in a separate Qt layer window in the
private nested compositor. Both sampled regions changed together (glass color
span 442); FFmpeg opened only one video input. Full compiled-shell startup and
the offscreen dock visibility, stale-hover and overlapping-query tests passed.
These checks establish shared playback and recovery behavior, not a universal
zero-latency guarantee under arbitrary host load.
