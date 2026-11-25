{ stdenv, cmake, ninja, qt6 }:
stdenv.mkDerivation {
 pname = "quickintosh-rendering";
 version = "1.1.0";
 src = ./.;
 nativeBuildInputs = [ cmake ninja ];
 buildInputs = [ qt6.qtbase qt6.qtdeclarative ];
 dontWrapQtApps = true;
}
