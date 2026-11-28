{
  caelestia-shell,
  config,
  lib,
  noctalia-legacy-src,
  lickintosh-src,
  rosa-src,
  eqsh-src,
  pkgs,
  ...
}:
let
  riceUser = config.quickintosh.user;
  riceHome = config.users.users.${riceUser}.home;
  system = pkgs.stdenv.hostPlatform.system;
  caelestiaPackage = caelestia-shell.packages.${system}.with-cli.override {
    hyprland = pkgs.hyprland;
  };
  caelestiaCli = caelestia-shell.inputs.caelestia-cli.packages.${system}.default;
  noctaliaLegacyRevision = builtins.substring 0 8 (noctalia-legacy-src.rev or "a08ff361");
  noctaliaLegacyVersion = "4.7.7+legacy.${noctaliaLegacyRevision}";
  noctaliaLegacyBase = noctalia-legacy-src.packages.${system}.default;
  noctaliaLegacyPackage =
    (pkgs.writeShellApplication {
      name = "noctalia-legacy";
      runtimeInputs = [ noctaliaLegacyBase ];
      text = ''
        export NOCTALIA_CONFIG_DIR="''${NOCTALIA_CONFIG_DIR:-${riceHome}/.config/noctalia-legacy}"
        export NOCTALIA_CACHE_DIR="''${NOCTALIA_CACHE_DIR:-${riceHome}/.cache/noctalia-legacy}"
        exec ${noctaliaLegacyBase}/bin/noctalia-shell "$@"
      '';
    }).overrideAttrs
      {
        pname = "noctalia-legacy";
        version = noctaliaLegacyVersion;
        meta = {
          description = "Noctalia v4 legacy desktop shell built with Quickshell";
          license = lib.licenses.mit;
          mainProgram = "noctalia-legacy";
          platforms = lib.platforms.linux;
        };
      };
  lickintoshQs = (caelestia-shell.inputs.quickshell.packages.${system}.default.override { withX11 = false; withI3 = false; }).withModules [ pkgs.qt6.qtimageformats caelestia-shell.inputs.m3shapes.packages.${system}.default ];
  appleEmojiFont = import ./lickintosh/emoji/font.nix { inherit pkgs; };
  capturePython = pkgs.python3.withPackages (p: [ p.pillow ]);
  shelfPython = pkgs.python3.withPackages (p: [ p.pillow p.pygobject3 p.pymupdf p.rembg p.onnxruntime ]);
  quickLookPython = pkgs.python3.withPackages (p: [ p.pillow p.pygobject3 ]);
  voicePython = pkgs.python3.withPackages (p: [ p.websockets ]);
  rosaIslandd = pkgs.rustPlatform.buildRustPackage {
    pname = "rosa-islandd";
    version = "0.1.0-${builtins.substring 0 8 rosa-src.rev}";
    src = rosa-src + "/src/islandd";
    cargoLock.lockFile = rosa-src + "/src/islandd/Cargo.lock";
    patches = [ ./lickintosh/islandd-downloads.patch ];
    nativeBuildInputs = [ pkgs.pkg-config ];
    buildInputs = [ pkgs.dbus pkgs.libpulseaudio ];
  };
  rosaTools = pkgs.runCommand "rosa-island-tools" { } ''
    mkdir -p $out/bin
    cp ${rosa-src}/bin/hyprdo $out/bin/hyprdo
    chmod +x $out/bin/hyprdo
    patchShebangs $out/bin
  '';
  tahoeGtk = import ./lickintosh/tahoe-theme.nix { inherit pkgs; };
  iconMaterialPython = pkgs.python3.withPackages (p: [ p.pillow p.numpy ]);
  tahoeDesignIcons = pkgs.fetchzip {
    extension = "tar.gz";
    url = "https://codeload.github.com/MiaowCham/macOS_Tahoe_Themes_for_MDF/tar.gz/48c6a0aaaca1c6023790815842f1c0e3ddb779dc";
    sha256 = "1a8qnvcad35jn1y04p6c8cmwb7ma1gwrhx3kgyzcvm15c6yd2wkb";
  };
  tahoeLinuxIcons = pkgs.fetchzip {
    extension = "tar.gz";
    url = "https://codeload.github.com/Scrimas/MacOS-Like/tar.gz/838dfd392b24d2e5886b6618bee63f84328baa52";
    sha256 = "1k78lciq9p6zf5ybf308cjxm71vvwirysqac8wdz92ms76kb20h8";
  };
  tahoeIconBank = pkgs.runCommand "lickintosh-native-icon-bank" {} ''
    mkdir -p $out/layered-icons
    ${pkgs.python3}/bin/python3 ${./lickintosh/layered-icons/bank.py} $out ${tahoeDesignIcons} ${tahoeLinuxIcons} ${pkgs.librsvg}/bin/rsvg-convert ${./lickintosh/layered-icons/artwork/discord-canary.png}
  '';
  tahoeIcons = pkgs.runCommand "lickintosh-tahoe-icons" {} ''
    mkdir -p $out/share/icons
    for theme in ${lickintosh-src}/assets/icons_desktop/MacTahoe*; do
      ln -s "$theme" "$out/share/icons/$(basename "$theme")"
    done
  '';
  desktopProfileSource = pkgs.runCommand "quickintosh-desktop-profile-source" {} ''
    mkdir -p $out/quicklook
    cp ${./lickintosh/desktop-profile.py} $out/desktop-profile.py
    cp ${./lickintosh/wallpaper_theme.py} $out/wallpaper_theme.py
    cp ${./lickintosh/font_preferences.py} $out/font_preferences.py
    cp ${./lickintosh/finder-glass.css} $out/finder-glass.css
    cp ${./lickintosh/quicklook/mime_types.py} $out/quicklook/mime_types.py
  '';
  desktopProfile = pkgs.writeShellApplication {
    name = "lickintosh-desktop-profile";
    runtimeInputs = [ quickLookPython pkgs.glib pkgs.gsettings-desktop-schemas ];
    text = ''
      export XDG_DATA_DIRS="${pkgs.nautilus}/share/gsettings-schemas/${pkgs.nautilus.name}:${pkgs.nemo}/share/gsettings-schemas/${pkgs.nemo.name}:${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}:''${XDG_DATA_DIRS:-/run/current-system/sw/share}"
      action="''${1:-enter}"
      shift || true
      export GI_TYPELIB_PATH="${pkgs.glib.out}/lib/girepository-1.0:''${GI_TYPELIB_PATH:-}"
      exec python3 ${desktopProfileSource}/desktop-profile.py "$action" ${tahoeGtk} ${tahoeIcons} "$@"
    '';
  };
  quickLookOpener = pkgs.writeShellApplication {
    name = "lickintosh-quicklook";
    runtimeInputs = [ quickLookPython pkgs.libnotify ];
    text = ''
      export GI_TYPELIB_PATH="${pkgs.glib.out}/lib/girepository-1.0:''${GI_TYPELIB_PATH:-}"
      export GIO_EXTRA_MODULES="${pkgs.gvfs}/lib/gio/modules:''${GIO_EXTRA_MODULES:-}"
      export LICKINTOSH_CLI="''${LICKINTOSH_CLI:-lickintosh}"
      exec python3 ${./lickintosh/quicklook}/open.py "$@"
    '';
  };
  quickLookDesktop = pkgs.makeDesktopItem {
    name = "lickintosh-quicklook";
    desktopName = "Quick Look";
    genericName = "Lickintosh File Preview";
    exec = "${quickLookOpener}/bin/lickintosh-quicklook %U";
    icon = "document-preview";
    categories = [ "Utility" "Viewer" ];
    # Associations are installed/restored by the rice profile, never globally.
    extraConfig.NoDisplay = "true";
  };
  finderUi = pkgs.runCommand "lickintosh-finder-ui" { nativeBuildInputs = [ pkgs.glib.dev pkgs.python3 ]; } ''
    mkdir -p $out
    gresource extract ${pkgs.nautilus}/bin/.nautilus-wrapped /org/gnome/nautilus/ui/nautilus-window.ui > window-original.ui
    gresource extract ${pkgs.nautilus}/bin/.nautilus-wrapped /org/gnome/nautilus/ui/nautilus-history-controls.ui > history-original.ui
    python3 ${./lickintosh/finder/overlay.py} window-original.ui $out/nautilus-window.ui history-original.ui $out/nautilus-history-controls.ui
  '';
  finderThemeLive = pkgs.stdenv.mkDerivation {
    pname = "quickintosh-finder-theme-live"; version = "1";
    src = ./lickintosh/finder;
    nativeBuildInputs = [ pkgs.pkg-config ]; buildInputs = [ pkgs.gtk4 ];
    buildPhase = ''$CC -shared -fPIC -O2 -Wall -Wextra theme-live.c -o theme-live.so $(pkg-config --cflags --libs gtk4)'';
    installPhase = ''install -Dm755 theme-live.so $out/lib/theme-live.so'';
  };
  finder = pkgs.writeShellApplication {
    name = "lickintosh-finder";
    runtimeInputs = [ pkgs.nautilus pkgs.gsettings-desktop-schemas pkgs.glib ];
    text = ''
      ${shelfPython}/bin/python3 ${./lickintosh/island-shelf/install_finder_services.py} ${shelfPython}/bin/python3 ${./lickintosh/island-shelf/finder_service.py}
      export XDG_DATA_DIRS="${tahoeGtk}/share:${tahoeIcons}/share:''${XDG_DATA_DIRS:-/run/current-system/sw/share}"
      export GI_TYPELIB_PATH="${pkgs.glib.out}/lib/girepository-1.0:''${GI_TYPELIB_PATH:-}"
      export GIO_EXTRA_MODULES="${pkgs.gvfs}/lib/gio/modules:''${GIO_EXTRA_MODULES:-}"
      export LD_PRELOAD="${finderThemeLive}/lib/theme-live.so''${LD_PRELOAD:+:$LD_PRELOAD}"
      export G_RESOURCE_OVERLAYS="/org/gnome/nautilus/ui=${finderUi}''${G_RESOURCE_OVERLAYS:+:$G_RESOURCE_OVERLAYS}"
      if [[ "''${1:-}" == --gapplication-service ]]; then
        exec nautilus "$@"
      fi
      exec nautilus --new-window "$@"
    '';
  };
  finderDesktop = pkgs.makeDesktopItem {
    name = "lickintosh-finder";
    desktopName = "Finder";
    genericName = "Lickintosh File Manager";
    exec = "${finder}/bin/lickintosh-finder %U";
    icon = "system-file-manager";
    mimeTypes = [ "inode/directory" ];
    categories = [ "System" "FileManager" ];
    extraConfig.NoDisplay = "true";
  };
  riceFileManager = pkgs.writeShellApplication {
    name = "rice-file-manager";
    text = ''
      state_dir="''${RICE_SHELL_STATE_DIR:-$HOME/.local/state/nixos-rice}"
      if [[ "$(cat "$state_dir/active-shell" 2>/dev/null || true)" == lickintosh ]]; then
        exec ${finder}/bin/lickintosh-finder "$@"
      fi
      exec ${pkgs.kdePackages.dolphin}/bin/dolphin "$@"
    '';
  };
  quickintoshWindowGlass = pkgs.callPackage ./lickintosh/compositor/hyprglass.nix {};
  supportsHyprimate = lib.versions.majorMinor pkgs.hyprland.version == "0.57";
  quickintoshHyprimate = pkgs.callPackage ./lickintosh/compositor/hyprimate.nix {};

  quickintoshGeometry = pkgs.callPackage ./lickintosh/rendering/geometry {};
  quickintoshRendering = pkgs.callPackage ./lickintosh/rendering/native {};
  quickintoshAnima = pkgs.callPackage ./lickintosh/live-backdrop/anima {};
  lickintoshRoot = pkgs.stdenvNoCC.mkDerivation {
    pname = "lickintosh-source";
    version = "unstable-${builtins.substring 0 8 (lickintosh-src.rev or "6e8f51b8")}";
    src = lickintosh-src;
    patches = [ ./lickintosh/desktop-delete.patch ./lickintosh/notch-labels.patch ./lickintosh/special-workspace-glass.patch ./lickintosh/wallpaper-directory.patch ./lickintosh/dock-visibility.patch ];
    nativeBuildInputs = [ pkgs.qt6.qtshadertools ];
    dontWrapQtApps = true;
    # Keep immutable icon trees shared even during unpacking; copying these
    # tens of thousands of files twice can exhaust inodes on updates.
    unpackPhase = ''
      runHook preUnpack
      mkdir source
      for entry in ${lickintosh-src}/*; do
        if [ "$(basename "$entry")" = assets ]; then
          mkdir source/assets
          for asset in "$entry"/*; do
            if [ "$(basename "$asset")" = icons_desktop ]; then
              ln -s "$asset" source/assets/icons_desktop
            else
              cp -r "$asset" source/assets/
            fi
          done
        else
          cp -r "$entry" source/
        fi
      done
      chmod -R u+w source
      sourceRoot=source
      runHook postUnpack
    '';
    dontBuild = true;
    dontFixup = true; # QML/assets only; helper shebangs are patched explicitly.
    installPhase = ''
      mkdir -p $out
      cp -r shell.qml settings.qml installer.qml services components core ui tools THIRD_PARTY_LICENSES LICENSE $out/
      mkdir -p $out/assets
      for asset in assets/*; do
        if [ "$(basename "$asset")" = icons_desktop ]; then
          ln -s ${lickintosh-src}/assets/icons_desktop $out/assets/icons_desktop
        else
          cp -r "$asset" $out/assets/
        fi
      done
      chmod -R u+w $out
      cp ${pkgs.writeText "lickintosh-shell.qml" (builtins.replaceStrings
        [ "    id: appRoot" "model: appRoot.interfaceShown ? Quickshell.screens : []" "active: appRoot.interfaceShown; Dock {}" ]
        [ ("    id: appRoot\n" + builtins.readFile ./lickintosh/ipc.qml)
          "model: appRoot.interfaceShown && appRoot.riceBarVisible ? Quickshell.screens : []"
          "active: appRoot.interfaceShown && ShellConfig.options.dockAppearance.enable; Dock {}" ]
        (builtins.readFile (lickintosh-src + "/shell.qml")))} $out/shell.qml
      substituteInPlace $out/ui/lockscreen/LockContext.qml \
        --replace-fail 'configDirectory: Quickshell.shellDir + "/ui/lockscreen/pam.d"' 'configDirectory: "/etc/pam.d"'
      substituteInPlace $out/ui/topbar/statusarea/spotlight/SpotlightWindow.qml \
        --replace-fail 'function clickAction(action) {' 'function clickAction(action) { if (action === "spotlight" || action === "applications") { searchField.text = ""; if (action === "spotlight") action = "" } if (action === "emoji") { searchField.text = ">emoji "; action = "actions" } else if (action === "command") { searchField.text = ">sh "; action = "actions" }'
      substituteInPlace $out/services/ShellConfig.qml \
        --replace-fail 'root.seedWallpaper()' 'root.ready = true'
      substituteInPlace $out/ui/dock/Dock.qml \
        --replace-fail 'Quickshell.env("HOME") + "/.icons/"' 'Quickshell.shellDir + "/assets/icons_desktop/"'
      substituteInPlace $out/services/ShellConfig.qml $out/ui/dock/Dock.qml \
        --replace '"dolphin"' '"lickintosh-finder"' --replace '"trash:/"' '"trash:///"'
      # The desktop configuration owns opacity, blur and window rules.
      substituteInPlace $out/services/Theme.qml \
        --replace-fail 'property bool applyToCompositor: true' 'property bool applyToCompositor: false'
      mkdir -p $out/share/icons
      for theme in $out/assets/icons_desktop/*; do
        ln -s "../../assets/icons_desktop/$(basename "$theme")" "$out/share/icons/$(basename "$theme")"
      done
      # Keep the user's explicitly disabled power-profiles service optional.
      substituteInPlace $out/services/GameMode.qml \
        --replace-fail '["powerprofilesctl", "set", "performance"]' '["sh", "-c", "if systemctl -q is-active power-profiles-daemon; then powerprofilesctl set performance; fi"]' \
        --replace-fail '["powerprofilesctl", "set", "balanced"]' '["sh", "-c", "if systemctl -q is-active power-profiles-daemon; then powerprofilesctl set balanced; fi"]'
      ${pkgs.python3}/bin/python3 ${./lickintosh/optimize.py} $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/fluid-glass.py} $out
      cp -r ${rosa-src}/config/quickshell/f $out/rosa
      chmod -R u+w $out/rosa
      cp ${rosa-src}/LICENSE $out/rosa/LICENSE
      cp ${rosa-src}/config/cava/config-bar $out/rosa/cava.conf
      cp -r ${rosa-src}/config/hypr/scripts $out/rosa/helpers
      chmod -R u+w $out/rosa
      ${pkgs.python3}/bin/python3 ${./lickintosh/rosa-integrate.py} $out ${rosaIslandd}/bin/islandd ${./lickintosh/RosaIntegration.qml} ${./lickintosh/RosaPage.qml}
      ${pkgs.python3}/bin/python3 ${./lickintosh/island-options.py} $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/voice}/integrate.py $out ${voicePython}/bin/python3
      ${pkgs.python3}/bin/python3 ${./lickintosh/interface}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/interface}/glass.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/capture}/integrate.py $out ${capturePython}/bin/python3
      ${pkgs.python3}/bin/python3 ${./lickintosh/interface/responsive-panels.py} $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/theming}/integrate.py $out ${capturePython}/bin/python3 ${noctaliaLegacyBase}/share/noctalia-shell
      ${pkgs.python3}/bin/python3 ${./lickintosh/interface/transient-notifications.py} $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/dock}/integrate.py $out ${capturePython}/bin/python3
      ${pkgs.python3}/bin/python3 ${./lickintosh/quicklook}/integrate.py $out ${quickLookPython}/bin/python3
      ${pkgs.python3}/bin/python3 ${./lickintosh/experience}/integrate.py $out ${quickLookPython}/bin/python3
      ${pkgs.python3}/bin/python3 ${./lickintosh/settings}/integrate.py $out ${quickLookPython}/bin/python3
      ${pkgs.python3}/bin/python3 ${./lickintosh/island-idle-hide}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/settings-cleanup.py} $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/appearance-polish}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/profile-sync}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/corners}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/corners}/menus-glass.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/statusbar-fix}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/visual-consistency}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/tahoe-unification}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/tahoe-unification}/runtime.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/spotlight-search}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/extra-widgets}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/image-widget}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/widget-motion}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/privacy-controls}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/icon-styles}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/layered-icons}/integrate.py $out ${iconMaterialPython}/bin/python3 ${pkgs.librsvg}/bin/rsvg-convert
      ln -s ${tahoeIconBank}/layered-icons/native $out/layered-icons/native
      ln -s ${tahoeIconBank}/layered-icons/bank.json $out/layered-icons/bank.json
      ${pkgs.python3}/bin/python3 ${./lickintosh/performance}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/tahoe-feedback}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/voice}/incoming-ui.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/notification-sounds}/integrate.py $out
      qsb --glsl "100 es,120,150" --hlsl 50 --msl 12 -o $out/components/icon-style.frag.qsb $out/components/icon-style.frag
      qsb --glsl "100 es,120,150" --hlsl 50 --msl 12 -o $out/components/bar-tint.frag.qsb $out/components/bar-tint.frag

      ${pkgs.python3}/bin/python3 ${./lickintosh/desktop-polish}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/finder-menus}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/widget-ui}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/widget-stability}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/island-media}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/tray-colors}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/creative-widgets}/integrate.py $out ${pkgs.python3}/bin/python3 ${pkgs.ffmpeg}/bin/ffmpeg ${pkgs.ffmpeg}/bin/ffprobe
      ${pkgs.python3}/bin/python3 ${./lickintosh/editor-layout}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/widget-review}/integrate.py $out ${pkgs.python3}/bin/python3 ${pkgs.tzdata}/share/zoneinfo
      ${pkgs.python3}/bin/python3 ${./lickintosh/notification-polish}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/display-wallpaper}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/dock}/identity-integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/runtime-efficiency}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/rendering}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/personalization}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/compositor}/integrate.py $out
      qsb --glsl "100 es,120,150" --hlsl 50 --msl 12 -o $out/assets/shaders/liquidglass/ClockColors.frag.qsb $out/assets/shaders/liquidglass/ClockColors.frag
      ${pkgs.python3}/bin/python3 ${./lickintosh/scale-geometry.py} $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/icon-raster-quality.py} $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/lock-state-sync.py} $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/locale-auth-integrate.py} $out ${./lickintosh/arch-pam.py}
      ${pkgs.python3}/bin/python3 ${./lickintosh/localize-ui.py} $out ${./lickintosh/english-ui.json}
      cp -r ${../defaults} $out/quickintosh-defaults
      ${pkgs.python3}/bin/python3 ${./lickintosh/branding.py} $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/i18n}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/island-dashboard/integrate.py} $out ${./lickintosh/island-dashboard} ${./lickintosh/focus}
      ${pkgs.python3}/bin/python3 ${./lickintosh/island-shelf}/integrate.py $out ${shelfPython}/bin/python3
      ${pkgs.python3}/bin/python3 ${./lickintosh/settings-tahoe}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/emoji}/integrate.py $out ${quickLookPython}/bin/python3
      ${pkgs.python3}/bin/python3 ${./lickintosh/calculator}/integrate.py $out ${quickLookPython}/bin/python3
      ${pkgs.python3}/bin/python3 ${./lickintosh/interface/menu-motion.py} $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/settings-organization}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/settings-review}/review.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/cursor}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/dock-glass-fix}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/live-backdrop}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/desktop-files}/integrate.py $out ${quickLookPython}/bin/python3
      ${pkgs.python3}/bin/python3 ${./lickintosh/wallpaper-theme}/integrate.py $out
      ${pkgs.python3}/bin/python3 ${./lickintosh/settings-consistency}/integrate.py $out
      patchShebangs $out/tools $out/rosa/helpers
    '';
  };
  lickintoshPackage = (pkgs.writeShellApplication {
    name = "lickintosh";
    runtimeInputs = [ lickintoshQs rosaIslandd rosaTools pkgs.whisper-cpp pkgs.localsend pkgs.poppler-utils pkgs.tesseract pkgs.zbar pkgs.wf-recorder pkgs.ffmpeg pkgs.pulseaudio pkgs.libnotify pkgs.cava pkgs.psmisc pkgs.libcanberra-gtk3 pkgs.cups pkgs.python3 pkgs.imagemagick pkgs.brightnessctl pkgs.ddcutil
      desktopProfile finder pkgs.glib pkgs.trash-cli pkgs.seahorse pkgs.pika-backup pkgs.networkmanagerapplet pkgs.simple-scan
      pkgs.playerctl pkgs.wl-clipboard pkgs.cliphist pkgs.grim pkgs.slurp
      pkgs.hyprpicker pkgs.jq pkgs.curl pkgs.xdg-utils pkgs.xdg-user-dirs
      pkgs.pipewire pkgs.wireplumber pkgs.networkmanager pkgs.bluez pkgs.upower
      pkgs.power-profiles-daemon pkgs.hyprsunset pkgs.procps pkgs.coreutils
      pkgs.util-linux pkgs.findutils pkgs.gnugrep pkgs.gawk pkgs.gnused ];
    text = ''
      # IPC and registry inspection do not instantiate QML. Do not rerun config
      # migrations and font/plugin setup for every volume key or panel shortcut.
      case "''${1:-}" in
        brightness)
          shift
          exec ${pkgs.python3}/bin/python3 ${lickintoshRoot}/tools/brightness.py "$@"
          ;;
        settings-restore)
          exec ${quickLookPython}/bin/python3 ${lickintoshRoot}/settingsapp/backend.py --restore
          ;;
        ipc)
          active_config="$(${pkgs.python3}/bin/python3 ${./lickintosh/icon-styles/ipc-path.py} ${lickintoshRoot})"
          exec ${lickintoshQs}/bin/qs -p "$active_config" "$@"
          ;;
        list|log|--help|--version)
          ${pkgs.python3}/bin/python3 ${lickintoshRoot}/island-shelf/ensure_ring_shortcut.py
      exec ${lickintoshQs}/bin/qs -p ${lickintoshRoot} "$@"
          ;;
      esac
      ${pkgs.python3}/bin/python3 ${../scripts/setup-defaults.py} ${lickintoshRoot}/quickintosh-defaults ${lickintoshRoot}/assets/wallpapers/daniel-leone.jpg
      mkdir -p "$HOME/.config/lickintosh/core" "$HOME/.config/lickintosh/rosa" "$HOME/.local/state/lickintosh/emoji"
      ${pkgs.python3}/bin/python3 ${./lickintosh/bootstrap.py} ${lickintoshRoot}/assets/wallpapers/daniel-leone.jpg
      export QUICKINTOSH_WHISPER_MODEL="${whisperModel}"
      export QML_IMPORT_PATH="${quickintoshRendering}/lib/qt-6/qml:${lib.makeSearchPath "lib/qt-6/qml" (with pkgs.qt6; [ qtgraphs qtquick3d qtquicktimeline qtmultimedia qt5compat qtsvg ])}:''${QML_IMPORT_PATH:-}"
      export QT_PLUGIN_PATH="${lib.makeSearchPath "lib/qt-6/plugins" (with pkgs.qt6; [ qtmultimedia qtimageformats ])}:''${QT_PLUGIN_PATH:-}"
      export FONTCONFIG_FILE=${pkgs.makeFontsConf { fontDirectories = [ (lickintosh-src + "/assets/fonts") ./lickintosh/widget-review/fonts appleEmojiFont (pkgs.nerd-fonts.symbols-only + "/share/fonts") ]; }}
      export GI_TYPELIB_PATH="${pkgs.glib.out}/lib/girepository-1.0:''${GI_TYPELIB_PATH:-}"
      export GIO_EXTRA_MODULES="${pkgs.gvfs}/lib/gio/modules:''${GIO_EXTRA_MODULES:-}"
      export XDG_DATA_DIRS="${lickintoshRoot}/share:''${XDG_DATA_DIRS:-/run/current-system/sw/share}"
      ${pkgs.python3}/bin/python3 ${./lickintosh/rendering/ensure-geometry.py} ${quickintoshGeometry}/lib/quickintosh-geometry.so
      ${lib.optionalString supportsHyprimate ''
        ${pkgs.python3}/bin/python3 ${./lickintosh/compositor/load-plugin.py} quickintosh-capture-guard ${quickintoshGeometry}/lib/quickintosh-capture-guard.so
        ${pkgs.python3}/bin/python3 ${./lickintosh/compositor/load-plugin.py} quickintosh-maximize-contour ${quickintoshGeometry}/lib/quickintosh-maximize-contour.so
      ''}
      ${pkgs.python3}/bin/python3 ${./lickintosh/compositor/load-plugin.py} hyprglass ${quickintoshWindowGlass}/lib/hyprglass.so ${./lickintosh/compositor/native_glass.py}
      ${lib.optionalString supportsHyprimate ''
        ${pkgs.python3}/bin/python3 ${./lickintosh/compositor/load-plugin.py} hyprimate ${quickintoshHyprimate}/lib/hyprimate.so
      ''}

      QUICKINTOSH_RENDERER="$(${pkgs.python3}/bin/python3 ${./lickintosh/rendering/launcher-env.py})"
      export QUICKINTOSH_RENDERER
      case "$QUICKINTOSH_RENDERER" in threaded|basic) export QSG_RENDER_LOOP="$QUICKINTOSH_RENDERER" ;; esac
      QT_SCALE_FACTOR="$(${pkgs.python3}/bin/python3 ${./lickintosh/interface-scale.py})"
      export QT_SCALE_FACTOR
      exec ${lickintoshQs}/bin/qs -p ${lickintoshRoot} "$@"
    '';
  }).overrideAttrs { version = lickintoshRoot.version; };
  whisperModel = pkgs.fetchurl {
    url = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin";
    sha256 = "1zifp9gk9220vysx8a00mzf2sy05ni4l6crx95baivhlvp1mpvb0";
  };
  shelfJobRunner = pkgs.writeShellApplication {
    name = "quickintosh-run";
    runtimeInputs = [ pkgs.python3 pkgs.libnotify ];
    text = ''exec ${pkgs.python3}/bin/python3 ${lickintoshRoot}/island-shelf/activity_runner.py "$@"'';
  };
  shelfMcp = pkgs.writeShellApplication {
    name = "quickintosh-mcp";
    runtimeInputs = [ pkgs.python3 ];
    text = ''exec ${pkgs.python3}/bin/python3 ${lickintoshRoot}/island-shelf/mcp_server.py "$@"'';
  };
  calculatorLauncher = pkgs.writeShellApplication {
    name = "quickintosh-calculator";
    runtimeInputs = [ lickintoshQs pkgs.wl-clipboard pkgs.hyprland ];
    text = ''
      if [ "$#" -eq 0 ]; then
        if qs -p ${lickintoshRoot}/calculator.qml ipc call calculator open 2>/dev/null; then exit 0; fi
      else
        if qs -p ${lickintoshRoot}/calculator.qml ipc call calculator command "$1" 2>/dev/null; then exit 0; fi
      fi
      export QML_IMPORT_PATH="${quickintoshRendering}/lib/qt-6/qml:${lib.makeSearchPath "lib/qt-6/qml" (with pkgs.qt6; [ qtgraphs qtquick3d qtquicktimeline qtmultimedia qt5compat qtsvg ])}:''${QML_IMPORT_PATH:-}"
      export QT_PLUGIN_PATH="${lib.makeSearchPath "lib/qt-6/plugins" (with pkgs.qt6; [ qtmultimedia qtimageformats ])}:''${QT_PLUGIN_PATH:-}"
      export FONTCONFIG_FILE=${pkgs.makeFontsConf { fontDirectories = [ (lickintosh-src + "/assets/fonts") ./lickintosh/widget-review/fonts appleEmojiFont (pkgs.nerd-fonts.symbols-only + "/share/fonts") ]; }}
      QT_SCALE_FACTOR="$(${pkgs.python3}/bin/python3 ${./lickintosh/interface-scale.py})"
      export QT_SCALE_FACTOR
      QUICKINTOSH_RENDERER="$(${pkgs.python3}/bin/python3 ${./lickintosh/rendering/launcher-env.py})"
      case "$QUICKINTOSH_RENDERER" in threaded|basic) export QSG_RENDER_LOOP="$QUICKINTOSH_RENDERER" ;; esac
      export QUICKINTOSH_CALCULATOR_ACTION="''${1:-}"
      exec qs -p ${lickintoshRoot}/calculator.qml --no-duplicate
    '';
  };
  wallpaperBenchmark = pkgs.writeShellApplication {
    name = "quickintosh-wallpaper-benchmark";
    runtimeInputs = [ lickintoshQs pkgs.ffmpeg pkgs.hyprland ];
    text = ''
      export QML_IMPORT_PATH="${quickintoshRendering}/lib/qt-6/qml:${lib.makeSearchPath "lib/qt-6/qml" (with pkgs.qt6; [ qtmultimedia qt5compat ])}:''${QML_IMPORT_PATH:-}"
      export QT_PLUGIN_PATH="${lib.makeSearchPath "lib/qt-6/plugins" (with pkgs.qt6; [ qtmultimedia ])}:''${QT_PLUGIN_PATH:-}"
      exec ${pkgs.python3}/bin/python3 ${./lickintosh/live-backdrop/benchmark.py} --qs ${lickintoshQs}/bin/qs --qt-root ${lickintoshRoot} --daemon ${quickintoshAnima}/bin/quickintosh-animad --cli ${quickintoshAnima}/bin/quickintosh-anima "$@"
    '';
  };
  calculatorDesktop = pkgs.makeDesktopItem {
    name = "org.quickintosh.Calculator";
    desktopName = "Calculator";
    genericName = "Calculator";
    comment = "Quickintosh scientific calculator, conversions and math notes";
    exec = "${calculatorLauncher}/bin/quickintosh-calculator";
    icon = "accessories-calculator";
    categories = [ "Utility" "Calculator" ];
    keywords = [ "calculadora" "calculatrice" "math" "calculator" "convert" ];
    startupWMClass = "org.quickintosh.Calculator";
  };
  quickintoshPackage = pkgs.runCommand "quickintosh" {} ''
    mkdir -p $out/bin
    ln -s ${lickintoshPackage}/bin/lickintosh $out/bin/quickintosh
    ln -s ${finder}/bin/lickintosh-finder $out/bin/quickintosh-finder
    ln -s ${quickLookOpener}/bin/lickintosh-quicklook $out/bin/quickintosh-quicklook
  '';
  eqshRoot = pkgs.stdenvNoCC.mkDerivation {
    pname = "eqsh-source";
    version = "26.1.1-${builtins.substring 0 8 eqsh-src.rev}";
    src = eqsh-src;
    dontBuild = true;
    dontFixup = true;
    installPhase = ''
      cp -r eqsh $out
      chmod -R u+w $out
      ${pkgs.python3}/bin/python3 ${./eqsh/patch-source.py} $out ${./eqsh/ipc.qml}
    '';
  };
  eqshPackage = (pkgs.writeShellApplication {
    name = "eqsh";
    runtimeInputs = [ lickintoshQs pkgs.python3 pkgs.coreutils pkgs.findutils pkgs.gnugrep pkgs.gawk pkgs.gnused pkgs.util-linux
      pkgs.pipewire pkgs.wireplumber pkgs.networkmanager pkgs.bluez pkgs.upower pkgs.playerctl
      pkgs.wl-clipboard pkgs.cliphist pkgs.grim pkgs.slurp pkgs.satty pkgs.brightnessctl pkgs.ddcutil
      pkgs.hyprland pkgs.curl pkgs.jq pkgs.glib pkgs.xdg-utils pkgs.which pkgs.procps ];
    text = ''
      python3 ${./eqsh/bootstrap.py}
      export QML_IMPORT_PATH="${lib.makeSearchPath "lib/qt-6/qml" (with pkgs.qt6; [ qtmultimedia qt5compat qtsvg ])}:''${QML_IMPORT_PATH:-}"
      export QT_PLUGIN_PATH="${lib.makeSearchPath "lib/qt-6/plugins" (with pkgs.qt6; [ qtmultimedia qtimageformats ])}:''${QT_PLUGIN_PATH:-}"
      export FONTCONFIG_FILE=${pkgs.makeFontsConf { fontDirectories = [ (eqsh-src + "/eqsh/media/fonts") ]; }}
      exec ${lickintoshQs}/bin/qs -p ${eqshRoot} "$@"
    '';
  }).overrideAttrs { version = eqshRoot.version; };
  shells = {
    default = "noctalia";
    shells = {
      noctalia = {
        label = "Noctalia C++";
        version = pkgs.noctalia-shell.version;
      };
      noctalia-legacy = {
        label = "Noctalia Stable (Legacy/Quickshell)";
        version = noctaliaLegacyVersion;
      };
      eqsh = { label = "eqSh"; version = eqshRoot.version; };
      lickintosh = {
        label = "Quickintosh";
        version = lickintoshRoot.version;
      };
      caelestia = {
        label = "Caelestia Shell";
        version = caelestiaPackage.version;
      };
    };
  };
  shellManifest = pkgs.writeText "nixos-rice-shells.json" (builtins.toJSON shells);
  riceShell = pkgs.stdenvNoCC.mkDerivation {
    pname = "rice-shell-manager";
    version = "1.0.0";
    src = ./rice;
    nativeBuildInputs = [ pkgs.makeWrapper ];
    dontBuild = true;
    installPhase = ''
      install -Dm755 rice-shell.py $out/libexec/rice-shell/rice-shell.py
      makeWrapper ${pkgs.python3}/bin/python3 $out/bin/rice-shell \
        --add-flags "$out/libexec/rice-shell/rice-shell.py" \
        --set-default RICE_SHELL_MANIFEST /etc/nixos-rice/shells.json \
        --prefix PATH : ${
          lib.makeBinPath [
            desktopProfile
            caelestiaPackage
            caelestiaCli
            pkgs.coreutils
            pkgs.brightnessctl
            pkgs.ddcutil
            pkgs.fuzzel
            pkgs.grim
            pkgs.hyprland
            pkgs.hyprsunset
            pkgs.noctalia-shell
            noctaliaLegacyPackage
            lickintoshPackage
            eqshPackage
            pkgs.procps
            pkgs.slurp
            pkgs.wf-recorder
            pkgs.wireplumber
            pkgs.wl-clipboard
          ]
        }
    '';
    meta = {
      description = "Runtime desktop-shell selector for Noctalia C++, Noctalia legacy and Caelestia";
      license = lib.licenses.mit;
      mainProgram = "rice-shell";
      platforms = lib.platforms.linux;
    };
  };
  riceManager = pkgs.stdenvNoCC.mkDerivation {
    pname = "nixos-rice-manager";
    version = "1.0.0";
    src = ./rice;
    nativeBuildInputs = [ pkgs.makeWrapper ];
    dontBuild = true;
    installPhase = ''
      install -Dm755 rice-manager.py $out/libexec/nixos-rice/rice-manager.py
      install -Dm644 catalog.json $out/share/nixos-rice/catalog.json
      makeWrapper ${pkgs.python3}/bin/python3 $out/bin/rice-manager \
        --add-flags "$out/libexec/nixos-rice/rice-manager.py" \
        --set-default RICE_CATALOG /etc/nixos-rice/rices.json \
        --set-default RICE_SHELL_BIN ${riceShell}/bin/rice-shell \
        --prefix PATH : ${
          lib.makeBinPath [
            caelestiaPackage
            caelestiaCli
            pkgs.coreutils
            pkgs.kitty
            pkgs.noctalia-shell
            noctaliaLegacyPackage
            riceShell
          ]
        }
    '';
    meta = {
      description = "Transactional rice profiles for Noctalia and Caelestia";
      license = lib.licenses.mit;
      mainProgram = "rice-manager";
      platforms = lib.platforms.linux;
    };
  };
  shellDefaults = pkgs.writeText "caelestia-shell-defaults.json" (
    builtins.toJSON {
      general = {
        showOverFullscreen = true;
        apps = {
          terminal = [ "kitty" ];
          audio = [ "pavucontrol" ];
          playback = [ "mpv" ];
          explorer = [ "dolphin" ];
        };
        idle.timeouts = [
          {
            timeout = 600;
            idleAction = "dpms off";
            returnAction = "dpms on";
          }
          {
            timeout = 660;
            idleAction = "lock";
          }
          {
            enabled = false;
            timeout = 1800;
            idleAction = [ "suspendThenHibernate" ];
          }
        ];
      };
      paths.wallpaperDir = "${riceHome}/Pictures/Wallpapers";
    }
  );
  cliDefaults = pkgs.writeText "caelestia-cli-defaults.json" (
    builtins.toJSON {
      theme = {
        enableTerm = false;
        enableHypr = false;
        enableDiscord = false;
        enableSpicetify = false;
        enablePandora = false;
        enableFuzzel = true;
        enableBtop = false;
        enableNvtop = false;
        enableHtop = false;
        enableGtk = false;
        enableQt = false;
        enableWarp = false;
        enableChromium = false;
        enableZed = false;
        enableCava = false;
      };
    }
  );
in
{
  # Expose the exact installed wrapper as a cheap, explicit source-update
  # target without searching through environment.systemPackages.
  system.build.noctaliaLegacy = noctaliaLegacyPackage;
  system.build.lickintosh = lickintoshPackage;
  system.build.quickintosh = quickintoshPackage;
  system.build.appleEmoji = appleEmojiFont;
  fonts.packages = [ appleEmojiFont (pkgs.runCommand "quickintosh-sf-fonts" {} ''
    mkdir -p $out/share/fonts/opentype
    for family in SFM SFPD SFPT SFPR; do
      ln -s ${lickintosh-src}/assets/fonts/$family $out/share/fonts/opentype/$family
    done
  '') ];
  fonts.fontconfig.defaultFonts.emoji = lib.mkBefore [ "Apple Color Emoji" ];
  fonts.fontconfig.localConf = ''
    <match target="pattern"><test name="family" compare="eq"><string>Noto Color Emoji</string></test><edit name="family" mode="prepend" binding="strong"><string>Apple Color Emoji</string></edit></match>
  '';
  system.build.rosa-islandd = rosaIslandd;
  system.build.eqsh = eqshPackage;
  security.pam.services.eqsh-lock = { };
  system.build.riceShell = riceShell;
  security.pam.services.lickintosh-lock = { };
  security.pam.services.lickintosh-lock-fprint = { };

  # D-Bus activation is needed by the file manager's trash, metadata and removable-device backends.
  # These are filesystem capabilities; rice selection still owns all appearance/defaults.
  services.dbus.packages = [ pkgs.gvfs ];
  systemd.packages = [ pkgs.gvfs ];
  services.udisks2.enable = true;
  environment.systemPackages = [ shelfJobRunner shelfMcp desktopProfile finder finderDesktop riceFileManager quickLookOpener quickLookDesktop calculatorLauncher calculatorDesktop quickintoshAnima wallpaperBenchmark
    pkgs.noctalia-shell
    noctaliaLegacyPackage
    lickintoshPackage
    quickintoshPackage
    eqshPackage
    caelestiaPackage
    caelestiaCli
    riceShell
    riceManager
  ];

  environment.etc."nixos-rice/shells.json".source = shellManifest;
  environment.etc."nixos-rice/rices.json".source = ./rice/catalog.json;

  # Merge safe defaults into an existing hand-edited Caelestia setup. User
  # values win, so Nexus remains the source of truth after the first rebuild.
  system.activationScripts.caelestia-config = {
    deps = [ "users" ];
    text = ''
      config_dir=${riceHome}/.config/caelestia
      mkdir -p "$config_dir"
      chown ${riceUser}:users "$config_dir"

      merge_config() {
        defaults="$1"
        destination="$2"
        temporary="$destination.tmp"
        if [ -f "$destination" ]; then
          ${pkgs.jq}/bin/jq -S -s '.[0] * .[1]' "$defaults" "$destination" > "$temporary"
        else
          ${pkgs.jq}/bin/jq -S . "$defaults" > "$temporary"
        fi
        if ! ${pkgs.diffutils}/bin/cmp -s "$temporary" "$destination"; then
          ${pkgs.coreutils}/bin/mv "$temporary" "$destination"
        else
          ${pkgs.coreutils}/bin/rm -f "$temporary"
        fi
        chown ${riceUser}:users "$destination"
        chmod 600 "$destination"
      }

      merge_config ${shellDefaults} "$config_dir/shell.json"
      merge_config ${cliDefaults} "$config_dir/cli.json"
    '';
  };
}
