{ stdenv, cmake, ninja, qt6 }:
stdenv.mkDerivation {
 pname = "quickintosh-rendering";
 version = "1.1.0";
 src = ./.;
 nativeBuildInputs = [ cmake ninja ];
 buildInputs = [ qt6.qtbase qt6.qtdeclarative qt6.qtmultimedia ];
 doCheck = true;
 checkPhase = ''
   export QT_PLUGIN_PATH="${qt6.qtbase}/lib/qt-6/plugins:${qt6.qtmultimedia}/lib/qt-6/plugins"
   export QT_FFMPEG_DECODING_HW_DEVICE_TYPES=""
   ctest --output-on-failure
 '';
 dontWrapQtApps = true;
}
