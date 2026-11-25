# Displays and wallpapers

Displays are managed in Settings → Displays. Select a display in the arrangement, drag it into position, or enter X/Y coordinates. Positions use logical pixels after scaling and rotation. Resolution, refresh rate, scale, rotation, extended/mirrored output, VRR, color depth and color profile are editable. Advanced options depend on support from Hyprland, the graphics driver and the display.

Changes stay in a draft until **Apply**. A 30-second preview offers **Keep Changes** and **Revert**. A separate watchdog restores the previous configuration if it is not confirmed, including when the shell exits. At least one independent display must remain enabled. Named profiles can be saved, loaded and removed. Confirmed settings live in `~/.config/quickintosh/displays/`; the shell restores them only when the connected output names match. Other rices do not read this directory.

Wallpapers support All Displays or an individual display, plus separate light, dark and lock-screen images. The lock screen uses a shared image. A display can inherit the global selection again. Add individual images/videos or additional folders without moving the originals. The existing wallpaper directory remains the main library.

Favorites are toggled with the star or right click. The library supports name/newest sorting, thumbnail sizes and optional filenames. Options include fill/fit/stretch/center, background color, dimming, instant/fast/smooth transitions, video pausing in full screen, and scheduled sequential/random wallpaper changes, optionally limited to favorites. Scheduled changes affect the global desktop selection; per-display overrides remain explicit. Videos are silent. Images use demand-driven cached thumbnails with two worker threads and a bounded queue.

Validation uses a fake compositor for display transactions, so automated tests never change the real monitor layout. UI validation runs on a private Wayland compositor. Hardware-specific HDR, mirroring and mode acceptance still require confirmation on the target equipment.
