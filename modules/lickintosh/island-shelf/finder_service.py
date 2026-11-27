"""File-manager bridge: only explicitly selected local URIs are forwarded."""
import base64,json,os,subprocess,sys
from urllib.parse import urlparse
from pathlib import Path

def selection(environment,arguments):
    values=environment.get('NAUTILUS_SCRIPT_SELECTED_URIS','').splitlines() or arguments
    values=[Path(value).as_uri() if value.startswith('/') else value for value in values]
    return [value for value in values if value and urlparse(value).scheme=='file' and urlparse(value).netloc in ('','localhost')][:256]

def main():
    floating='--floating' in sys.argv
    values=selection(os.environ,[a for a in sys.argv[1:] if a!='--floating'])
    if not values:return 0
    encoded=base64.b64encode(json.dumps(values,ensure_ascii=True).encode()).decode()
    result=subprocess.run(['quickintosh','ipc','call','shelf','addFloatingFiles' if floating else 'addFiles',encoded],capture_output=True,text=True,timeout=15)
    if result.returncode:raise RuntimeError('Could not reach the Quickintosh file tray')
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,RuntimeError,subprocess.SubprocessError) as error:
        print(str(error),file=sys.stderr);raise SystemExit(1)
