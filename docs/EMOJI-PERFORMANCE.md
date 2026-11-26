# Emoji panel validation — 2026-11-25

Validated in an isolated nested Hyprland session with software rendering; no
keyboard/mouse events were sent to the user's desktop. The same QML and helper
sources are installed by the bundle.

- 30 consecutive open/close cycles: completed without a stuck panel.
- 20 further cycles with the warm placement worker: completed without a stuck
  panel; internal placement median 24.5 ms, maximum 36 ms.
- External end-to-end test commands (including launching IPC clients, querying
  state and software rendering): median 226.9 ms, p95 256.6 ms, maximum 333.8 ms.
  These numbers are not the widget's frame time or a native GPU benchmark.
- The visual transition is 100 ms at normal motion scale. Input closes immediately.
- English/Portuguese search, skin-tone selection and insertion into the previous
  test field passed. The inserted full sequence was U+1F44D U+1F3FD (👍🏽).
- Accessibility unit test verifies the focused field's screen extents and that
  placement never requests field text. The current user's application did not
  expose a caret during the read-only check, so pointer fallback was used.
- Catalog/clipboard/accessibility tests: 4 passed. Arch activation tests: 10 passed.

No finite test establishes zero lag for every application, GPU, scale factor or
system load. Unsupported app accessibility cannot yield an exact caret position.
