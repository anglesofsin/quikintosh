# Immediate island tab selection

The old 65ms exit plus 130ms arrival fades delayed every selection. A second
opacity gate hid the contents during geometry changes. Both are removed from tab
switches; opening/closing still retain their coordinated surface animation.
Visited pages are retained, with inactive loaders hidden and input disabled.
Existing camera/media/resource watchers already follow effective visibility.

ShelfIcon no longer clears Image/VectorImage sources when an ancestor hides.
That previously caused synchronous vector reloads on every return, even with
retained page instances. In the isolated software-rendered compositor, 56
synchronous selections all changed the page immediately. After the source fix,
42 repeated selections averaged 0.95ms and peaked at 4ms (previous intermediate
build peaked at 1347ms). These timings measure the selection handler, not
end-to-end presentation or hardware FPS. All 14 page captures, player controls,
editor hold and collapse checks passed; runtime log contained no checked QML
reference/type/load errors. Evidence: `~/.local/state/quickintosh/reviews/tab-response-review`.

## Stable destination layout

Each retained page is now laid out at its destination width/height, centered
inside the clipped animated body. The shell morph no longer resizes all cached
layouts every frame. This prevents GridView column-count changes and repeated
text wrapping during a tab switch. Widget grid cell widths use integer pixels;
weather hourly cells use a fixed layout preference rather than a circular
parent-width preference. The private validation includes rapid returns to the
widget library and final screenshot inspection. No fade delay was reintroduced.
