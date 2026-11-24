{ pkgs }:
let
  runtime = import ./darling-runtime.nix { inherit pkgs; };
  command = pkgs.writeShellApplication {
    name = "quickintosh-mac";
    runtimeInputs = [ runtime (pkgs.python3.withPackages (p: [ p.pillow ])) pkgs.zenity pkgs.xdg-utils pkgs.glib pkgs.kitty pkgs._7zz ];
    text = ''exec python3 ${../modules/lickintosh/mac-apps/manager.py} "$@"'';
  };
  desktop = pkgs.makeDesktopItem {
    name = "quickintosh-mac-apps";
    desktopName = "macOS Applications";
    comment = "Install and run compatible macOS applications with Darling";
    exec = "quickintosh-mac library";
    icon = "system-software-install";
    categories = [ "System" "PackageManager" ];
  };
  installer = pkgs.makeDesktopItem {
    name = "quickintosh-mac-installer";
    desktopName = "macOS Installer";
    exec = "quickintosh-mac install %f";
    icon = "system-software-install";
    categories = [ "System" "PackageManager" ];
    mimeTypes = [ "application/x-apple-diskimage" "application/vnd.apple.installer+xml" "application/x-quickintosh-macos-package" "application/x-xar" ];
    noDisplay = true;
  };
  mime = pkgs.writeTextDir "share/mime/packages/quickintosh-mac.xml" ''
    <?xml version="1.0" encoding="UTF-8"?>
    <mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
      <mime-type type="application/x-quickintosh-macos-package">
        <comment>macOS installer package</comment>
        <sub-class-of type="application/x-xar"/>
        <glob pattern="*.pkg" weight="60"/>
        <icon name="system-software-install"/>
      </mime-type>
    </mime-info>
  '';
in pkgs.symlinkJoin {
  name = "quickintosh-mac-apps";
  paths = [ runtime command desktop installer mime ];
}
