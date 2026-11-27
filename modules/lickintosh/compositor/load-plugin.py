"""Load a bundled plugin; a failure must not prevent shell startup."""
import json
import os
import subprocess
import sys
import importlib.util
import tempfile
from pathlib import Path


def configure_layers(name):
    # Also register after a first-boot plugin load, which follows Lua config.
    if name == 'hyprglass':
        result = subprocess.run(['hyprctl', 'eval',
            'if hl.plugin.hyprglass then hl.plugin.hyprglass.config({windows={background_cache=false,live_resample=true,live_resample_fps=0}}); hl.plugin.hyprglass.preset("quickintosh-dock", {inherits="pomme",blur_strength=0.65,bevel_strength=0.18,specular_strength=0.22,dark={brightness=1.0,contrast=1.0,tint_color=0x00000000},light={brightness=1.0,contrast=1.0,tint_color=0x00000000}}); hl.plugin.hyprglass.layer("quickshell:dock", '
            '{preset="quickintosh-dock",mask_mode="contour",mask_threshold=0.015,live_resample=true}); '+
            ';'.join('hl.plugin.hyprglass.layer('+json.dumps(ns)+',{mask_mode="contour",mask_threshold=0.18})' for ns in ['quickintosh-quickshot-controls','quickintosh-sharing-panel','quickintosh-status-popover'])+ ';hl.plugin.hyprglass.preset("quickintosh-island", {inherits="pomme",blur_strength=0.65,bevel_strength=0.18,specular_strength=0.22,dark={brightness=1.0,contrast=1.0,tint_color=0},light={brightness=1.0,contrast=1.0,tint_color=0}});hl.plugin.hyprglass.layer("quickintosh-island-dashboard",{preset="quickintosh-island",mask_mode="contour",mask_threshold=0.004,live_resample=true}) end'],
            capture_output=True, text=True, timeout=3)
        if len(sys.argv)>3 and result.returncode==0 and 'error' not in result.stdout.lower():
            spec=importlib.util.spec_from_file_location('native_glass',sys.argv[3])
            policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
            class Api:
                os=__import__('os')
                STATE=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'lickintosh/settings'
                @staticmethod
                def lua(value):
                    if isinstance(value,dict):return '{'+','.join('['+json.dumps(k)+']='+Api.lua(v) for k,v in value.items())+'}'
                    if isinstance(value,bool):return 'true' if value else 'false'
                    return json.dumps(value)
                @staticmethod
                def read_json(path):
                    try:
                        value=json.loads(path.read_text());return value if isinstance(value,dict) else {}
                    except (OSError,ValueError):return {}
                @staticmethod
                def write_json(path,value):
                    path.parent.mkdir(parents=True,exist_ok=True)
                    fd,tmp=tempfile.mkstemp(dir=path.parent)
                    with os.fdopen(fd,'w') as f:json.dump(value,f)
                    os.replace(tmp,path)
                @staticmethod
                def run(command):return subprocess.check_output(command,text=True,timeout=5)
            preferences=Api.read_json(Path.home()/'.config/lickintosh/core/settings-preferences.json')
            overrides=preferences.get('inputOverrides',{});overrides=overrides if isinstance(overrides,dict) else {}
            values={k:v for k,v in overrides.items() if k.startswith(policy.PREFIX)}
            policy.apply(Api,values)



def main():
    name, library = sys.argv[1:3]
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
    except Exception as error:
        print(f'Quickintosh: optional plugin load failed: {error}', file=sys.stderr)
