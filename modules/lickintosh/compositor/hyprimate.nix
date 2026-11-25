{ lib, stdenv, cmake, ninja, pkg-config, binutils, glibc, hyprland, libpng, nlohmann_json, libglvnd, lua, fetchFromGitHub }:
assert lib.assertMsg (lib.versionAtLeast hyprland.version "0.57" && lib.versionAtLeast stdenv.cc.version "16") "Hyprimate requires the validated Hyprland 0.57.x and GCC 16 toolchain; do not load it into the current 0.56.2 compositor.";
stdenv.mkDerivation {
 pname = "hyprimate";
 version = "0.1-49504fa";
 src = fetchFromGitHub {
  owner = "JustinBacher"; repo = "hyprimate";
  rev = "49504fabb83411d3862dd76dde9383618ab66a55";
  hash = "sha256-Tn3AC6n8NQNV1Y3GghJBUd0qhMNtZ5Fx6bZJ3pPUS9w=";
 };
 nativeBuildInputs = [ cmake ninja pkg-config binutils (lib.getBin glibc) ];
 buildInputs = [ hyprland hyprland.dev libpng nlohmann_json libglvnd lua ] ++ hyprland.buildInputs;
 cmakeBuildType = "Release";
 cmakeFlags = [ "-DBUILD_TESTING=OFF" "-DHYPRLAND_EXECUTABLE=${hyprland}/bin/.Hyprland-wrapped" "-DHYPRIMATE_SPRITE_DIR=${placeholder "out"}/share/hyprimate/sprites" ];
 ninjaFlags = [ "hyprimate" ];
 installPhase = ''
  install -Dm755 hyprimate.so $out/lib/hyprimate.so
  mkdir -p $out/share/hyprimate/sprites $out/share/licenses/hyprimate
  cp ../src/window/swarm/sprites/*.png $out/share/hyprimate/sprites/
  cp ../LICENSE ../THIRD_PARTY_NOTICES.md ../CREDITS.md $out/share/licenses/hyprimate/
 '';
}
