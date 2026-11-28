# Small macOS file interactions

Implemented in source (not deployed):
- Desktop Return/Enter starts renaming exactly one selection. F2 remains; Ctrl+O opens selected items. Text input keeps its own keys.
- Desktop rename selects the stem, retaining the extension; directories select their entire name.
- Finder installs a capture controller only on NautilusWindow. Editable/TextView focus is excluded; native file-view rename action is reused. Portal choosers are excluded. Library compiles against GTK4.
- Quick Look retains the surface until its short fade finishes, supports reversing that fade, exposes local raster previews immediately, defers background inventory/capture requests, and uses a bounded metadata cache invalidated by file modification time/size. Image decoding follows display size instead of a fixed 2400px.

Audit of other microinteractions:
- Copy, cut, paste, undo/redo, duplicate and new-folder shortcuts already exist on the desktop; do not duplicate them.
- Quick Look already has Space/Escape closing and arrow navigation; preserve those bindings.
- Folder spring-loading and drag previews already exist in the dock; retain their existing behavior.
- Broader behavior changes in Spotlight, file dialogs or island file lists are excluded by the user's choice.

Validation limitations: backend tests cover file actions/cache invalidation. Private native QML checks cover Quick Look opening/reversal. These are not proof of zero latency on all file types or of a host-GPU frame budget. A real isolated Nautilus instance opened its Rename File popover on Return; Escape preserved the file. Cold PDF/video timing and host-GPU frame pacing still need end-to-end measurement before deployment. Software-rendered first-frame runs reached 102–122 ms, so an unconditional sub-100-ms or zero-lag claim is not supported.

Current artifacts:
- Finder GTK library: /nix/store/k5z377v148sfv436kr1f4ay55f8d6swa-quickintosh-finder-theme-live-1/lib/theme-live.so
- Native Finder capture: /home/pg/.local/state/quickintosh/reviews/file-microinteractions/finder-return-rename.png
- Editable Quick Look review tree: /tmp/qi-quicklook-review
- No activation or host app restart performed for this change.

Final private software-renderer run: first frames 122, 15, 28, 26, 70, 18, 39, 38 ms; all eight reopen/reverse cycles passed. The 100 ms target was missed once; no claim of zero latency or universal frame-budget compliance.
