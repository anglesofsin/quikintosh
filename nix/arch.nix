{ desktop, inputs }:
let
  pkgs = desktop.pkgs;
  config = desktop.config;
  find = name: builtins.head (builtins.filter (p: p.name == name) config.environment.systemPackages);
  runtime = pkgs.buildEnv {
    name = "quickintosh-arch-runtime";
    paths = [ (import ../modules/lickintosh/finder-portal/package.nix { inherit pkgs; }) (import ../modules/lickintosh/share-picker/cursor.nix { inherit pkgs; }) config.programs.hyprland.portalPackage config.system.build.appleEmoji config.system.build.quickintosh config.system.build.lickintosh
      config.system.build.riceShell (find "lickintosh-finder") (find "lickintosh-finder.desktop")
      (find "lickintosh-quicklook") (find "lickintosh-quicklook.desktop")
      (find "lickintosh-desktop-profile") (find "rice-file-manager")
      (find "quickintosh-discord-install") config.system.build.noctaliaLegacy
      config.system.build.eqsh pkgs.noctalia-shell
      (builtins.head (builtins.filter (p: pkgs.lib.hasPrefix "caelestia-shell-" p.name) config.environment.systemPackages))
      (builtins.head (builtins.filter (p: pkgs.lib.hasPrefix "caelestia-cli-" p.name) config.environment.systemPackages)) ] ++ (with pkgs; [
        bash jq bc python3 coreutils findutils gnugrep gawk gnused curl procps
        hyprland xdg-desktop-portal-gtk
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
  test -f $out/hypr/hyprland.lua
  for helper in special-toggle.sh toggle-special-left.sh toggle-special-right.sh toggle-special-public.sh toggle-special-scratchpad.sh toggle-stream-hide.sh canvas-zoom-reset.sh infinite-desktop-scroll-sidemove.sh; do
    test -x "$out/scripts/$helper" || { echo "Missing workspace helper: $helper" >&2; exit 1; }
  done
  cp ${config.environment.etc."nixos-rice/shells.json".source} $out/config/shells.json
  cp ${../modules/rice/catalog.json} $out/config/rices.json
  cp -r ${../arch}/. $out/arch/
  cp ${../modules/lickintosh/arch-pam.py} $out/arch/host-pam.py
''
