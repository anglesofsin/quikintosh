{ lib, stdenv, pkg-config, hyprland, aquamarine, hyprcursor, hyprgraphics, hyprlang, hyprutils, pixman, libdrm, libglvnd, libinput, wayland, wayland-protocols, libxkbcommon, libxcb, libxcb-errors, xorg, glslang, cairo }:
let
 modern = lib.versionAtLeast hyprland.version "0.57";
 compiler = if modern then hyprland.stdenv else stdenv;
in
compiler.mkDerivation {
 pname = "quickintosh-geometry";
 version = "1.2.0";
 src = ./.;
 nativeBuildInputs = [ pkg-config ];
 buildInputs = lib.optionals modern hyprland.buildInputs ++ [ hyprland.dev aquamarine hyprcursor hyprgraphics hyprlang hyprutils pixman libdrm libglvnd libinput wayland wayland-protocols libxkbcommon libxcb libxcb-errors xorg.xcbutilwm xorg.xcbutilrenderutil glslang cairo ];
 dontConfigure = true;
 buildPhase = ''
   $CXX -std=c++${if modern then "26" else "23"} -shared -fPIC -O2 $(pkg-config --cflags hyprland) geometry.cpp -o quickintosh-geometry.so
   ${lib.optionalString modern "$CXX -std=c++26 -shared -fPIC -O2 $(pkg-config --cflags hyprland) protocol-guard.cpp -ldl -o quickintosh-capture-guard.so"}
 '';
 doCheck = true;
 checkPhase = ''
   $CXX -std=c++23 focus-restore-policy-test.cpp -o focus-policy-test
   ./focus-policy-test
   $CXX -std=c++23 drag-shake-test.cpp -o drag-shake-test
   ./drag-shake-test
 '';
 installPhase = ''mkdir -p $out/lib; cp quickintosh-geometry.so $out/lib/; ${lib.optionalString modern "cp quickintosh-capture-guard.so $out/lib/"}'';
}
