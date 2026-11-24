{ inputs }:
{ config, lib, pkgs, ... }:
let cfg = config.quickintosh; in {
  options.quickintosh = {
    enable = lib.mkEnableOption "the Quickintosh desktop";
    macApps.enable = lib.mkEnableOption "experimental macOS application compatibility with Darling";
    user = lib.mkOption { type = lib.types.str; description = "Existing normal user receiving the desktop configuration"; };
    discord.enable = lib.mkEnableOption "Discord clients with the Dynamic Island companion built in";
    discord.clients = lib.mkOption { type = lib.types.listOf (lib.types.enum [ "canary" "ptb" "stable" ]); default = [ "canary" ]; description = "Discord channels to install with the companion"; };
  };
  imports = [
    (import ./discord.nix)
    ({ config, lib, pkgs, ... }: lib.mkIf config.quickintosh.enable (import ../modules/rice.nix {
      inherit config lib pkgs;
      inherit (inputs) caelestia-shell noctalia-legacy-src rosa-src eqsh-src;
      # A path input nested in this repository can inherit the parent Git rev.
      # Normalize its source so docs/installer commits don't rebuild all assets.
      lickintosh-src = {
        outPath = builtins.path { path = inputs.lickintosh-src.outPath; name = "quickintosh-upstream"; };
        rev = (builtins.fromJSON (builtins.readFile ../upstream/SOURCES.json)).lickintosh.revision;
      };
    }))
    ({ config, lib, pkgs, ... }: lib.mkIf config.quickintosh.enable (import ../modules/hyprland.nix { inherit config lib pkgs; }))
    ({ config, pkgs, ... }: lib.mkIf config.quickintosh.enable ((import ./overlay.nix { inherit inputs; }) { inherit pkgs; }))
  ];
  config = lib.mkIf cfg.enable {
    assertions = [{ assertion = builtins.hasAttr cfg.user config.users.users; message = "Create quickintosh.user in users.users before enabling Quickintosh."; }];
    services.dbus.enable = true;
    services.gvfs.enable = true;
    services.gnome.gnome-keyring.enable = true;
    services.pipewire = { enable = true; pulse.enable = true; alsa.enable = true; wireplumber.enable = true; };
    security.rtkit.enable = true;
    networking.networkmanager.enable = lib.mkDefault true;
    hardware.bluetooth.enable = lib.mkDefault true;
    hardware.i2c.enable = true;
    programs.dconf.enable = true;
    programs.gamemode.enable = true;
    users.users.${cfg.user}.extraGroups = [ "video" "audio" "input" "i2c" "networkmanager" ];
    environment.systemPackages = with pkgs; [ kitty matugen mpv pavucontrol kdePackages.kdeconnect-kde bibata-cursors ]
      ++ lib.optionals cfg.macApps.enable [ (import ../packages/mac-apps.nix { inherit pkgs; }) ];
    fonts.packages = with pkgs; [ nerd-fonts.jetbrains-mono liberation_ttf ];
    xdg.portal.extraPortals = [ pkgs.xdg-desktop-portal-gtk ];
  };
}
