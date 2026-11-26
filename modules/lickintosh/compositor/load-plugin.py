"""Load a bundled plugin; a failure must not prevent shell startup."""
import json
import os
import subprocess
import sys


def configure_layers(name):
    # Also register after a first-boot plugin load, which follows Lua config.
    if name == 'hyprglass':
        subprocess.run(['hyprctl', 'eval',
            'if hl.plugin.hyprglass then hl.plugin.hyprglass.config({windows={background_cache=true,live_resample=true,live_resample_fps=0}}); hl.plugin.hyprglass.preset("quickintosh-dock", {inherits="pomme",blur_strength=0.65,bevel_strength=0.18,specular_strength=0.22,dark={brightness=1.0,contrast=1.0,tint_color=0x00000000},light={brightness=1.0,contrast=1.0,tint_color=0x00000000}}); hl.plugin.hyprglass.layer("quickshell:dock", '
            '{preset="quickintosh-dock",mask_mode="contour",mask_threshold=0.015,live_resample=true}) end'],
            capture_output=True, text=True, timeout=3)


def main():
    name, library = sys.argv[1:]
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        return
    plugins = json.loads(subprocess.check_output(
        ['hyprctl', 'plugins', 'list', '-j'], text=True, timeout=3
    ))
    if any(plugin.get('name') == name for plugin in plugins):
        configure_layers(name)
        return
    result = subprocess.run(
        ['hyprctl', 'plugin', 'load', library], capture_output=True, text=True, timeout=8
    )
    if result.returncode or result.stdout.strip() != 'ok':
        print(f'Quickintosh: {name} unavailable on the running compositor.', file=sys.stderr)
    else:
        configure_layers(name)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'Quickintosh: optional plugin load failed: {error}', file=sys.stderr)
