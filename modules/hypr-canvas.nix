{ pkgs, lib, hyprland }:
let
  modern = lib.versions.majorMinor hyprland.version == "0.57";
  compiler = if modern then hyprland.stdenv else pkgs.stdenv;
in
compiler.mkDerivation {
    pname = "hypr-canvas";
    version = "0.1-a5f9cda";

    src = pkgs.fetchFromGitHub {
      owner = "aaronsb";
      repo = "hypr-canvas";
      rev = "a5f9cdaccb864db094a6a978498bb77c7e90fc53";
      hash = "sha256-75c/soq/YF2KQCTNR2GgnfgHCeCG0ZCNX1phissdDX8=";
    };

    patches = [ ./hypr-canvas-mode-gated-reset.patch ] ++ lib.optionals modern [ ./hypr-canvas-057.patch ./hypr-canvas-monitor-render.patch ];

    postPatch = ''
      ${lib.optionalString modern "sed -i 's/-std=c++2b/-std=c++26/' Makefile"}
      substituteInPlace src/canvas.cpp \
        --replace-fail '    m_mouseButtonHook = hookByName("onMouseButton", (void*)&hkOnMouseButton);' '    m_mouseButtonHook = nullptr;' \
        --replace-fail '    m_mouseMovedHook  = hookByName("onMouseMoved", (void*)&hkOnMouseMoved);' '    m_mouseMovedHook  = nullptr;'
    '';

    nativeBuildInputs = with pkgs; [ pkg-config ];
    buildInputs = lib.optionals modern hyprland.buildInputs ++ (with pkgs; [
      hyprland.dev
      aquamarine
      hyprcursor
      hyprgraphics
      hyprlang
      hyprutils
      glslang
      pixman
      libdrm
      libglvnd
      libinput
      wayland
      wayland-protocols
      cairo
      libxkbcommon
      libxcb
      libxcb-errors
      xorg.xcbutilwm
      xorg.xcbutilrenderutil
    ]);

    NIX_CFLAGS_COMPILE = lib.optionalString modern "-I${hyprland.dev}/include/hyprland/protocols";
    makeFlags = [ "CXX=${compiler.cc.targetPrefix}c++" ];

    installPhase = ''
      runHook preInstall
      mkdir -p $out/lib/hyprland
      cp hypr-canvas.so $out/lib/hyprland/hypr-canvas.so
      runHook postInstall
    '';
  }
