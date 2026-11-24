{
  description = "Meu NixOS com Quickintosh";
  inputs = {
    quickintosh.url = "git+ssh://git@github.com/anglesofsin/quikintosh.git";
    nixpkgs.follows = "quickintosh/nixpkgs";
  };
  outputs = inputs@{ nixpkgs, ... }: {
    nixosConfigurations.meupc = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        ./configuration.nix # mantenha o SEU host, discos e bootloader
        inputs.quickintosh.nixosModules.default
        {
          nixpkgs.config.allowUnfree = true;
          quickintosh = {
            enable = true;
            user = "seuusuario";
            discord = { enable = true; clients = [ "canary" ]; };
          };
        }
      ];
    };
  };
}
