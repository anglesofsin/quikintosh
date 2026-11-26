{ pkgs }:
pkgs.stdenvNoCC.mkDerivation {
 pname = "quickintosh-apple-color-emoji";
 version = "26-20260722";
 src = pkgs.fetchurl {
  url = "https://github.com/samuelngs/apple-emoji-ttf/releases/download/macos-26-20260722-484daf4e/AppleColorEmoji-Linux.ttf";
  hash = "sha256-43x69iZaxKCvbVe8ZehhCad22ZZug0MzRVf2PaSCUW8=";
 };
 dontUnpack = true;
 installPhase = ''
  mkdir -p $out/share/fonts/truetype/apple-color-emoji
  cp $src $out/share/fonts/truetype/apple-color-emoji/AppleColorEmoji.ttf
 '';
 meta.description = "Apple Color Emoji converted to Linux-compatible CBDT/CBLC by samuelngs/apple-emoji-ttf";
}
