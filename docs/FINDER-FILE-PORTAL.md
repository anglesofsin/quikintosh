# Finder file dialogs

Quickintosh routes only `org.freedesktop.impl.portal.FileChooser` to Nautilus's
native implementation using the `quickintosh-finder` portal descriptor. A small
asynchronous delegate owns the backend name without starting Nautilus until
a file request arrives. This avoids a circular dependency between the portal
frontend and Finder during cold startup. Open,
save, multiple selection and folder dialogs therefore belong to Finder and use
its current Tahoe GTK4 material, SF fonts and wallpaper-derived icon/accent
palette. GTK remains an available fallback; Hyprland remains the screen-capture
backend. Portal requests, filters and returned URIs retain the native protocol.

The desktop profile registers a per-user Nautilus D-Bus activation service using
the Finder wrapper. Its service mode does not open an extra regular window, and
loads the same resource overlays/live CSS provider even when no Finder window
was previously open. Chooser material selectors also target NautilusFileChooser.
GTK3 fallback styles omit GTK4-only root variables/focus pseudo-classes.

On NixOS the portal descriptor/configuration is installed declaratively. The
Arch bundle includes the descriptor and its installer writes the corresponding
per-user routing and activation entries, using its normal backup/restore flow.
A running portal frontend needs one restart to pick up changed routing. Do not
restart it during an active screen-sharing session without user approval.

Validation: cold frontend startup with the delegate completed in 0.62 seconds
on a private bus; frontend OpenFile/SaveFile requests reached the native chooser
and cancelled successfully. Frontend OpenFile/SaveFile acceptance also returned
the expected temporary-file URIs through the delegate. The native implementation was also exercised in a nested Wayland compositor with
a private session bus. Open, save, multiple and directory requests opened and
closed without returning file URIs on cancellation. Save accepted a temporary
filename and returned its URI; Open accepted a temporary existing file and
returned its URI. Automatic acceptance used a test-only GTK action driver in the
private test process; it is not part of the installed software. Ten Arch
installer tests and five palette/material tests also passed.

Implementation reference: GNOME's portal delegates its file chooser requests to
Nautilus at `/org/freedesktop/portal/desktop`:
https://gitlab.gnome.org/GNOME/xdg-desktop-portal-gnome/-/blob/main/src/filechooser.c

Native file chooser windows identify as `org.quickintosh.Finder.FileChooser`.
The Finder presentation hook sets this only for `NautilusFileChooser` during
realize/map; ordinary Finder windows keep their original identity. Hyprland
floats and centers these dialogs and excludes them from learned app layout
preferences. Dialogs do not create a separate Dock app entry. Nested-compositor
validation confirmed floating OpenFile, SaveFile, multiple and directory dialogs.

The screen-sharing picker uses a fixed-cell GridView rather than unconstrained
Repeater items in a GridLayout. Native toplevel captures provide window previews;
window addresses are normalized independently from the portal's selection handle.
Workspace choices retain the backend tracker id. An unavailable preview does not
prevent choosing a valid source. Region selection stays a separate slurp step.
The four tabs were visually checked in a private nested compositor. Seven source
protocol tests cover Unicode/byte lengths, window identities, workspace ids,
negative monitor coordinates, invalid choices and cancellation.

Quick Look toolbar icons reuse the rice's vector artwork with a consistent
stroke weight (Feather MIT license included with the assets). Narrow windows put
additional actions in the More menu. The interface was rendered at 880×650 and
520×450 in the isolated compositor; the 12 backend tests passed.
