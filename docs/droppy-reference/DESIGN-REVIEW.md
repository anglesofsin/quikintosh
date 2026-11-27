# Isolated Dynamic Island design review

User requested that this review not be deployed or rebuilt into the host system.
All changes in this review remain in the repository and a mutable temporary
source overlay. The active user shell source is unchanged:
`/nix/store/75zgrw5wc231c2mzwl156w1riy7vp2p7-lickintosh-source-reference-shelf`.

Artifacts: `~/.local/state/quickintosh/reviews/droppy-design-review`.
User-provided Droppy screenshots are the authority for the paired comparisons.
Composites are labelled reference/current and preserve actual captures, with
cropping/resizing for presentation; they are not fabricated UI renders.

Changes under review:

- Explicit trigger toggle with a short close-event guard. Outside-press dismissal
  cannot be mistaken for a request to reopen on the same click.
- Shared menu enter/exit transitions with reduced-motion handling, lighter rim,
  restrained refraction, title/icon corrections and matching file menu behavior.
- Compact surface stays visible until expanded surface presentation begins;
  handover waits two frame callbacks. Repeated right-click/morph tests verify
  ownership and reversals, not every physical display's presentation timing.
- Focus duration has labelled ruler ticks, phase color and 1–480 minute selection.
- Edit completion is blue; editor remains a single shared flow.
- Rename popup no longer dims a rectangular area outside the capsule.

Review coverage: Home, Files, Clipboard, Media, Lyrics, Audio, Weather,
Notifications, Camera, System Stats, Activities, Stay Awake, Widgets and Storage;
expanded toolkit/vault/terminal/voice/ring/selection/job-history views; player
sizes, notch geometry, editor dragging, actual menu clicks and native glass draws.

Remaining differences observed in reference comparisons:

- Many catalogue icons are monochrome while Droppy's widget catalogue has
  colorful illustrations. Existing generated glyphs do not establish identity.
- Card proportions and content density differ across Home configurations.
- Several Droppy integrations have no direct Linux counterpart or require
  external accounts. CATALOGUE.json retains the outstanding scopes.
- Source screenshots have different wallpaper and content; background color
  differences alone are not evidence of an incorrect glass algorithm.
- The audio fixture is explicitly synthetic; private tests do not use host audio.

No full pixel-identity claim or claim of completion of the entire Droppy catalogue
is supported by this review. Test logs and captures distinguish tested behavior
from visual reference matching.

Additional refinements: the player uses a seven-bar meter fed from the existing
Cava stream and only holds it while visible and playing. The source control stays
accessible. Focus ruler uses labelled values and phase accent; audio mode controls
use the reference amber accent. No existing user session was changed.

Evidence from /tmp/qi-design-final-validation.log: actual compact owner repeated
20 morph handoffs and disabled-dashboard behavior; menu trigger open/close/open;
local expanded pages and editor interaction. /tmp/qi-design-audio-validation.log
covers capsule clipping with private synthetic streams. Full 15-page render pass:
/tmp/qi-design-all-refined.log. Final meter iteration is checked separately.


## Player, navigation and mixer refinement

Isolated revision: inline elapsed/remaining times around a 6 px seek track, adjacent lyrics badge, compact navigation (36 px with 34 × 28 px targets), and 0–200% application gain with a midpoint unity marker. Mixer backgrounds use available slider geometry to keep the rounded mask inside each row. The audio fixture contains two synthetic streams; it does not change live application volume. Existing clipboard and context-menu implementation is preserved. The previous 34-screen contact sheet is retained as `all-surfaces-unchanged.png`; it is baseline evidence, not a claim that all 34 screens were reworked in this revision.
