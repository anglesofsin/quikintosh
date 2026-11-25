{ lib, stdenv, pkg-config, hyprland, aquamarine, hyprcursor, hyprgraphics, hyprlang, hyprutils, pixman, libdrm, libglvnd, libinput, wayland, wayland-protocols, libxkbcommon, libxcb, libxcb-errors, xorg, glslang, cairo }:
let
 modern = lib.versionAtLeast hyprland.version "0.57";
 compiler = if modern then hyprland.stdenv else stdenv;
in
compiler.mkDerivation {
 pname = "quickintosh-geometry";
 version = "1.1.0";
 src = ./.;
 nativeBuildInputs = [ pkg-config ];
 buildInputs = lib.optionals modern hyprland.buildInputs ++ [ hyprland.dev aquamarine hyprcursor hyprgraphics hyprlang hyprutils pixman libdrm libglvnd libinput wayland wayland-protocols libxkbcommon libxcb libxcb-errors xorg.xcbutilwm xorg.xcbutilrenderutil glslang cairo ];
 dontConfigure = true;
 buildPhase = ''
   $CXX -std=c++${if modern then "26" else "23"} -shared -fPIC -O2 $(pkg-config --cflags hyprland) geometry.cpp -o quickintosh-geometry.so
 '';
 installPhase = ''mkdir -p $out/lib; cp quickintosh-geometry.so $out/lib/'';
}
