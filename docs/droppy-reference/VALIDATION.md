# Native surface validation

The review runs on a private, nested Hyprland display. It does not inject input
into the user's desktop or use the user's Discord profile. Screenshots and
recordings are written to `~/.local/state/quickintosh/reviews/droppy-reference-review`.

Validated in this revision:

- Fifteen expanded pages load, including Files, Clipboard, Audio and Storage.
- Switching pages updates the selected page synchronously; visited pages retain
  their components. Each page lays out at its destination size during the outer
  capsule morph, rather than reflowing at every intermediate width.
- The widget editor keeps the shelf open after the pointer leaves.
- Actual MPRIS transport and volume requests reach the isolated test player.
- Native glass renders without reading a stale layer-cache entry in the fixture.
- Nine temporary-file tests exercise archive/extraction, path traversal rejection,
  folder copying/collision handling, rename/collision handling, reference-only
  removal, tracked folder arrivals, image resizing, PDF generation and storage.

The screenshot review caught a Transform placement race; placement now retries
until the compositor has mapped the window, with a bounded retry count.

This is not a claim of pixel-identical parity with every Droppy screen. In
particular, global drag shaking outside Quickintosh, proprietary Apple sharing,
background removal and arbitrary video/PDF transformation are not implemented
by this patch. Transform currently operates on local images and ZIP archives.
Reply depends on the sending application's freedesktop inline-reply capability.
Do not represent a synchronous tab-selection benchmark as a display-frame or
end-to-end latency benchmark.

Additional evidence: the actual compact owner passed two synthetic right clicks
on its private window, 20 expand/collapse cycles and 12 interrupted reversals.
A fake notification sender received the exact text submitted through the reply
field; no message was sent to another person. Transform placement was asserted
as a floating 414×680 window; the action footer is outside its scrolling content.
