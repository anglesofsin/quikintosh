{ lib, stdenv, fetchFromGitHub, pkg-config, wayland-scanner, lua5_5, hyprland, wayland, aquamarine, hyprcursor, hyprgraphics, hyprlang, hyprutils, pixman, libdrm, libglvnd, libinput, wayland-protocols, libxkbcommon, libxcb, libxcb-errors, xorg, glslang, cairo }:
let
 modern = lib.versions.majorMinor hyprland.version == "0.57";
 compiler = if modern then hyprland.stdenv else stdenv;
in
compiler.mkDerivation {
 pname = "hyprglass";version = if modern then "1.1.0" else "0.11.0";
 src = if modern then fetchFromGitHub { owner="hyprnux";repo="hyprglass";rev="85b8a8ed8431d7b6f1ef8dad8ae0470d8ea7f291";hash="sha256-Jq47p3kJ3N/qw8E83lIewjg9hp7oJw9iIYzMT+YPXic="; } else fetchFromGitHub { owner="hyprnux";repo="hyprglass";rev="7fc328064c63d9fbaaac8d8204eadf85dcdeae19";hash="sha256-SOdn2s/oxf5v2VYHVmQvfvRIyyV9kFNvEBpQXkLCb+s="; };
 patches = if modern then [ ./hyprglass-057-workspace.patch ./hyprglass-window-animation.patch ] else [ ./hyprglass-skip-dirty.patch ./hyprglass-workspace-viewport.patch ./hyprglass-workspace-move-alpha.patch ];
 postPatch = ''
  ${lib.optionalString modern "cp ${./window-glass-animation.hpp} src/WindowGlassAnimation.hpp"}
  ${lib.optionalString modern "sed -i 's/-std=c++23/-std=c++26/' Makefile"}
  ${lib.optionalString (!modern) "substituteInPlace src/PluginConfig.cpp --replace-fail 'ConfigKeys::ENABLED, Config::INTEGER{1}' 'ConfigKeys::ENABLED, Config::INTEGER{0}'"}
  ${lib.optionalString modern "substituteInPlace src/PluginConfig.cpp --replace-fail 'ConfigKeys::ENABLED, true' 'ConfigKeys::ENABLED, false'"}
 '';
 nativeBuildInputs = [ pkg-config wayland-scanner ];
 buildInputs = lib.optionals modern hyprland.buildInputs ++ [ hyprland.dev lua5_5 wayland aquamarine hyprcursor hyprgraphics hyprlang hyprutils pixman libdrm libglvnd libinput wayland-protocols libxkbcommon libxcb libxcb-errors xorg.xcbutilwm xorg.xcbutilrenderutil glslang cairo ];
 makeFlags = [ "CXX=${compiler.cc.targetPrefix}c++" "HYPRGLASS_VERSION=${if modern then "1.1.0" else "0.11.0"}" ];
 NIX_CFLAGS_COMPILE = "-I${lua5_5}/include -I${hyprland.dev}/include/hyprland/protocols";
 enableParallelBuilding = true;
 installPhase = ''install -Dm755 hyprglass.so $out/lib/hyprglass.so;install -Dm644 LICENSE $out/share/licenses/hyprglass/LICENSE'';
}
