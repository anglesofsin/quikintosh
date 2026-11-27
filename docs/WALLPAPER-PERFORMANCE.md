# Animated wallpaper performance

Alt+F toggles native internal maximization while leaving client fullscreen off.
The compositor retains the layout node and restores it without converting a tiled
window to floating. Opening a new tiled window on that workspace exits maximize;
opening a floating dialog does not. The work area and rounded glass edge are
preserved. Super+F keeps true fullscreen. The maximize shortcut is configurable
through `Toggle maximize`.

Wallpaper pause policy checks each output's visible regular and special workspace,
ignores unmapped/hidden windows and distinguishes fullscreen (bit 2) from maximized
(bit 1). Pausing when maximized is optional and off by default, so transparent
maximized windows keep their animated background. Battery/fullscreen defaults,
original video resolution, source FPS and the material are preserved.

Wallpaper Options → Playback diagnostics enables bounded native measurements only
while the diagnostics are visible. It reports delivered video frames per second,
95th-percentile frame interval, long gaps, dimensions, pixel format and frame
storage. GPU texture storage does **not** prove hardware decoding: software-decoded
frames can also be uploaded to a GPU. Intentional playback pauses reset the sample
window. Ordinary playback collects no timing history and starts no diagnostic timer.
The existing frame relay is retained: glass consumers do not decode another copy.
The unused QML playback-position callback was removed. The statistics observer
is disconnected when measurement is off. Cross-thread video relays keep at most
one pending frame and replace it with the newest arrival, instead of queueing
callbacks that reread the same latest frame after a GUI stall. Source generations
cancel pending frames on replacement/destruction; no pixel readback is added.

Settings communicates with the shell through a short-lived measurement lease and
a one-second state report. The lease expires after eight seconds if the settings
process disappears. Cross-process tests cover starting/stopping the measurement.

## Comparing a separate player

A pinned MIT Anima build is included as `quickintosh-anima` / `quickintosh-animad`.
Its upstream `fast` mpv profile is changed to the normal `default` profile; scaling
quality is not silently reduced. It is not auto-started or made the default player.
The in-process Qt frame-sharing path remains the compatible default: directly
replacing that process would remove the sinks used by client glass. Promoting
another backend requires validating that integration and hardware performance.

`quickintosh-wallpaper-benchmark` compares Qt and Anima on explicitly provided
**private** compositor outputs. It rejects the normal user runtime and host outputs,
uses temporary homes/configurations, disables audio/characters for the comparison,
terminates its own players and never changes wallpaper preferences. Example:

```sh
quickintosh-wallpaper-benchmark --backend qt --video /path/video.mp4 \
  --runtime /tmp/private-runtime --display /tmp/private-runtime/wayland-1 \
  --signature private-instance --seconds 10
```

Repeat with `--backend anima` in the same compositor. JSON reports process CPU
(one-core percentage), RSS/PSS, source metadata, frame statistics and decoder
selection logs where available. Qt counts delivered frames; Anima's status counts
surface commits, which may repeat a video frame. The report distinguishes these.
Software-rendered nested sessions are not evidence of physical-display GPU gains;
no universal speedup percentage is claimed. Video frame delivery also differs from
the shell's displayed frame rate, available under Rendering & Performance.

Reviewed upstream commit: `9272f2eb0741017e336aadfc71f819722e874722`.
Sources: https://github.com/AkerimC/anima (video renderer and Wayland frame loop),
https://doc.qt.io/qt-6/advanced-ffmpeg-configuration.html (hardware selection/logging).
