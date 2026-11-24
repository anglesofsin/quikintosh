{ pkgs }:
let
  release = pkgs.stdenvNoCC.mkDerivation {
    pname = "darling-official-runtime";
    version = "0.1.20260608";
    src = pkgs.fetchurl {
      url = "https://github.com/darlinghq/darling/releases/download/v0.1.20260608/debs_20260608.zip";
      hash = "sha256-J0ae85Mtoukd1/s0tw42KKPlS3r5+1SABR9ErzXsof0=";
    };
    nativeBuildInputs = [ pkgs.unzip pkgs.dpkg pkgs.gnutar pkgs.xz pkgs.zstd
      (pkgs.python3.withPackages (p: [ p.lief ])) ];
    dontUnpack = true;
    dontBuild = true;
    dontFixup = true;
    installPhase = ''
      mkdir -p $out
      unzip -q $src -d debs
      for package in debs/*/*noble*.deb; do dpkg-deb --fsys-tarfile "$package" | tar --extract --no-same-owner --no-same-permissions --file=- --directory="$out"; done
      cp -a $out/usr/. $out/
      rm -rf $out/usr
      chmod -R u+w $out
      # Privilege is provided only inside a subordinate user namespace.
      chmod u-s $out/bin/darling
      python3 ${../modules/lickintosh/mac-apps/patch_corecrypto_exports.py} $out/libexec/darling/usr/lib/system/libcorecrypto.dylib
    '';
  };
  entry = pkgs.writeShellScript "quickintosh-darling-entry" ''
    export QUICKINTOSH_SETPRIV=${pkgs.util-linux}/bin/setpriv
    exec ${pkgs.python3}/bin/python3 ${../modules/lickintosh/mac-apps/session.py} --namespace-server
  '';
  fhs = pkgs.buildFHSEnv {
    name = "quickintosh-darling-fhs";
    targetPkgs = p: [ release p.bash p.python3 p.coreutils p.util-linux p.glibc p.zlib p.libbsd p.libmd
      p.xdg-user-dirs p.libcap p.libelf p.fuse p.systemdLibs p.dbus p.libxml2 p.openssl p.libedit
      p.libGL p.libGLU p.mesa p.vulkan-loader p.cairo p.freetype p.fontconfig
      p.libpng p.libjpeg8 p.libtiff p.giflib p.ffmpeg_6 p.llvmPackages_18.libllvm
      p.libx11 p.libxext p.libxrandr p.libxcursor p.libxinerama p.libxfixes
      p.libxi p.libxrender p.libxcb p.libxkbfile p.libxkbcommon p.libpulseaudio p.alsa-lib ];
    multiPkgs = p: [ p.glibc p.libGL p.libGLU p.libx11 p.libxext p.libxrandr p.libxcursor
      p.libxinerama p.libxfixes p.libxi p.libxrender p.libxcb p.libpulseaudio ];
    # The generic FHS merger drops empty directories and rewrites individual
    # files as Nix-store links. Darling needs its complete Darwin filesystem.
    extraBuildCommands = ''
      rm -rf $out/usr/libexec/darling
      mkdir -p $out/usr/libexec/darling
    '';
    extraBwrapArgs = [ "--cap-add ALL" ''--bind "$QUICKINTOSH_DARLING_BASE" /usr/libexec/darling'' ];
    runScript = entry;
    profile = ''
      export DPREFIX="''${DPREFIX:-$HOME/.local/share/quickintosh/darling/prefix}"
      export LANG=C.UTF-8
      export XDG_CACHE_HOME="''${XDG_CACHE_HOME:-$HOME/.cache}"
      export MESA_SHADER_CACHE_DIR="$XDG_CACHE_HOME/darling/mesa"
      mkdir -p "$XDG_CACHE_HOME/fontconfig" "$MESA_SHADER_CACHE_DIR"
      export FONTCONFIG_FILE=${pkgs.makeFontsConf { fontDirectories = [ pkgs.liberation_ttf pkgs.dejavu_fonts ]; }}
    '';
  };
in pkgs.writeShellApplication {
  name = "darling";
  runtimeInputs = [ pkgs.util-linux pkgs.coreutils pkgs.python3 ];
  text = ''
    if [ "$(id -u)" = 0 ]; then echo 'Run Darling as your normal desktop user.' >&2; exit 1; fi
    QUICKINTOSH_HOST_UID="$(id -u)"
    QUICKINTOSH_HOST_GID="$(id -g)"
    export QUICKINTOSH_HOST_UID QUICKINTOSH_HOST_GID
    export DPREFIX="''${DPREFIX:-$HOME/.local/share/quickintosh/darling/prefix}"
    mkdir -p "$(dirname "$DPREFIX")"
    export QUICKINTOSH_DARLING_FHS=${fhs}/bin/quickintosh-darling-fhs
    export QUICKINTOSH_DARLING_SOURCE=${release}/libexec/darling
    exec python3 ${../modules/lickintosh/mac-apps/session.py} "$@"
  '';
}
