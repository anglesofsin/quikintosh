"""Copy chosen Unicode text, then paste only into the original focused window."""
import json,re,subprocess,sys,time
value,target=sys.argv[1:3]
if not value or len(value)>80:raise SystemExit('Invalid emoji')
subprocess.run(['wl-copy','--type','text/plain;charset=utf-8'],input=value.encode(),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=3)
if not re.fullmatch(r'0x[0-9a-fA-F]+',target) or target=='0x0':raise SystemExit(0)
time.sleep(.28)
try:
 active=json.loads(subprocess.check_output(['hyprctl','activewindow','-j'],text=True,timeout=2))
 if active.get('address')!=target:raise SystemExit(0)
 name=str(active.get('class','')).lower()
 mods='CTRL SHIFT' if any(term in name for term in ['kitty','foot','alacritty','wezterm','konsole','terminal','org.gnome.console']) else 'CTRL'
 command=';'.join('hl.dispatch(hl.dsp.send_key_state({mods="'+mods+'",key="V",state="'+state+'",window="address:'+target+'"}))' for state in ['down','up'])
 result=subprocess.run(['hyprctl','eval',command],capture_output=True,text=True,timeout=2)
 if result.returncode or 'error' in result.stdout.lower():print('Emoji copied; automatic paste unavailable: '+result.stdout.strip(),file=sys.stderr)
except (OSError,ValueError,subprocess.SubprocessError):
 print('Emoji copied; original window is unavailable',file=sys.stderr)
