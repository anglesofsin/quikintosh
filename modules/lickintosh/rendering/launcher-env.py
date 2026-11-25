"""Print only allowlisted environment settings for this shell process."""
import json,os
from pathlib import Path
try:
 data=json.loads((Path(os.environ['HOME'])/'.config/lickintosh/shell-config.json').read_text())
 mode=data.get('performance',{}).get('renderer','auto')
except (OSError,ValueError,KeyError,TypeError,AttributeError):mode='auto'
if mode not in ('auto','threaded','basic'):mode='auto'
print(mode)
