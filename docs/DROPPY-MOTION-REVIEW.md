# Island motion revision

The expanded shelf now keeps its Wayland buffer size stable across pages. Only
its clipped body changes size. This removes buffer resize/remap from tab changes.
Page requests are coalesced during the short fade-out; the latest request wins,
and interrupted fade-ins continue from their current opacity.

Opening content waits for the body geometry to settle. Closing fades content
before shrinking the body. The compact surface returns on actual collapse
completion instead of a timer estimated from the animation duration. Reopening
cancels the pending close. Disabling the shelf clears ownership immediately.

Shared-element flights release both endpoints and their spring when cancelled.
A recall cannot restart during a dashboard handoff or when presentation is
suppressed. Large-player springs now respond in 0.32s with a 240ms close; compact activity
content is revealed only after enough surface exists. Live native glass, privacy geometry and
right-click persistence remain in place.

The floating player's opaque mode dropdown is replaced by three matching capsule
buttons. Other shelf choices use a neutral translucent surface and an explicit
Basic control style so platform defaults cannot leak into custom delegates.

Evidence: private nested compositor, all 14 pages, Mini/Player/Lyrics geometry,
MPRIS controls, editor hold, 20 normal handoffs 12 rapid reversed handoffs, and media/call/timer ownership handoffs.
Artifacts live in `~/.local/state/quickintosh/reviews/droppy-motion-review`.
These tests verify transition ownership, settled geometry and QML runtime errors;
they do not prove a universal FPS guarantee under arbitrary host load.
