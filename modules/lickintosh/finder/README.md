# Finder presentation in Lickintosh

The file manager remains Nautilus. `overlay.py` modifies only the content
AdwToolbarView in its GtkBuilder resource, allowing files to scroll behind the
toolbar. The Lickintosh Finder wrapper loads this resource through GLib's
`G_RESOURCE_OVERLAYS`; the distribution's Nautilus binary is unchanged.

`../finder-glass.css` is appended to the rice-managed GTK 4 stylesheet. It keeps
the file view opaque, paints the frame outside the rounded sidebar opaque,
and applies native backdrop blur to the sidebar and floating toolbar controls.
Nested path buttons are transparent so they do not stack opaque layers.
The decorative yellow button remains insensitive, and follows the other window
controls' inactive state. CSS is restored by the existing desktop-profile
snapshot when leaving Lickintosh.

GTK's backdrop blur, tint and highlights approximate glass, but do not implement
the Quickshell shader's optical refraction. No screenshot polling, injected
input, client-side file-manager replacement or binary patching is used.

References:
- https://docs.gtk.org/gio/struct.Resource.html#overlays
- https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1.9/method.ToolbarView.set_extend_content_to_top_edge.html
