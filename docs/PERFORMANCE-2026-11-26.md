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
* Reconstructed Liquid Glass previously used a one-time video reference frame.
  A visible animated backdrop now uses a muted video source within the same
  shader scene, seeking to the desktop video's position when loaded. It is
  created only while the backdrop is requested; no repeated screenshots or
  image-file encoding are added. Existing video playback/pause preferences apply.

The native dock compositor path is retained. Reconstructed shaders for widgets
and panels remain the same. A live video layer was verified behind those shaders
in a private nested compositor, without moving any windows.

Diagnostics also found repeated Discord Canary tray property failures and swap
usage. These observations do not establish every source of intermittent stalls.
This change does not hide those diagnostics, restart Discord, clear swap, reduce
video resolution or lower FPS. Long-running live performance still depends on
media decoding, the graphics driver and other host load.
