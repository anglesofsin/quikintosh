{ inputs }:
{ pkgs, ... }:
let
  inherit (inputs) hyprland-src noctalia-src nixpkgs-patched;
  system = pkgs.stdenv.hostPlatform.system;

  # Copy only the patch contents into their own store paths. An unrelated edit
  # elsewhere in this repository therefore cannot invalidate these packages.
  hyprlandPatch = builtins.path {
    path = ../modules/hyprland-seethrough.patch;
    name = "hyprland-seethrough.patch";
  };
  noctaliaPatch = builtins.path {
    path = ../modules/noctalia-brightness-cooldown.patch;
    name = "noctalia-brightness-cooldown.patch";
  };

  # This package set is intentionally pinned to an exact nixpkgs commit and
  # does not follow the operating system's rolling nixpkgs input.
  patchedPkgs = import nixpkgs-patched {
    inherit system;
    config.allowUnfree = true;
  };

  upstreamHyprland = hyprland-src.packages.${system}.hyprland;
  modernHyprland = pkgs.lib.versions.majorMinor upstreamHyprland.version == "0.57";
  patchedHyprland = upstreamHyprland.overrideAttrs (old: {
    patches = (old.patches or [ ]) ++ (if modernHyprland then [
      ../modules/hyprland-0.57-seethrough.patch
      ../modules/hyprland-0.57-workspace-viewport.patch
    ] else [ hyprlandPatch ../modules/hyprland-workspace-viewport.patch ]);
    # v0.56.2's lock already supplies Glaze 8, but its CMake range still
    # rejects version 8 and tries an impure network fetch. Upstream removed
    # that stale upper bound after the tag; keep this conditional for both the
    # tagged checkout and newer revisions where the fix is already present.
    postPatch = (old.postPatch or "") + ''
      if grep -qF 'find_package(glaze 7...<8 QUIET)' CMakeLists.txt; then
        substituteInPlace CMakeLists.txt \
          --replace-fail 'find_package(glaze 7...<8 QUIET)' 'find_package(glaze QUIET)'
      fi
    '';
  });
  # The portal itself does not need recompilation for the compositor patch.
  # Reuse its cached binary and only rewrite wrapper references so commands
  # such as hyprctl resolve to the patched Hyprland selected by this system.
  cachedHyprlandPortal =
    if modernHyprland then hyprland-src.packages.${system}.xdg-desktop-portal-hyprland
    else patchedPkgs.xdg-desktop-portal-hyprland;
  matchedHyprlandPortalBase =
    patchedPkgs.runCommand "xdg-desktop-portal-hyprland-${cachedHyprlandPortal.version}-matched" { }
      ''
        cp -a ${cachedHyprlandPortal} "$out"
        chmod -R u+w "$out"

        while IFS= read -r file; do
          if grep -qF '${cachedHyprlandPortal}' "$file"; then
            substituteInPlace "$file" \
              --replace-fail '${cachedHyprlandPortal}' "$out"
          fi
        done < <(grep -RIl '${cachedHyprlandPortal}' "$out")

        # Only the legacy portal wrapper embeds a compositor path.
        ${pkgs.lib.optionalString (!modernHyprland) ''
          while IFS= read -r file; do
            if grep -qF '${patchedPkgs.hyprland}' "$file"; then
              substituteInPlace "$file" \
                --replace-fail '${patchedPkgs.hyprland}' '${patchedHyprland}'
            fi
          done < <(grep -RIl '${patchedPkgs.hyprland}' "$out")
        ''}
      '';
  # The NixOS Hyprland module probes package.override before using the portal.
  # Expose a no-op override because the wrapper references are already fixed.
  matchedHyprlandPortal = matchedHyprlandPortalBase // {
    override = _args: matchedHyprlandPortalBase;
  };

  patchedNoctalia = noctalia-src.packages.${system}.default.overrideAttrs (old: {
    patches = (old.patches or [ ]) ++ [ noctaliaPatch ];
  });

  patchedNoctaliaShell =
    (patchedPkgs.runCommand "noctalia-shell-${patchedNoctalia.version}" { } ''
      mkdir -p $out/bin $out/share
      ln -s ${patchedNoctalia}/bin/noctalia $out/bin/noctalia
      ln -s noctalia $out/bin/noctalia-shell
      for dir in ${patchedNoctalia}/share/*; do
        base=$(basename "$dir")
        [ "$base" = noctalia ] && ln -s "$dir" "$out/share/noctalia-shell"
        [ -e "$out/share/$base" ] || ln -s "$dir" "$out/share/$base"
      done
      for dir in ${patchedNoctalia}/*; do
        base=$(basename "$dir")
        if [ "$base" != bin ] && [ "$base" != share ]; then
          ln -s "$dir" "$out/$base"
        fi
      done
    '')
    // {
      inherit (patchedNoctalia) version;
    };
in {
  nixpkgs.overlays = [(final: prev: {
    hyprland = patchedHyprland;
    xdg-desktop-portal-hyprland = matchedHyprlandPortal;
    noctalia-shell = patchedNoctaliaShell;
  })];
}
