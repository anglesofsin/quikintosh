# Live wallpaper glass and island collapse

HyprGlass now subscribes to a layer root again when the layer is mapped. Its
view association can become available after `view.create`. The subscription is
deduplicated by the existing observer. This repairs missed layer subscriptions, but subscription alone does not cover
every video presentation path. The dock now also resamples on each real monitor
frame when its namespace has live resampling enabled. That bypass applies only
to `quickshell:dock`; other layers retain background caching. It does not schedule
frames or introduce a polling render loop. Disabling live resampling for the dock
retains the normal cache policy.

The island clears media enlargement, manual expansion, pin and voice peek when
opening its shelf or collapsing after pointer departure. A cover remains active
until the shelf's close interval and the underlying activity morph have settled.
Expanded content is hidden on collapse rather than being exposed again by spring
motion or a changed activity underneath it.

Validation uses a separate nested compositor: animated background pixel samples,
a video wallpaper, plugin unload/reload while the wallpaper remains running, and
rapid island open/close sequences with an enlarged media state. These checks do
not automate input in the user's graphical session.
