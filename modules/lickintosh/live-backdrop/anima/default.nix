{ lib, rustPlatform, fetchFromGitHub, pkg-config, makeWrapper, wayland, libGL, mpv-unwrapped, libpulseaudio, libxkbcommon }:
rustPlatform.buildRustPackage {
  pname = "quickintosh-anima";
  version = "0.1.0-9272f2e";
  src = fetchFromGitHub {
    owner = "AkerimC"; repo = "anima";
    rev = "9272f2eb0741017e336aadfc71f819722e874722";
    sha256 = "0jyrqvqjjwfbz4ibxh3pi79hr4q5vbi3qarp937w66ldw30810ff";
  };
  cargoLock.lockFile = ./Cargo.lock;
  nativeBuildInputs = [ pkg-config makeWrapper ];
  buildInputs = [ wayland libGL mpv-unwrapped libpulseaudio libxkbcommon ];
  cargoBuildFlags = [ "--package" "anima" "--bin" "anima" "--bin" "animad" ];
  preBuild = ''export NIX_BUILD_CORES=2; export CARGO_BUILD_JOBS=2'';
  # Compare the normal-quality path; do not silently adopt upstream's fast scaler.
  postPatch = ''substituteInPlace src/render/video.rs --replace-fail '("profile", "fast")' '("profile", "default")' '';
  doCheck = false;
  postInstall = ''
    mv $out/bin/anima $out/bin/quickintosh-anima
    mv $out/bin/animad $out/bin/quickintosh-animad
    wrapProgram $out/bin/quickintosh-animad --prefix LD_LIBRARY_PATH : ${lib.makeLibraryPath [ libpulseaudio libGL wayland libxkbcommon ]}
  '';
  meta = { description = "Pinned native wallpaper engine for isolated Quickintosh comparisons"; license = lib.licenses.mit; platforms = lib.platforms.linux; };
}
