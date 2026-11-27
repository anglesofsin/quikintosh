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


## Follow-up: lyrics alignment and icon badges

Lyrics badge follows the rendered title width with a 7 px gap and vertically centered glyph; intrinsic text width replaces a separate font-metrics estimate. Remaining vertical space goes between metadata and the seek row, keeping transport controls near the bottom. Icon and badge are centered as a group with a 4 px gap, and tray buttons grow for additional digits. New transparent AI tray and microphone assets have measured alpha bounds; the microphone has no sound waves. Targeted native player/menu review passed (20.031 s); synthetic audio review passed (36.906 s). Updated player, navigation and audio comparisons were visually inspected; no activation was performed.


## Reference glyph and typography correction

Time labels use 13 px SF Pro Text Medium with tabular figures; artist uses 16 px SF Pro Display Medium. Re-generated laptop and inbox from the user-supplied reference crops using built-in image_gen, preserving transparent negative space and measuring alpha bounds for centering. Unselected navigation glyphs and the floating-player laptop use secondary foreground. Native player/menu test passed in 27.088 s; player/navigation comparison images visually reviewed. No live activation.


## Textbox-only refinement

Teleprompter, Quick Terminal, transcription and Markdown vault share ShelfTextArea: translucent neutral fill, fine rounded border, 14/12 px horizontal/vertical padding, explicit legible placeholders, focus/selection states. Existing terminal monospace and all widget actions remain. A focused native isolated test captured all four surfaces and executed the terminal input/output fixture successfully (11.534 s). The broader utility run encountered an editor state left open after the context-menu trigger sequence; that unrelated sequence is not claimed as passing in this revision. Preview: textboxes-refined.png. Reference consulted: https://getdroppy.app/docs/droplets/teleprompter (documentation does not supply pixel specifications for these four textboxes).
