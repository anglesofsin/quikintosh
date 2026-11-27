// Hyprland 0.57 also publishes named/addressed workspaces without numeric IDs.
// Compare complete descriptors, including socket-event hints, rather than
// treating a missing special ID as an empty regular desktop.
function workspaceKeys(workspace) {
    if (!workspace || workspace === 0) return [];
    if (typeof workspace !== "object") workspace = {name: String(workspace)};
    return [workspace.address, workspace.name, workspace.id]
        .filter(value => value !== undefined && value !== null && value !== "" && String(value) !== "0")
        .map(value => String(value));
}
function sameWorkspace(a, b) {
    const keys = workspaceKeys(a);
    return workspaceKeys(b).some(key => keys.includes(key));
}
function windowVisible(window, monitor, workspaceHint, specialHint) {
    if (!window || window.hidden || window.mapped === false || !monitor) return false;
    const special = specialHint !== undefined && specialHint !== null
        ? specialHint : (workspaceKeys(monitor.specialWorkspace).length
            ? monitor.specialWorkspace : monitor.activeSpecialWorkspace);
    if (workspaceKeys(special).length) return sameWorkspace(window.workspace, special);
    if (window.pinned) return true;
    const regular = workspaceKeys(workspaceHint).length ? workspaceHint : monitor.activeWorkspace;
    return sameWorkspace(window.workspace, regular);
}
function specialEvent(name, data, focusedMonitor) {
    const fields = String(data || "").split(",");
    const v2 = name === "activespecialv2";
    if (fields[v2 ? 2 : 1] && fields[v2 ? 2 : 1] !== focusedMonitor) return null;
    if (!(v2 ? fields[1] : fields[0])) return 0;
    return v2 ? {id: fields[0], name: fields[1], address: fields[0]}
              : {name: fields[0], address: fields[0]};
}
