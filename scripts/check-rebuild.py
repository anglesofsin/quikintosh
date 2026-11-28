#!/usr/bin/env python3
"""Check tracked source inputs and helper references; does not activate a system."""
from pathlib import Path
import json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]

def check():
 tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'))
 errors=[];checked=0
 required=['flake.nix','flake.lock','nix/module.nix','nix/overlay.nix','modules/rice.nix','modules/hyprland.nix','modules/hyprland-lua/hyprland.lua','upstream/SOURCES.json','upstream/lickintosh/shell.qml','scripts/setup-defaults.py','defaults/shell-config.json']
 for name in required:
  if name not in tracked or not (ROOT/name).is_file():errors.append('Missing tracked source: '+name)
 for p in [ROOT/'flake.nix',*sorted((ROOT/'nix').glob('*.nix')),*sorted((ROOT/'modules').rglob('*.nix')),*sorted((ROOT/'packages').glob('*.nix'))]:
  text=p.read_text()
  for rel in re.findall(r'\$\{(\.{1,2}/[^}\s]+)\}',text):
   path=(p.parent/rel).resolve()
   if not path.is_relative_to(ROOT):errors.append('Source escapes repository: '+str(p.relative_to(ROOT))+' → '+rel);continue
   name=str(path.relative_to(ROOT));checked+=1
   if not path.exists():errors.append('Missing input: '+name)
   elif path.is_file() and name not in tracked:errors.append('Untracked build input: '+name)
   elif path.is_dir() and not any(x.startswith(name+'/') for x in tracked):errors.append('Untracked input directory: '+name)
  if re.search(r'/tmp/qi-|/home/pg/\.local/state/quickintosh/active-review',text):errors.append('Temporary development dependency: '+str(p.relative_to(ROOT)))
 lua=(ROOT/'modules/hyprland-lua/hyprland.lua').read_text()
 helpers=sorted(set(re.findall(r'(?:/home/pg/scripts/|/scripts/)([A-Za-z0-9_.-]+)',lua)))
 for name in helpers:
  key='modules/infinite-desktop/'+name
  if key not in tracked:errors.append('Hyprland helper is not tracked: '+key)
 lock=json.loads((ROOT/'flake.lock').read_text())
 if not lock.get('nodes',{}).get('root'):errors.append('Invalid flake lock')
 sensitive=re.compile(r'gh[pousr]_[A-Za-z0-9]{32,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|AKIA[0-9A-Z]{16}')
 for folder in ['profiles','defaults']:
  for p in (ROOT/folder).rglob('*'):
   if p.is_file() and p.suffix in ['.json','.conf','.nix']:
    text=p.read_text()
    if sensitive.search(text):errors.append('Possible credential in '+str(p.relative_to(ROOT)))
    if '/home/pg/' in text or '/tmp/qi-' in text or '/nix/store/' in text:errors.append('Machine-local path in public profile: '+str(p.relative_to(ROOT)))
 return {'trackedFiles':len(tracked)-1,'nixPathInputsChecked':checked,'hyprlandHelpersChecked':len(helpers),'errors':errors,'scope':'Static inventory; use the pinned Nix builds to validate assembly and dependencies.'}

if __name__=='__main__':
 report=check();print(json.dumps(report,indent=2));sys.exit(bool(report['errors']))
