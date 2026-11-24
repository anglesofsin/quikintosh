{ pkgs }: 
pkgs.stdenvNoCC.mkDerivation {
    pname = "mactahoe-gtk-theme";
    version = "2026-11-22";
    src = pkgs.fetchFromGitHub {
      owner = "vinceliuice";
      repo = "MacTahoe-gtk-theme";
      rev = "1e45e19f510edb8cde18fa84d6cd5319f60b086b";
      sha256 = "1f09mrcygk4wllh3mk2r8ch00mp8w9pcj03f9ahq0drx9qfkdbp9";
    };
    nativeBuildInputs = [ pkgs.sassc pkgs.glib pkgs.libxml2 pkgs.which ];
    postPatch = ''
      substituteInPlace libs/lib-core.sh \
        --replace-fail 'MY_HOME=$(getent passwd "''${MY_USERNAME}" | cut -d: -f6)' 'MY_HOME="$HOME"' \
        --replace-fail 'SUDO_BIN="$(command -v sudo)"' 'SUDO_BIN=""' \
        --replace-fail 'silent_mode="false"' 'silent_mode="true"' \
        --replace-fail 'exec 2> "''${MACTAHOE_TMP_DIR}/error_log.txt"' ':'
    '';
    dontBuild = true;
    installPhase = ''
      export HOME=$TMPDIR/home
      mkdir -p "$HOME" $out/share/themes
      bash install.sh -d $out/share/themes -o normal -b
    '';
  }
