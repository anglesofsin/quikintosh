# Live wallpaper glass and island collapse

HyprGlass now subscribes to a layer root again when the layer is mapped. Its
view association can become available after `view.create`. The subscription is
deduplicated by the existing observer. This lets animated wallpaper commits
invalidate the dock's cached backdrop without mouse movement or window damage.
No polling render loop or forced global frame-rate increase is introduced.

The island clears media enlargement, manual expansion, pin and voice peek when
opening its shelf or collapsing after pointer departure. A cover remains active
until the shelf's close interval and the underlying activity morph have settled.
Expanded content is hidden on collapse rather than being exposed again by spring
motion or a changed activity underneath it.

Validation uses a separate nested compositor: animated background pixel samples,
a video wallpaper, plugin unload/reload while the wallpaper remains running, and
rapid island open/close sequences with an enlarged media state. These checks do
not automate input in the user's graphical session.
