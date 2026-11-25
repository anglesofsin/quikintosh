# Window effects and widget personalization

Settings → Windows & Effects controls native window opacity, blur, shadows, corners, layout and focus behavior. Changes belong to the Quickintosh profile. Leaving the profile restores the compositor values captured before these overrides, including four-sided window spacing.

Under Application rules, choose an open application's class or enter its exact class, add a rule and optionally restrict it to an exact title. Rules support active/inactive opacity, blur, shadows, animations, corners, borders and window glass. Removing a rule disables its named compositor rules.

Window Liquid Glass uses [HyprGlass](https://github.com/hyprnux/hyprglass), pinned to a release for the bundled Hyprland. It starts disabled globally; a per-application material can enable it individually. The application's background must be transparent to reveal the glass. Kitty supports this with `background_opacity` below 1. Window opacity also affects foreground text; use Kitty's background opacity when only its background should be translucent.

Clock widget → Typography/Colors & effects supports separate colors, wallpaper palette colors, horizontal/vertical divisions, diagonal blends, stripes and three-color composition. Single color remains available. Weather widget settings include precipitation, intensity, speed, lightning and drop color. Weather animation pauses with reduced animation settings and while locked.

The Glass rendering group exposes background caching, live refresh and the refresh limit. Zero means unlimited. The existing visual defaults are retained.

## Hyprimate

[Hyprimate](https://github.com/JustinBacher/hyprimate) runs with the patched Hyprland 0.57.2 and its C++26 toolchain. Quickintosh loads the plugin on startup when built for the 0.57 series. The Liquid style is the plugin default. Settings → Windows & Effects exposes the window, workspace, and wallpaper groups as soon as the plugin loads. Custom Hyprland configuration can live alongside the settings.

Settings → Windows & Effects → Workspace animations lists Hyprimate transitions first, followed by the five native Hyprland styles and Off. Hyprimate exposes the selected effect’s parameters. Native transitions support duration, timing curve, travel distance, and direction. This section preserves the separate special-workspace animations.

The default Nix pin still targets 0.56.2. To build the 0.57 packages, override the compositor input in your host flake. For example, from a Quickintosh checkout:

```sh
nix build .#hyprland .#shell \
  --override-input hyprland-src 'git+https://github.com/hyprwm/Hyprland.git?ref=refs/tags/v0.57.2&rev=11cbc6c577b84ffb1edf4df3fc5b6128c3ae6947&submodules=1' \
  --max-jobs 1 --cores 3
```

Build the compositor, shell and plugins from the same pin. The new compositor takes effect when a new graphical session starts.

The 0.57.2 ports keep the scrolling viewport clip on both window draw and occlusion passes, and keep the HyprGlass composite inside that clip while preserving its padded sample. During a Hyprimate Liquid animation, the glass keeps sampling the live scene, and the finished glass layer follows the same deformation as the window. HyprCanvas and Quickintosh accept named special-workspace identities from the new IPC API. The existing patches continue to apply to 0.56.2.

The see-through capture port redraws the active workspace with Hyprland's protected-content filter for normal full-monitor capture. Region and rotated-monitor captures use Hyprland's native redaction. In a nested 0.57.2 session, a protected test window was omitted from a full-monitor screenshot, revealing the window behind it. Geometry, HyprGlass, HyprCanvas and Hyprimate loaded together. The smoke test opened and closed a window with Liquid, scrolled a special workspace in Canvas mode and captured a scrolling workspace transition with native glass enabled.
