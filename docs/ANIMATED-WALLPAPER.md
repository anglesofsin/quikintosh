# Animated wallpaper playback quality

Settings → Wallpaper → Options → Animated wallpaper performance includes:

- **Video resolution:** Original, 720p, 1080p, 1440p or 2160p.
- **Video frame rate:** Original, 15, 24, 30, 60 or 120 FPS.

Both default to **Original**. Restore playback defaults resets both along with
playback/pause preferences. These controls affect animated wallpapers across
displays; they do not limit shell animations, monitor refresh rate or widgets.
Resolution caps use a 16:9 bounding box, preserve aspect ratio and never enlarge
the input. Frame rate caps never duplicate frames to increase the original FPS.

When a cap is chosen, the shell continues playing the source while FFmpeg
prepares an H.264 playback copy in the background. The copy is cached under
`$XDG_CACHE_HOME/quickintosh/wallpaper-render` (normally `~/.cache`). The key
includes source path, modification time, size and both limits. The source is
never changed by Settings. Conversion is low priority with two encoder threads;
concurrent requests for the same copy share a file lock. An error leaves the
source playing and is shown in Wallpaper options. The first preparation can take
longer than the clip itself; subsequent requests reuse the completed copy.

The wallpaper's VideoOutput remains the single source of frames for widget and
panel glass, including after switching to an optimized copy. Theme palette
extraction continues using the first frame of the selected original source.
Deleting the cache regenerates optimized copies when required.
