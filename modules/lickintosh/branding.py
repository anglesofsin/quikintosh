"""Change visible product branding without migrating IPC names or user state."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
for path in root.rglob('*'):
    if path.is_file() and path.suffix in {'.qml','.json','.desktop','.py'}:
        original=path.read_text()
        updated=original.replace('Lickintosh Quick Look','Quickintosh Quick Look') if path.suffix=='.py' else original.replace('Lickintosh','Quickintosh')
        if updated!=original:path.write_text(updated)
