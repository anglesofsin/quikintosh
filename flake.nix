{
  description = "Quickintosh — complete Tahoe-inspired NixOS/Hyprland desktop";
  inputs = {
    nixgl = { url = "github:nix-community/nixGL"; inputs.nixpkgs.follows = "nixpkgs"; };
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    nixpkgs-patched.url = "github:NixOS/nixpkgs/9fbb54b33e91ee4ca368e35a78e0613c720600b3";
    hyprland-src.url = "git+https://github.com/hyprwm/Hyprland.git?submodules=1";
    noctalia-src = { url = "git+https://github.com/noctalia-dev/noctalia.git"; inputs.nixpkgs.follows = "nixpkgs-patched"; };
    noctalia-legacy-src = { url = "git+https://github.com/noctalia-dev/noctalia.git?ref=legacy-v4"; inputs.nixpkgs.follows = "nixpkgs-patched"; };
    eqsh-src = { url = "git+https://github.com/eq-desktop/eqsh.git?submodules=1"; flake = false; };
    rosa-src = { url = "git+https://github.com/fedyaqq34356/rosa.git"; flake = false; };
    lickintosh-src = { url = "path:./upstream/lickintosh"; flake = false; };
    caelestia-shell = { url = "git+https://github.com/caelestia-dots/shell.git"; inputs.nixpkgs.follows = "nixpkgs"; };
  };
  outputs = inputs@{ self, nixpkgs, ... }: let
    system = "x86_64-linux";
    demo = nixpkgs.lib.nixosSystem {
      inherit system;
      modules = [ self.nixosModules.default {
        nixpkgs.config.allowUnfree = true;
        quickintosh = { enable = true; user = "demo"; };
        users.users.demo = { isNormalUser = true; home = "/home/demo"; };
        fileSystems."/" = { device = "none"; fsType = "tmpfs"; };
        boot.loader.grub.enable = false;
        system.stateVersion = "26.05";
      } ];
    };
  in {
    nixosModules.default = import ./nix/module.nix { inherit inputs; };
    packages.${system} = {
      darling = import ./packages/mac-apps.nix { pkgs = import nixpkgs { inherit system; config.allowUnfree = true; }; };
      darling-experimental = import ./packages/darling-experimental.nix { pkgs = import nixpkgs { inherit system; config.allowUnfree = true; }; };
      darling-language = import ./packages/darling-language.nix { pkgs = import nixpkgs { inherit system; config.allowUnfree = true; }; };
      darling-naturallanguage = import ./packages/darling-naturallanguage.nix { pkgs = import nixpkgs { inherit system; config.allowUnfree = true; }; };
      default = demo.config.system.build.quickintosh;
      quickintosh = demo.config.system.build.quickintosh;
      shell = demo.config.system.build.lickintosh;
      shell-source = demo.config.system.build.quickintoshSource;
      glass-plugin = demo.config.system.build.quickintoshGlass;
      geometry-plugin = demo.config.system.build.quickintoshGeometry;
      finder-theme = demo.config.system.build.quickintoshFinderTheme;
      workspace-scripts = builtins.head (builtins.filter
        (p: p.name == "infinite-desktop-scripts") demo.config.environment.systemPackages);
      hyprland-config = builtins.head (builtins.filter
        (p: p.name == "hyprland-config") demo.config.environment.systemPackages);
      rice-shell = demo.config.system.build.riceShell;
      hyprland = demo.config.programs.hyprland.package;
      arch-mesa = inputs.nixgl.packages.${system}.nixGLIntel;
      arch = import ./nix/arch.nix { desktop = demo; inherit inputs; };
    };
    checks.${system}.configuration = demo.config.system.build.toplevel;
  };
}
