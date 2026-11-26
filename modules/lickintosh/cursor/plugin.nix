{ lib, stdenv, pkg-config, fetchzip, lua5_5, hyprland, aquamarine, hyprcursor, hyprgraphics, hyprlang, hyprutils, pixman, libdrm, libglvnd, libinput, wayland, wayland-protocols, libxkbcommon, libxcb, libxcb-errors, xorg, glslang, cairo }:
let
 modern = lib.versionAtLeast hyprland.version "0.57";
 compiler = if modern then hyprland.stdenv else stdenv;
in
compiler.mkDerivation {
 pname = "quickintosh-dynamic-cursors";
 version = "1.1.0";
 src = fetchzip {
 url = "https://github.com/VirtCode/hypr-dynamic-cursors/archive/2a8d0b735328d874a78ca93b2f201649f712a74a.tar.gz";
 hash = "sha256-PSt/SRtemvsoGYNFJ7YLiXGxT8EJe3AhmGwt5Vt79aA=";
 };
 nativeBuildInputs = [ pkg-config ];
 buildInputs = lib.optionals modern hyprland.buildInputs ++ [ lua5_5 hyprland.dev aquamarine hyprcursor hyprgraphics hyprlang hyprutils pixman libdrm libglvnd libinput wayland wayland-protocols libxkbcommon libxcb libxcb-errors xorg.xcbutilwm xorg.xcbutilrenderutil glslang cairo ];
 patches = [ ./highres.patch ];
 dontConfigure = true;
 enableParallelBuilding = true;
 dontUseCmakeConfigure = true;
 buildPhase = ''
   make -j3 CXX="$CXX" EXTRA_CXXFLAGS="-O2" all
 '';
 installPhase = ''mkdir -p $out/lib; cp out/dynamic-cursors.so $out/lib/'';
}
