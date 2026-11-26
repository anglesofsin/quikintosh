# Animated wallpaper diagnosis

Host: AMD Raven graphics, 2 GiB VRAM, 1920×1080 at 240 Hz. The selected video
is H.264, 4096×2302, 60 FPS, 24 seconds, approximately 18.7 Mbit/s.

## Measurements

- No swap pressure: 0 swap used and approximately 9 GiB RAM available.
- A 32-sample live IPC check returned in 44–133 ms. It did not capture a long
  GUI freeze; intermittent stalls outside that sample remain possible.
- All 1,440 video packet timestamps are monotonic after presentation ordering;
  the largest interval is 16.667 ms. The file is not missing timestamp segments.
- The same file was played through Qt Multimedia, including its loop boundary,
  in separate 30-second offscreen tests. Software decoding delivered 1,781
  frames with no frame gaps over 60 ms; VA-API delivered 1,783. CPU time was
  approximately 65 seconds versus 2.14 seconds. The live shell's AMD decoder
  engine counters were advancing: hardware decoding was already active.
- Pausing playback reduced graphics work but did not eliminate the load.
  Enabling only the native window glass cache did not materially improve it;
  that diagnostic change was reverted.
- With all relevant menus closed, the compositor still had 20 mapped shell
  layers. Many were completely transparent 1920×1080 menu/panel surfaces.
  VRAM usage was approximately 1.8–1.9 GiB out of 2 GiB.
- Temporarily disabling panel preparation reduced mapped layers from 20 to 6.
  Median GPU usage changed from 91.5% to 70%, returning to 84.5% when restored.
  VRAM did not immediately fall, so this experiment demonstrates unnecessary
  compositing work, not that all cached GPU allocations were released.

## Correction

`GlassBackdrop` now temporarily maps a panel only while preparing it. Once
preparation finishes, the original window visibility binding controls mapping;
closed panels are removed from composition. Their QML objects, app models,
prepared backdrop and persistent scene graph remain retained. Opening/closing
animations still control visibility through their existing presence state.

The change keeps the original video, resolution, frame rate, materials,
transparency, blur and UI geometry. It does not replace preparation with
construction on click or turn off effects. Live video rendering still has an
inherent cost, and these observations do not establish the cause of every
possible host freeze.

## Applied verification

After activation and shell-only restart, with the original video still playing,
closed panels settled to 6 mapped layers. A six-second sample measured median
GPU usage of 70% (67–72%) and 1,446 MiB VRAM. Shell IPC reported ready, no hidden
window captures were active, and Hyprland reported no configuration errors.
The isolated lifecycle test exercised all six panel types and Launchpad twice;
prepared scenes survived closing and reopening. Its first control-center opening
was slow (886 ms) under the software-rendered nested test; subsequent measured
openings ranged from 13–138 ms. This does not prove all interaction latency or
intermittent live freezes have been eliminated.
