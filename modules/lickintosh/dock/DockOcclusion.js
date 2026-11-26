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
        const workspace = client.workspace || {}
        const active = owner.activeWorkspace || {}
        const special = owner.specialWorkspace || {}
        const namedSpecial = workspace.type === 'special' || String(workspace.address || workspace.name || '').startsWith('special:')
        const isSpecial = namedSpecial || Number(workspace.id) < 0
        function same(a,b) {
            if(a.id !== undefined && b.id !== undefined)return a.id === b.id
            const x=String(a.address || a.name || ''), y=String(b.address || b.name || '')
            return x!=='' && x===y
        }
        const specialShown = same(workspace,special) && (special.id !== 0) &&
            (Number(special.id)<0 || String(special.address || special.name || '').startsWith('special:'))
        if(isSpecial ? !specialShown : !client.pinned && !same(workspace,active))continue
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
