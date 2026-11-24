"""Resolve the running shell after a Nix upgrade, without starting a shell."""
from pathlib import Path
import sys
fallback=sys.argv[1]
for proc in Path('/proc').iterdir():
 if not proc.name.isdecimal():continue
 try:
  args=(proc/'cmdline').read_bytes().decode().split('\0')
  if '-p' not in args or any(x in args for x in ['ipc','list','log']):continue
  path=Path(args[args.index('-p')+1])
  if '-lickintosh-source-' not in str(path) or path.name=='settings.qml':continue
  if path.name=='shell.qml' or (path.is_dir() and (path/'shell.qml').exists()):
   print(path);break
 except (OSError,ValueError,IndexError):continue
else:print(fallback)
