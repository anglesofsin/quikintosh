// Pure policy: a hidden workspace must never stop a visible wallpaper.
function pauseReason(clients, monitors, name, options, onBattery, gameMode) {
    if (gameMode) return 'game-mode';
    if (!options.videoEnabled) return 'disabled';
    if (options.videoPauseBattery && onBattery) return 'battery';
    const monitor = monitors.find(m => m.name === name);
    if (!monitor) return '';
    const regular = Number(monitor.activeWorkspace?.id);
    const special = Number(monitor.specialWorkspace?.id || 0);
    for (const client of clients) {
        if (client.monitor !== monitor.id || client.hidden || client.mapped === false) continue;
        const workspace = Number(client.workspace?.id);
        if (workspace !== regular && (!special || workspace !== special)) continue;
        const state = Number(client.fullscreen || 0);
        if (options.pauseFullscreen && (state & 2)) return 'fullscreen';
        if (options.pauseMaximized && state === 1) return 'maximized';
    }
    return '';
}
