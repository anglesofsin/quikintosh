{ pkgs }:
pkgs.runCommand "quickintosh-mactahoe-cursors" {
  nativeBuildInputs = [ pkgs.python3 pkgs.hyprcursor ];
  src = pkgs.fetchzip {
    url = "https://github.com/vinceliuice/MacTahoe-icon-theme/archive/839848b9a8a38a92a6936e30c4abe35cc6f2546d.tar.gz";
    hash = "sha256-NAahlBOYub0QlqkYStamoCbyWh+H5JG/iFm4Ws9EU3A=";
  };
} ''
  mkdir -p $out/share/icons/MacTahoe-cursors $out/share/licenses/mactahoe-cursors
  cp -r $src/cursors/dist/. $out/share/icons/MacTahoe-cursors/
  mkdir -p $out/share/icons/MacTahoe-dark-cursors
  cp -r $src/cursors/dist-dark/. $out/share/icons/MacTahoe-dark-cursors/
  mkdir -p hd-work
  python3 ${../cursor/build_hd.py} "$src/cursors/src" "$out/share/icons" "$PWD/hd-work"
  cp $src/cursors/LICENSE $out/share/licenses/mactahoe-cursors/LICENSE
''
