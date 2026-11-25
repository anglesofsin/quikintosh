{ pkgs, portal }:
let
  theme = pkgs.runCommand "quickintosh-share-picker-theme" {} ''
    install -Dm644 ${./hyprtoolkit.conf} "$out/hypr/hyprtoolkit.conf"
  '';
  styled = pkgs.runCommand "quickintosh-hyprland-portal" {
    version = pkgs.lib.getVersion portal;
    meta = portal.meta or {};
  } ''
    cp -a ${portal} "$out"
    chmod -R u+w "$out"
    while IFS= read -r file; do
      substituteInPlace "$file" --replace-quiet '${portal}' "$out"
    done < <(grep -RIlF '${portal}' "$out")
    if [ -x "$out/bin/hyprland-share-picker" ]; then
      mv "$out/bin/hyprland-share-picker" "$out/bin/.quickintosh-share-picker"
      cat > "$out/bin/hyprland-share-picker" <<SCRIPT
#!${pkgs.runtimeShell}
state_dir="\''${RICE_SHELL_STATE_DIR:-\''${XDG_STATE_HOME:-\$HOME/.local/state}/nixos-rice}"
if [ "\$(cat "\$state_dir/active-shell" 2>/dev/null)" = lickintosh ]; then
  export XDG_CONFIG_HOME='${theme}'
fi
exec "$out/bin/.quickintosh-share-picker" "\$@"
SCRIPT
      chmod +x "$out/bin/hyprland-share-picker"
    fi
  '';
in styled // { override = _: styled; }
