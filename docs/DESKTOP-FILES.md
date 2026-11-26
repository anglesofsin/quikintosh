# Desktop file shortcuts

Click the desktop or select an icon to focus its file shortcuts. Text editors,
widget text fields and inline renaming retain their own text shortcuts.

| Shortcut | Action |
| --- | --- |
| Ctrl+A | Select all desktop files |
| Ctrl+C / Ctrl+X | Copy / cut selected files |
| Ctrl+V | Paste file selections from the clipboard |
| Ctrl+Z | Undo the last desktop file operation |
| Ctrl+Shift+Z / platform redo shortcut | Redo |
| Ctrl+D | Duplicate selected files |
| Ctrl+Shift+N | Create a folder |
| Ctrl+H | Toggle hidden files |
| F2 | Rename one selected file |
| Enter | Open selected files |
| Delete | Move selected files to Trash |
| Space | Quick Look |

Copy and paste use file URI clipboard data, accepting GNOME copied-files and
standard URI-list selections. Cut clipboard contents are cleared only after a
successful move, and only if another app has not replaced the clipboard.
Operations execute serially in a background worker. Undo/redo keeps up to 100
groups for the lifetime of that worker (not across shell restarts). It covers
copy, move, link, trash, rename, duplicate and new-file/folder operations made
through the desktop, including imported file drops. Undo refuses to overwrite
occupied original paths and preserves the pending history on failure. Undoing
creation/copy moves the resulting item to standard FreeDesktop Trash rather
than permanently deleting it. Trash metadata preserves original names/paths.
Independent operations performed in other file managers are not in this history.

Validation: temporary-directory tests cover collisions, copy/move undo/redo,
trash restoration and metadata, folders and symlinks, partial-operation history,
rename/create, redo invalidation, URI clipboard paste and clipboard cut clearing.

# Flatpak application icons

The shared layered-icon resolver accepts reverse-DNS app IDs and installed icon
URLs, falling back to the exact final app component only when the theme has
artwork for that name. Thus `org.chromium.Chromium` and `chromium-browser` use the
existing Chromium renditions for light/dark and as the source for tinted/clear.
Exact theme matches win; generic suffixes such as `Settings` cannot accidentally
select system artwork. Apps with no matching artwork keep their original icon.
