# Decorated maximize and drag surfaces

- ScreenEdges now distinguishes internal maximize (1) from actual fullscreen (2), and subscribes to the shared client inventory while enabled.
- ABI-checked maximize-contour plugin extends only the virtual shader rounding box below the output for tagged maximized windows. Client/layout geometry and upper corners remain intact; it does not resize or crop client content. Scope is the normal output transform (the current display). Rotated outputs retain their existing rounding.
- Dock drag targets update the magnification pointer and drag hover state. External desktop/stack drags no longer disable the lens. Reordering the dock itself retains its previous behavior. Existing transformed dock source is preserved during source-only deployment.
- Drag basket uses ShelfPanelMaterial and the shared smooth contour, with reversible opacity/scale and animated hover/drop highlights. Drag entry accepts a copy action without activating any application. Sharing is only dispatched on drop; KDE Connect provider selection prevents falling back to launching a LocalSend window when KDE Connect is selected.
- Transform uses the same material and places itself at the lower right of its monitor on every opening, fitting smaller displays with margins. This uses the actual Lua monitor object rather than comparing it with an integer ID.

Validation:

- Native private compositor pixel test: upper-left remains background (rounded), both lower corners contain window pixels, internal state remains maximized; restored window exits maximize. Plugin loads/unloads with matching compositor ABI.
- ScreenEdges QML test distinguishes maximized, fullscreen, and fullscreen on another workspace.
- Native drag-surface test exercises actual dock lens geometry through its drag tracking method, captures the basket and Transform, verifies exact lower-right position and no KDE Connect client window. It does not transfer files to a real device.
- Software OpenGL captures validate geometry and QML shaders; they do not validate the host GPU's complete Liquid Glass refraction quality.

Artifacts: /home/pg/.local/state/quickintosh/reviews/maximize-dock/
