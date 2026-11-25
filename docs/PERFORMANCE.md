# Runtime performance audit

The audit inventoried 572 QML files and approximately 332 timer declarations in the assembled shell, then reviewed rendering, service polling, filesystem work, queues, cache invalidation and hidden-component lifetimes by subsystem. Declaration counts include conditional and one-shot timers; they are not a count of active polling loops.

## Changes

| Area | Change |
|---|---|
| Liquid Glass | Hidden or inactive glass components stop per-frame coordinate mapping. Retained window captures pause streaming without discarding their last valid frame. Stationary geometry checks retain unchanged objects and avoid republishing the native window model; moving/precision paths remain active. |
| Panel responsiveness | Common panels are built asynchronously in staggered startup batches. Their desktop models and capture delegates survive closing. A serialized preparation queue renders glass/materials while panels are transparent and have empty input masks. Control Center starts its opening animation immediately using the prepared scene. |
| Dock | Capture is prepared at its resting bounds before sliding in as one unit. Internal grid movement transitions stay disabled while the opening layout settles. |
| Capture lifecycle | Closed toplevels are detached immediately. Failed screencopy restarts back off from 80 ms up to 4 seconds, and stop for closed sources. |
| Dock | Identical preview, trash, identity and grouped-app replies do not rewrite models. Filesystem notifications remain immediate; the fallback Trash check runs every 30 seconds. Unrelated shared-data writes no longer refresh recent files. Explicitly pinned shared-data folders still receive their own changes. |
| File previews | At most two thumbnail jobs execute and 128 are pending. Failed files are negatively cached for five minutes or until their fingerprint changes; that cache is bounded to 512 entries. Large Trash listings generate thumbnails only for returned entries. Listing metadata is reused. |
| Application catalog | Desktop entries are parsed again only when their fingerprint changes. Directory/symlink identity participates in invalidation, including Nix generation changes. |
| Widgets | Resource collection follows visible consumers and releases subscriptions for hidden widgets and snapshots. A retired image dropdown no longer launches recursive wallpaper scans. Media widgets and the island share one MPRIS position clock. |
| Audio/privacy | A persistent `pw-dump --monitor` helper merges metadata changes off the UI thread. Only classifier/audio-policy fields are forwarded; unchanged state uses small heartbeats. Disconnects clear state. No audio or video samples are read. |
| Network/brightness | The menu-bar Wi-Fi icon shares NetworkManager state. Bursts of network events are coalesced. Brightness hotkeys keep immediate file notifications; slow hardware polling is a 30-second fallback, with refresh when Control Center opens. |
| Clipboard | Unchanged files reuse cached hashes. Short text previews are read directly, replacing per-entry shell pipelines. The cache stores fingerprints/hashes, never copied text, and is written with mode 0600. |

## Reviewed paths retained

Spotlight/Launchpad already use cached application metadata and virtualized result rows. Wallpaper thumbnails already load on demand with two workers and a bounded queue. Icon generation is cached and idle between requests. Settings queries have freshness/coalescing guards and serialize mutations. Notification delivery, weather caching, theming, screenshot export, Quick Look inspection cancellation, lock-screen loading and compatibility/install helpers were reviewed; unrelated behavior was preserved. Review is not a claim of exercising every hardware-dependent action.

## Measurements and validation

The earlier audit at commit `c301857b` used a controlled private Wayland comparison with the same shell configuration, fake read-only Hyprland metadata and a continuous animation driver. After eight seconds of warm-up, CPU was sampled over eight seconds. This is a desktop workload comparison, not a video-FPS or GPU benchmark.

| Main shell process | Before | Optimized |
|---|---:|---:|
| CPU, percentage of one core | 57.25% | 28.75% |
| Resident memory | 525.66 MiB | 507.95 MiB |

The CPU reduction in that historical scenario was approximately 50%. That measurement predates the responsiveness correction below and must not be presented as a benchmark of the current retained-panel policy. Real consumption depends on open windows, video, calls, drivers and the compositor.

In a separate live metadata check, forwarding the required PipeWire fields reduced a 433,844-byte graph to 23,620 bytes. The unchanged privacy classifier and external-audio policy returned equivalent results on the original and reduced graph, comparing unordered result collections.

The follow-up responsiveness review found that waiting for a new backdrop on each click, rebuilding desktop snapshot models, and switching the prepared Launchpad grid to files made interaction slower. Those paths were corrected. The policy intentionally retains prepared objects and textures rather than minimizing memory at the expense of click latency.

Common panels use an explicit host window, so they can prepare before being shown. Preparation uses the panel's resting capture area, including panels translated offscreen while closed. It is serialized, pauses during interaction/lock, and reruns after relevant workspace/window/wallpaper changes. Video-wallpaper frames do not continually restart preparation. Background resource subscriptions remain suspended while a panel is transparent. The retained-source flag is latched asynchronously: `hasContent` must not be a dependency of `captureSource`, because clearing the source changes `hasContent` during binding evaluation.

The optional `tests/test_panel_responsiveness.py` runs six panels plus Launchpad mode in an explicitly private compositor and temporary HOME. It checks preparation before input, empty hidden input regions, released keyboard focus, two opening/closing cycles, and retained backdrop readiness. It reports first-frame timings as diagnostics, not universal FPS or latency guarantees. Tests with mocked native captures also verify pause/resume without source reattachment and immediate detachment on source close.

Tests cover clipboard hash reuse/invalidation and cache permissions, incremental PipeWire frames/updates/deletions, unchanged geometry polling and its fast path, closed-capture detachment, bounded thumbnails, negative caching and catalog invalidation. The native assembled shell is also loaded in an isolated compositor. Lock/unlock, logout and physical display changes are not triggered by the audit.

Read-only diagnostic commands after installation:

```sh
quickintosh ipc call performance status
quickintosh ipc call dock state
```

The counters expose capture subscriptions and native refresh/query counts, not window titles or clipboard contents.

References: [Quickshell refresh semantics](https://quickshell.org/docs/v0.3.1/types/Quickshell.Hyprland/Hyprland/), [ScreencopyView readiness and stop semantics](https://quickshell.org/docs/v0.3.1/types/Quickshell.Wayland/ScreencopyView/), [Toplevel lifecycle](https://quickshell.org/docs/v0.3.1/types/Quickshell.Wayland/Toplevel/).
