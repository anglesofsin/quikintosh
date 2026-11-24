"""Explicit companion installation into an existing writable mod, without restarting Discord."""
from pathlib import Path
import argparse,runpy,sys
source=Path(sys.argv[1]);parser=argparse.ArgumentParser()
parser.add_argument('--renderer',type=Path,help='Existing desktop mod renderer.js inside your home')
args=parser.parse_args(sys.argv[2:]);module=runpy.run_path(str(source/'install-clients.py'))
if args.renderer:
    path=args.renderer.expanduser().resolve(strict=True)
    if path.name!='renderer.js' or not path.is_relative_to(Path.home()):parser.error('Choose a renderer.js belonging to an existing mod inside your home')
    module['append'](path)
    print('Companion installed; restart this Discord client when convenient. Original backup kept in ~/.local/state/nixos-rice/voice-backup.')
else:module['main']()
