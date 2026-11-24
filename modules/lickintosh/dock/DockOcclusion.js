.pragma library

// Coordinates from Hyprland are global compositor-logical units. Qt's shell
// scale applies only to the dock rectangle, not the compositor's monitor origin.
function blocked(clients, monitors, monitorName, dock, shellScale) {
    const monitor = monitors.find(m => m.name === monitorName)
    if (!monitor || !dock || !(dock.width > 0 && dock.height > 0)) return false
    const scale = Number.isFinite(shellScale) && shellScale > 0 ? shellScale : 1
    const area = {x: Number(monitor.x || 0) + dock.x * scale,
                  y: Number(monitor.y || 0) + dock.y * scale,
                  width: dock.width * scale, height: dock.height * scale}
    for (const client of clients) {
        if (!client || client.mapped === false || client.hidden) continue
        const owner = monitors.find(m => m.id === client.monitor)
        if (!owner) continue
        const workspace = client.workspace?.id
        const special = owner.specialWorkspace?.id
        // Hidden/minimized special workspaces do not obstruct the desktop,
        // including pinned windows moved there by the shell's Hide action.
        const specialVisible = special !== undefined && special !== 0 && workspace === special
        if (workspace < 0 ? !specialVisible
            : !client.pinned && workspace !== owner.activeWorkspace?.id) continue
        if (owner.id === monitor.id && Number(client.fullscreen) > 0) return true
        if (!client.at || !client.size) continue
        const x = Number(client.at[0]), y = Number(client.at[1])
        const width = Number(client.size[0]), height = Number(client.size[1])
        if (![x,y,width,height].every(Number.isFinite) || width <= 0 || height <= 0) continue
        if (x < area.x + area.width && x + width > area.x &&
            y < area.y + area.height && y + height > area.y) return true
    }
    return false
}
