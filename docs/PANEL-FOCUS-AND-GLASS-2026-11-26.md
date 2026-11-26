# Panel visibility, focus restoration and background work

## Closed and reopened panels

The window visibility binding now remains installed for the full prepared panel
lifetime. Its value follows preparation or real presentation, including exit
animations. It no longer saves/restores a potentially stale visible state.
Preparation also stops overriding child visibility: Qt's effective inherited
`visible=false` could otherwise be restored as an explicit value, leaving a
panel's content invisible after reopening. Prepared models and scene graphs are
retained; closed full-screen panels remain unmapped.

Read-only `quickintosh ipc call panels state` reports presentation and content
visibility without changing focus. The isolated lifecycle test waits for actual
animation progress before checking visible content. Control center reopening was
also confirmed by the user after the stable binding change.

## Layer close must not open special workspaces

Hyprland 0.57's `refocusLastWindow` can restore the last window when a non-keyboard
layer is under the pointer, even if that window's workspace is hidden. Explicit
focus to that window opens its workspace. The bundled ABI-checked compatibility
guard now routes only this automatic hidden-workspace restoration through the
normal pointer refocus path. Exclusive keyboard layers and explicit focus or
workspace commands retain their original behavior.

In an isolated compositor the regression reproduced on three of three panel
closes. With the guard it reproduced on zero of eight; an explicit focus command
still opened the special workspace. Plugin load/unload was exercised there too.
`tests/test_layer_focus_restore.py` requires a private compositor and refuses the
host runtime.

## Recalculate glass only when its background changes

The native glass damage observer now respects layer order. A top/overlay layer
cannot change the background of a normal window, and a layer above another layer
cannot change the lower layer's sample. Unmapped, hidden or invisible-workspace
windows are not dirtied by unrelated surface commits. Window background caching
is enabled with live invalidation; animation geometry and actual background
changes still invalidate samples. The dock's per-render-frame sampling remains.

In a private compositor, a changing top layer caused 116 window cache hits,
zero cache misses and zero blur passes during the sample. A changing background
then caused 147 resamples, and sampled glass pixels visibly changed with it.
`tests/test_glass_background_order.py` checks both caching and live pixels.
No shader parameters, visual geometry, transparency or FPS limits were reduced.

## Diagnose intermittent freezes

`quickintosh ipc call wallpaperVideo monitor true` temporarily enables a video
frame interval counter and a 20 ms GUI heartbeat. `quickintosh ipc call
wallpaperVideo state` reports maximum frame gap, gaps above 100 ms, time since
the last frame and maximum GUI heartbeat gap. Disable with `monitor false` after
measurement. These counters are off by default and do not change playback.

If both counters stall together, investigate the shell/render event loop and
host load; if video stalls while the heartbeat remains timely, investigate the
media path. The observations do not prove every intermittent host stall has the
same cause. A pre-change live IPC sample captured 1,328 ms maximum latency
(100 samples; 52.9 ms median), while builds were running, so it must not be
presented as a controlled idle before/after benchmark.

## Closing panels and dock motion

Panels that own their QML exit animation no longer request an additional
compositor exit animation/snapshot. This rule does not disable their client
animation. The user reported improved Apple/volume panel closing after the live
rule, but earlier intermittent stalls were not fully eliminated by that rule.

Material preparation is now completed once per retained backdrop. Later geometry
and focus events do not remap already prepared panels or repeat `grabToImage`.
Actual live background sampling continues independently; preparation is only for
warming the render resources, not for freezing their texture.

The native dock contour previously shared the generic 33 ms rebuild cooldown.
Its plate moves inside a stationary layer window, so holding the old contour
makes its edge lag behind the current client buffer. Dock content commits now
invalidate that contour without the cooldown. Other layers keep their existing
rebuild policy. This changes neither the glass preset nor its opacity/shaders.
The dock still samples each rendered monitor frame.

The updated retained-panel lifecycle test passed all seven cases (including the
applications grid), twice each, with no material preparation after closing.
The nested compositor uses software rendering and the test ran during a native
build; its frame timings are not a host-GPU performance benchmark.

The native pixel regression passed six shown/hidden dock cycles: each hidden
sample matched the unobstructed background within three RGB levels. The new
plugin also passed the live-background/cache test and the special-workspace
focus regression in the private compositor. These tests do not prove absence
of every transient on the host GPU during mixed application workloads.
