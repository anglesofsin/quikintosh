# Expanded island contours

The main expanded panel, expanded activity content and floating player now use a shared analytic signed-distance alpha mask. It clips the composited children and background together, including border coverage, in a single device-resolution pass. It replaces the nested rectangle-mask plus 4x multisample layer on the large panel. Clickthrough regions retain their previous behavior.

Notch media uses matching square top corners on its background and content mask. The separate square filler rectangle and rounded goo background are no longer mixed for notch media. Detached media keeps its rounded shape.

Native island glass receives mask_feather=0.16, preserving the alpha transition instead of turning partial coverage into a hard glass boundary. Both the baseline Hyprland declaration and generated custom glass profiles carry the value; other surfaces keep their own settings.

Verification artifacts: /home/pg/.local/state/quickintosh/reviews/smooth-corners/

- rounded.png and rounded-detail.png: native Qt shader capture over a blue background; child content is clipped and boundary pixels have partial coverage.
- notch.png and notch-detail.png: square top corners and smooth rounded bottom corners.
- notch-player.png: actual island activity in notch mode.

The private compositor uses software OpenGL. This verifies QML geometry, shader rendering, input/menu transitions and pixel coverage; it does not establish the quality of the host GPU's refracted background in every situation.
