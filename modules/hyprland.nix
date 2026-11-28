{
  config,
  caelestia-shell,
  lib,
  pkgs,
  ...
}:
let
  riceUser = config.quickintosh.user;
  riceHome = config.users.users.${riceUser}.home;
  cleanModuleSource =
    src:
    lib.cleanSourceWith {
      inherit src;
      filter =
        path: _type:
        let
          name = baseNameOf path;
        in
        name != "__pycache__" && !(lib.hasInfix ".bak" name) && !(lib.hasSuffix ".pyc" name);
    };

  hypr-canvas = pkgs.callPackage ./hypr-canvas.nix {};
  cursorLocator = pkgs.callPackage ./lickintosh/cursor/plugin.nix {};

  hyprland-config = pkgs.stdenv.mkDerivation {
    name = "hyprland-config";
    src = cleanModuleSource ./hyprland-lua;
    dontBuild = true;
    installPhase = ''
      mkdir -p $out
      cp -r * $out/
      ${pkgs.python3}/bin/python3 - "$out" ${lib.escapeShellArg riceHome} <<'PYPORTABLE'
import sys
from pathlib import Path
for p in Path(sys.argv[1]).rglob('*'):
    if p.is_file():
        try: s=p.read_text()
        except UnicodeError: continue
        p.write_text(s.replace('/home/pg', sys.argv[2]))
PYPORTABLE
      substituteInPlace $out/hyprland.lua \
        --replace-fail "@HYPR_CANVAS_PLUGIN@" "${hypr-canvas}/lib/hyprland/hypr-canvas.so"
      substituteInPlace $out/cursor-locate.lua --replace-fail "@CURSOR_LOCATOR_PLUGIN@" "${cursorLocator}/lib/dynamic-cursors.so"
    '';
  };
  infinite-desktop-scripts = pkgs.stdenv.mkDerivation {
    name = "infinite-desktop-scripts";
    nativeBuildInputs = [ pkgs.python3 ];
    src = cleanModuleSource ./infinite-desktop;
    dontBuild = true;
    installPhase = ''
      mkdir -p $out
      cp -r * $out/
      ${pkgs.python3}/bin/python3 - "$out" ${lib.escapeShellArg riceHome} <<'PYPORTABLE'
import sys
from pathlib import Path
for p in Path(sys.argv[1]).rglob('*'):
    if p.is_file():
        try: s=p.read_text()
        except UnicodeError: continue
        p.write_text(s.replace('/home/pg', sys.argv[2]))
PYPORTABLE
      chmod +x $out/*.sh $out/*.py
      patchShebangs $out
    '';
  };
in
{
  programs.hyprland = {
    enable = true;
    portalPackage = import ./lickintosh/share-picker/package.nix { inherit pkgs; portal = pkgs.xdg-desktop-portal-hyprland; quickshell = (caelestia-shell.inputs.quickshell.packages.${pkgs.stdenv.hostPlatform.system}.default.override { withX11 = false; withI3 = false; }).withModules [ pkgs.qt6.qtimageformats caelestia-shell.inputs.m3shapes.packages.${pkgs.stdenv.hostPlatform.system}.default ]; };
    xwayland.enable = true;
  };

  environment.systemPackages = with pkgs; [
    (import ./lickintosh/share-picker/cursor.nix { inherit pkgs; })
    jq
    bc
    python3
    procps
    libnotify
    unzip
    ffmpeg
    zenity
    ddcutil
    hyprland-config
    infinite-desktop-scripts
    polkit_gnome
    wlr-randr
    grim
    slurp
    hyprshot
    wl-clipboard
    swappy
    satty
    imagemagick
    tesseract
    wf-recorder
    curl
    cliphist
    hyprpicker
    zbar
    translate-shell
    linux-wallpaperengine
    espeak-ng
    pulseaudio
    kdePackages.breeze-icons
    hypr-canvas
  ];

  services.upower.enable = lib.mkForce true;

  xdg.portal = {
    extraPortals = [ (import ./lickintosh/finder-portal/package.nix { inherit pkgs; }) ];
    config = {
      common."org.freedesktop.impl.portal.FileChooser" = [ "quickintosh-finder" "gtk" ];
      common.default = lib.mkForce [
        "hyprland"
        "gtk"
      ];
      "Hyprland" = {
        "org.freedesktop.impl.portal.FileChooser" = [ "quickintosh-finder" "gtk" ];
        default = lib.mkDefault "hyprland;gtk";
      };
    };
  };

  system.activationScripts.hyprland-config = {
    text = ''
      mkdir -p ${riceHome}/.config/hypr
      chown ${riceUser}:users ${riceHome}/.config/hypr
      for f in ${hyprland-config}/*.lua; do
        ln -sf "$f" "${riceHome}/.config/hypr/$(basename $f)"
      done
      chown -h ${riceUser}:users ${riceHome}/.config/hypr/*
    '';
    deps = [ "users" ];
  };

  system.activationScripts.infinite-desktop-scripts = {
    text = ''
      mkdir -p ${riceHome}/scripts
      chown ${riceUser}:users ${riceHome}/scripts
      for f in ${infinite-desktop-scripts}/*; do
        ln -sf "$f" "${riceHome}/scripts/$(basename $f)"
      done
      chown -h ${riceUser}:users ${riceHome}/scripts/*
    '';
    deps = [ "users" ];
  };

  environment.sessionVariables = {
    XCURSOR_THEME = "MacTahoe-cursors";
    XCURSOR_SIZE = "31";
    HYPRCURSOR_THEME = "MacTahoe-cursors";
    HYPRCURSOR_SIZE = "31";
    NIXOS_OZONE_WL = "1";
    QT_QPA_PLATFORM = "wayland;xcb";
    QT_WAYLAND_DISABLE_WINDOWDECORATION = "1";
    GDK_BACKEND = "wayland,x11";
    SDL_VIDEODRIVER = "wayland";
    CLUTTER_BACKEND = "wayland";
    _JAVA_AWT_WM_NONREPARENTING = "1";
    QT_PLUGIN_PATH = [ "/run/current-system/sw/lib/qt-6/plugins" ];
    MOZ_ENABLE_WAYLAND = "1";
  };
  environment.etc."xdg/menus/applications.menu".text = ''
    <!DOCTYPE Menu PUBLIC "-//freedesktop//DTD Menu 1.0//EN"
      "http://www.freedesktop.org/standards/menu-spec/1.0/menu.dtd">
    <Menu>
      <Name>Applications</Name>
      <DefaultAppDirs/>
      <DefaultDirectoryDirs/>
      <DefaultMergeDirs/>
    </Menu>
  '';
}
