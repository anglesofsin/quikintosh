"""Transient primary-selection frame; no text is stored or passed as argv."""
import json,os,sys
if os.environ.get('CLIPBOARD_STATE') in ('nil','clear','sensitive'):text=''
else:text=sys.stdin.buffer.read(65537).decode(errors='replace')
if len(text)>65536:text=''
print(json.dumps(dict(text=text)),flush=True)
