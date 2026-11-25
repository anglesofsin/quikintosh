# Runtime performance audit

The audit inventoried 572 QML files and approximately 332 timer declarations in the assembled shell, then reviewed rendering, service polling, filesystem work, queues, cache invalidation and hidden-component lifetimes by subsystem. Declaration counts include conditional and one-shot timers; they are not a count of active polling loops.

## Changes

| Area | Change |
|---|---|
| Liquid Glass | Hidden or inactive glass components stop per-frame coordinate mapping. Stationary geometry checks retain unchanged objects and avoid republishing the native window model; moving/precision paths remain active. |
| First visible frame | Control Center begins its opening animation after the backdrop is ready. Dock prepares capture at its resting bounds before sliding in, and retains capture through its closing animation. |
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

A controlled private Wayland comparison used the same shell configuration, fake read-only Hyprland metadata and a continuous animation driver. After eight seconds of warm-up, CPU was sampled over eight seconds. This is a desktop workload comparison, not a video-FPS or GPU benchmark.

| Main shell process | Before | Optimized |
|---|---:|---:|
| CPU, percentage of one core | 57.25% | 28.75% |
| Resident memory | 525.66 MiB | 507.95 MiB |

The CPU reduction in that scenario was approximately 50%. Real consumption depends on open windows, video, calls, drivers and the compositor.

In a separate live metadata check, forwarding the required PipeWire fields reduced a 433,844-byte graph to 23,620 bytes. The unchanged privacy classifier and external-audio policy returned equivalent results on the original and reduced graph, comparing unordered result collections.

Private presentation tests checked that no positive Control Center opening progress precedes backdrop readiness, Dock is presented only with ready glass, capture survives its closing animation, and capture stops while hidden. Dock warm reopening measured about 72 ms in that fixture; cold creation and real window capture add their own costs.

Tests cover clipboard hash reuse/invalidation and cache permissions, incremental PipeWire frames/updates/deletions, unchanged geometry polling and its fast path, closed-capture detachment, bounded thumbnails, negative caching and catalog invalidation. The native assembled shell is also loaded in an isolated compositor. Lock/unlock, logout and physical display changes are not triggered by the audit.

Read-only diagnostic commands after installation:

```sh
quickintosh ipc call performance status
quickintosh ipc call dock state
```

The counters expose capture subscriptions and native refresh/query counts, not window titles or clipboard contents.

References: [Quickshell refresh semantics](https://quickshell.org/docs/v0.3.1/types/Quickshell.Hyprland/Hyprland/), [ScreencopyView readiness and stop semantics](https://quickshell.org/docs/v0.3.1/types/Quickshell.Wayland/ScreencopyView/), [Toplevel lifecycle](https://quickshell.org/docs/v0.3.1/types/Quickshell.Wayland/Toplevel/).
