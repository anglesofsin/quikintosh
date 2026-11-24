{ pkgs }:
let python = pkgs.python3.withPackages (p: [ p.pyicu p.ltpycld2 ]);
in pkgs.writeShellApplication {
  name = "quickintosh-darling-language";
  runtimeInputs = [ pkgs.systemd ];
  text = ''exec ${python}/bin/python3 ${../modules/lickintosh/mac-apps/language-provider.py} "$@"'';
}
