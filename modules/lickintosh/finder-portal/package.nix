{ pkgs }:
pkgs.runCommand "quickintosh-finder-portal" {} ''
  mkdir -p $out/share/xdg-desktop-portal/portals
  cat > $out/share/xdg-desktop-portal/portals/quickintosh-finder.portal <<'PORTAL'
[portal]
DBusName=org.gnome.Nautilus
Interfaces=org.freedesktop.impl.portal.FileChooser;
UseIn=Hyprland;
PORTAL
''
