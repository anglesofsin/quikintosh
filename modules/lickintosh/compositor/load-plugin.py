"""Load a bundled plugin; a failure must not prevent shell startup."""
import json
import os
import subprocess
import sys


def main():
    name, library = sys.argv[1:]
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        return
    plugins = json.loads(subprocess.check_output(
        ['hyprctl', 'plugins', 'list', '-j'], text=True, timeout=3
    ))
    if any(plugin.get('name') == name for plugin in plugins):
        return
    result = subprocess.run(
        ['hyprctl', 'plugin', 'load', library], capture_output=True, text=True, timeout=8
    )
    if result.returncode or result.stdout.strip() != 'ok':
        print(f'Quickintosh: {name} unavailable on the running compositor.', file=sys.stderr)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'Quickintosh: optional plugin load failed: {error}', file=sys.stderr)
