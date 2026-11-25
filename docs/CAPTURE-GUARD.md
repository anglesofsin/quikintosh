# Captured-window close race

Quickintosh loads `quickintosh-capture-guard` with the matching Hyprland 0.57 bundle. It corrects a legacy toplevel-export protocol race: a capture request can arrive after its window disappears. The host otherwise returns without creating the request's new frame object. When the client releases that ID, Wayland disconnects the entire shell with `invalid object`.

The guard creates an inert failed frame and retains it until its client destroys it. Valid captures use the original implementation. No rendering, frame rate, animation or capture permissions change.

The host compiler inlines the exported capture member into its registered request callback. The guard therefore resolves that callback's unique ELF function symbol, verifies the compositor ABI, and installs the hook through Hyprland's hook API. It refuses an unknown or stripped binary rather than guessing machine-code offsets. Protocol callbacks remain mapped across manual plugin unloading, so outstanding client resources do not become dangling callbacks.

This compatibility fix can load into an existing matching session. It does not restart the compositor or interrupt calls. The installer bundles it for Arch through the same pinned Nix package.

The same compatibility module corrects initial focus only when the previous owner is Quickintosh's on-demand desktop layer. It preserves explicit no-focus rules and exclusive modal focus.

Validation: the unguarded isolated compositor disconnected Quickshell during repeated mapped-window captures. With the guard, 16 captured windows closed successfully (16 protocol failures returned normally, zero invalid-object errors). The desktop focus fixture reproduced initial-focus suppression before loading the guard and passed with three newly opened terminals afterward.
