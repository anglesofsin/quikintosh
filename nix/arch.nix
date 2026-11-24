{ desktop, inputs }:
let
  pkgs = desktop.pkgs;
  config = desktop.config;
  find = name: builtins.head (builtins.filter (p: p.name == name) config.environment.systemPackages);
  runtime = pkgs.buildEnv {
    name = "quickintosh-arch-runtime";
    paths = [ config.system.build.quickintosh config.system.build.lickintosh
      config.system.build.riceShell (find "lickintosh-finder") (find "lickintosh-finder.desktop")
      (find "lickintosh-quicklook") (find "lickintosh-quicklook.desktop")
      (find "lickintosh-desktop-profile") (find "rice-file-manager")
      (find "quickintosh-discord-install") config.system.build.noctaliaLegacy
      config.system.build.eqsh pkgs.noctalia-shell
      (builtins.head (builtins.filter (p: pkgs.lib.hasPrefix "caelestia-shell-" p.name) config.environment.systemPackages)) ] ++ (with pkgs; [
        hyprland xdg-desktop-portal-hyprland xdg-desktop-portal-gtk
        kitty matugen mpv playerctl wl-clipboard cliphist grim slurp satty
        hyprpicker hyprsunset brightnessctl ddcutil wireplumber pipewire
        glib gsettings-desktop-schemas nautilus gvfs polkit_gnome
        bibata-cursors nerd-fonts.symbols-only liberation_ttf
        qt6.qtwayland qt6.qtsvg qt6.qtimageformats fontconfig
      ]);
    ignoreCollisions = true;
    pathsToLink = [ "/bin" "/share" "/lib" "/libexec" ];
  };
in pkgs.runCommand "quickintosh-arch-bundle" {} ''
  mkdir -p $out/config $out/arch
  ln -s ${runtime} $out/runtime
  cp -r ${find "hyprland-config"} $out/hypr
  cp -r ${find "infinite-desktop-scripts"} $out/scripts
  cp ${config.environment.etc."nixos-rice/shells.json".source} $out/config/shells.json
  cp ${../modules/rice/catalog.json} $out/config/rices.json
  cp -r ${../arch}/. $out/arch/
''
