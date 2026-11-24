# Dynamic Island voice integration

Settings → Dynamic Island → Voice calls controls detection, individual clients,
priority, names, streamer-mode privacy, self/other participants, avatars, speaking
rings, ring animation, visible participant limit and avatar size. Default priority:
Canary, PTB, Stable, Equibop. A preferred client overrides that order when in a call.
Transient notifications and alarms still take priority over the ongoing call.
Call presentation supports automatic media-aware minimization, main-island focus,
and an always-minimized left bubble with the center clock. The bubble shows the
active speaker, falling back to the call picture when nobody speaks. Hover/click
expands it; joining can expand for four seconds. The expanded card shows DM/server
picture, channel name, elapsed time, optional server name and controls.
Elapsed time starts when the renderer observes joining; it cannot reconstruct call
time before the companion was loaded.

Discord receives a renderer companion using its existing mod's common
stores and Flux events. The companion sends only call/participant metadata over a
loopback WebSocket (127.0.0.1:6891). No tokens, messages or audio capture are involved. User-clicked microphone, deafen
and leave buttons route strictly to the displayed session and channel. Multiple clients remain isolated. Disconnect/leave clears
state. Streamer mode hides that client's call by default. Speaking uses Discord's
voice speaking flag, never inferred audio levels. DMs and group calls are included.

The Nix Equicord renderer includes the companion. `install-clients.py` also installs
it into the existing writable desktop mod and Equibop's chosen custom build (or a
preserved copy of its existing ASAR through its supported `equicordDir` setting).
For running Shade managed clients, it preserves the original app entry point and
adds a separate Electron companion after the original bootstrap. Protected assets,
authentication and licensing are unchanged. Each client needs one reload/restart;
the installer does not restart clients. Installer backups are timestamped under
`~/.local/state/nixos-rice/voice-backup`. If a client updater replaces its mod or
managed app entry point, run the installer again. No running process is injected.

Other call apps are detected only when their PipeWire streams explicitly advertise
`media.role=Communication`; arbitrary microphone use is not a call. PipeWire does
not expose remote participants or their speaking flags; those features require the
Discord companion. The PipeWire monitor is event driven, with no audio polling.

The broker runs only while the enhanced island is enabled and unlocked. Linux
parent-death signals clean up both broker and PipeWire monitor if the shell exits.
Avatars are cached, bounded to 80 px; pulse animation is disabled by default.

Validation:

- `node test-renderer.cjs`: channel entry, participant metadata, speaking flags, leave.
- `python test_bridge.py` with the Nix Python websockets environment: schema,
  avatar URL validation, client/account separation, cleanup and privacy metadata.
- Runtime fixture tests exercise the actual island with WebSocket events: priority,
  privacy, visibility controls, expansion and disconnect cleanup. Fixtures are not
  evidence of a real Discord voice call. Verify an actual call after client restart.

Avatar images are fetched asynchronously into `~/.cache/lickintosh/voice-images`
(or XDG_CACHE_HOME), with a 24 MiB / 256-file budget. Previously downloaded photos
work offline and survive shell restarts. New avatar hashes keep the previous photo
while fetching; retries have backoff and no download blocks call-state events.
Self mute/deafen comes from MediaEngineStore local state and change listeners,
rather than waiting for gateway VOICE_STATE_UPDATES. Server mute/deafen is retained.


Update resilience (2026-11-24): the shell runs guard.py every 30 seconds to
check installed managed bootstrap/mod paths and reapply the companion after file
replacement. Unknown bootstrap formats are refused and logged, not overwritten.
The hook handles pre-existing webContents, DOM-ready, completed loads and a
15-second reinjection check. The renderer resolves stores by public mod exports,
store identity and webpack cache, avoiding fixed module IDs. Client identity comes
from the native release channel/hook before the hostname fallback.

A running client is never restarted by the guard. If updates replace a bootstrap,
repair affects the next client restart/reload; no universal immunity to future
Discord API changes is claimed. A running Discord WebRTC duplex pair supplies a
basic external call state if detailed metadata is absent. This fallback contains
no invented participants, avatars or call controls. Native metadata takes priority.
