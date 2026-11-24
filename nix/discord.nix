{ config, lib, pkgs, ... }:
let
  companion = pkgs.equicord.overrideAttrs (old: {
    postInstall = (old.postInstall or "") + ''
      test -f $out/desktop/renderer.js
      cat ${../modules/lickintosh/voice/discord-bridge.js} >> $out/desktop/renderer.js
    '';
  });
  clients = { stable = pkgs.discord; ptb = pkgs.discord-ptb; canary = pkgs.discord-canary; };
  installer = pkgs.writeShellApplication {
    name = "quickintosh-discord-install";
    runtimeInputs = [ pkgs.python3 pkgs.nodejs ];
    text = ''
      exec python3 ${../scripts/discord-install.py} ${../modules/lickintosh/voice} "$@"
    '';
  };
in {
  config = lib.mkIf config.quickintosh.enable {
    environment.systemPackages = [ installer ] ++ lib.optionals config.quickintosh.discord.enable
      (map (name: clients.${name}.override { withEquicord = true; equicord = companion; }) config.quickintosh.discord.clients);
  };
}
