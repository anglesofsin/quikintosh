{ lib, stdenv, fetchFromGitHub, pkg-config, wayland-scanner, lua5_5, hyprland, wayland, aquamarine, hyprcursor, hyprgraphics, hyprlang, hyprutils, pixman, libdrm, libglvnd, libinput, wayland-protocols, libxkbcommon, libxcb, libxcb-errors, xorg, glslang, cairo }:
stdenv.mkDerivation {
 pname = "hyprglass";version = "0.11.0";
 src = fetchFromGitHub { owner="hyprnux";repo="hyprglass";rev="7fc328064c63d9fbaaac8d8204eadf85dcdeae19";hash="sha256-SOdn2s/oxf5v2VYHVmQvfvRIyyV9kFNvEBpQXkLCb+s="; };
 patches = [ ./hyprglass-skip-dirty.patch ./hyprglass-workspace-viewport.patch ./hyprglass-workspace-move-alpha.patch ];
 postPatch = ''
  substituteInPlace src/PluginConfig.cpp --replace-fail 'ConfigKeys::ENABLED, Config::INTEGER{1}' 'ConfigKeys::ENABLED, Config::INTEGER{0}'
 '';
 nativeBuildInputs = [ pkg-config wayland-scanner ];
 buildInputs = [ hyprland.dev lua5_5 wayland aquamarine hyprcursor hyprgraphics hyprlang hyprutils pixman libdrm libglvnd libinput wayland-protocols libxkbcommon libxcb libxcb-errors xorg.xcbutilwm xorg.xcbutilrenderutil glslang cairo ];
 makeFlags = [ "CXX=${stdenv.cc.targetPrefix}c++" "HYPRGLASS_VERSION=0.11.0" ];
 NIX_CFLAGS_COMPILE = "-I${lua5_5}/include -I${hyprland.dev}/include/hyprland/protocols";
 enableParallelBuilding = true;
 installPhase = ''install -Dm755 hyprglass.so $out/lib/hyprglass.so;install -Dm644 LICENSE $out/share/licenses/hyprglass/LICENSE'';
}
