# Window effects and widget personalization

Settings → Windows & Effects controls native window opacity, blur, shadows, corners, layout and focus behavior. Changes belong to the Quickintosh profile. Leaving the profile restores the compositor values captured before these overrides, including four-sided window spacing.

Under Application rules, choose an open application's class or enter its exact class, add a rule and optionally restrict it to an exact title. Rules support active/inactive opacity, blur, shadows, animations, corners, borders and window glass. Removing a rule disables its named compositor rules.

Window Liquid Glass uses [HyprGlass](https://github.com/hyprnux/hyprglass), pinned to a release for the bundled Hyprland. It starts disabled globally; a per-application material can enable it individually. The application's background must be transparent to reveal the glass. Kitty supports this with `background_opacity` below 1. Window opacity also affects foreground text; use Kitty's background opacity when only its background should be translucent.

Clock widget → Typography/Colors & effects supports separate colors, wallpaper palette colors, horizontal/vertical divisions, diagonal blends, stripes and three-color composition. Single color remains available. Weather widget settings include precipitation, intensity, speed, lightning and drop color. Weather animation pauses with reduced animation settings and while locked.

The Glass rendering group exposes background caching, live refresh and the refresh limit. Zero means unlimited. The existing visual defaults are retained.

## Hyprimate compatibility work

The requested [Hyprimate](https://github.com/JustinBacher/hyprimate) revision targets Hyprland 0.57.x and a C++26 toolchain. The current Quickintosh compositor is 0.56.2 with custom capture and scrolling-workspace clipping patches. Those patches do not apply unchanged to 0.57.2. Hyprimate is **not installed or enabled** by this change: the compositor, existing plugins and both patches must be ported and tested together before activating that upgrade. The package uses the target compositor’s toolchain and the Quickintosh launcher loads it when built for the 0.57 series. Settings → Windows & Effects shows the Hyprimate controls when the plugin is loaded, with searchable groups for windows, workspaces and wallpaper. User Lua configuration must be retained, and activation of a new compositor requires a new session.

The experimental 0.57.2 viewport port is in `modules/hyprland-0.57-workspace-viewport.patch`. It moves the clip onto the active render context and preserves the tiled-window clipping for both drawing and occlusion. The active 0.56.2 build still uses its existing patches. The 0.57.2 port needs a compositor build and a visual scrolling-workspace regression test before activation.

The 0.57 migration also has candidate ports for see-through monitor capture, HyprCanvas and HyprGlass. The capture port redraws the active workspace with Hyprland's protected-content filter for normal full-monitor capture. Region and rotated-monitor captures retain Hyprland's native redaction. The HyprGlass port clips the final composite while keeping the padded sample and obtains window fade from the compositor's render presentation. The 0.56 packages continue using their existing patches. Validate capture privacy, canvas zoom and input, workspace slides and plugin coexistence before changing the pinned compositor.
