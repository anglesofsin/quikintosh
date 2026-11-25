{ stdenv, pkg-config, hyprland, aquamarine, hyprcursor, hyprgraphics, hyprlang, hyprutils, pixman, libdrm, libglvnd, libinput, wayland, wayland-protocols, libxkbcommon, libxcb, libxcb-errors, xorg, glslang, cairo }:
stdenv.mkDerivation {
 pname = "quickintosh-geometry";
 version = "1.0.0";
 src = ./.;
 nativeBuildInputs = [ pkg-config ];
 buildInputs = [ hyprland.dev aquamarine hyprcursor hyprgraphics hyprlang hyprutils pixman libdrm libglvnd libinput wayland wayland-protocols libxkbcommon libxcb libxcb-errors xorg.xcbutilwm xorg.xcbutilrenderutil glslang cairo ];
 dontConfigure = true;
 buildPhase = ''
   $CXX -std=c++23 -shared -fPIC -O2 $(pkg-config --cflags hyprland) geometry.cpp -o quickintosh-geometry.so
 '';
 installPhase = ''mkdir -p $out/lib; cp quickintosh-geometry.so $out/lib/'';
}
