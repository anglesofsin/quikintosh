{ pkgs }:
let
  python = pkgs.python3.withPackages (p: [ p.pygobject3 ]);
  launcher = pkgs.writeShellScript "quickintosh-finder-portal" ''
    export GI_TYPELIB_PATH="${pkgs.glib.out}/lib/girepository-1.0:''${GI_TYPELIB_PATH:-}"
    exec ${python}/bin/python3 ${./portal.py}
  '';
in pkgs.runCommand "quickintosh-finder-portal" {} ''
  mkdir -p $out/share/xdg-desktop-portal/portals $out/share/dbus-1/services
  cat > $out/share/xdg-desktop-portal/portals/quickintosh-finder.portal <<'PORTAL'
[portal]
DBusName=org.quickintosh.FinderPortal
Interfaces=org.freedesktop.impl.portal.FileChooser;
UseIn=Hyprland;
PORTAL
  cat > $out/share/dbus-1/services/org.quickintosh.FinderPortal.service <<SERVICE
[D-BUS Service]
Name=org.quickintosh.FinderPortal
Exec=${launcher}
SERVICE
''
