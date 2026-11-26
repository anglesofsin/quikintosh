# Wallpaper storage at login

Keep the wallpaper directory on storage available before the shell starts,
preferably `~/Pictures/Wallpapers`. Every parent directory must also be available:
a local wallpaper reached through a `~/Pictures` symlink into a locked encrypted
volume is still unavailable at login.

Check with `readlink -f ~/Pictures/Wallpapers` and
`findmnt -T ~/Pictures/Wallpapers`. The canonical path and the wallpaper selected
in Settings should resolve without unlocking an optional data drive.

If Pictures points to encrypted storage, make Pictures a real local directory
before placing Wallpapers inside it. Other images can remain on the encrypted
drive and be linked individually into Pictures. Preserve the original symlink,
record old/new paths, validate file hashes, and update saved rice profiles that
reference the previous wallpaper directory. Do not move unrelated private images
out of encrypted storage or commit personal wallpaper collections to Git.
