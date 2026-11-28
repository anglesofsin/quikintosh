with import (builtins.fetchTarball {
  url = "https://github.com/NixOS/nixpkgs/archive/9fbb54b33e91ee4ca368e35a78e0613c720600b3.tar.gz";
  sha256 = "sha256-cV5xEJJK3BvhU8rEd4mC9UsmDi5qscv/kzGPhBRC5WA=";
}) {};
stdenv.mkDerivation {
  name = "kokoro-env";
  buildInputs = [
    python312
    python312.pkgs.pip
    python312.pkgs.wheel
    python312.pkgs.setuptools
    zlib
    stdenv.cc.cc.lib
  ];
  LD_LIBRARY_PATH = lib.makeLibraryPath [ zlib stdenv.cc.cc.lib ];
  shellHook = ''
    export LD_LIBRARY_PATH="${lib.makeLibraryPath [ zlib stdenv.cc.cc.lib ]}:$LD_LIBRARY_PATH"
  '';
}
