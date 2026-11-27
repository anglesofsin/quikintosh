function windowVisible(window, monitor, workspaceHint) {
    if (!window) return false;
    if (window.hidden || window.mapped === false) return false;
    if (!monitor) return true; // wait for the first shared monitor snapshot
    const workspace = Number(window.workspace && window.workspace.id);
    if (!Number.isFinite(workspace)) return true;
    const regular = workspaceHint || Number(monitor.activeWorkspace && monitor.activeWorkspace.id);
    const special = Number(monitor.specialWorkspace && monitor.specialWorkspace.id);
    return workspace === regular || (special !== 0 && workspace === special);
}
