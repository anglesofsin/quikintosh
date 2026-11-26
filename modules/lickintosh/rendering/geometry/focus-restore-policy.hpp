#pragma once
// Only automatic layer-focus restoration is gated. Explicit user focus actions
// must keep their normal ability to open a workspace.
constexpr bool shouldRefocusPointer(bool monitor, bool exclusiveLayer, bool window,
                                   bool workspace, bool visibleWorkspace) {
    return monitor && !exclusiveLayer && window && workspace && !visibleWorkspace;
}
