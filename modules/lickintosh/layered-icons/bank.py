"""Index pinned, downloaded renditions. Never synthesize light/dark artwork."""
from pathlib import Path
import json,sys,subprocess
from concurrent.futures import ThreadPoolExecutor
root,apple,fallback=map(Path,sys.argv[1:4]);bank={m:{} for m in ['light','dark','clear']}
def norm(s):return s.lower().removesuffix('.desktop').removesuffix('.svg').removesuffix('.png').replace(' ','-').replace('_','-')
# Linux counterparts retain their own app logos. Only direct system counterparts
# (Finder, Settings, Launchpad, etc.) use the Apple design-resource artwork.
aliases={
 'Finder':['system-file-manager','file-manager','org.gnome.nautilus','nautilus','nemo'],
 'System Settings':['preferences-system','settings-app','settings','org.quickshell'],
 'Launch Pad':['launchpad','view-app-grid','applications-all'],
 'Trash Empty':['user-trash','trash-empty'],'Trash Full':['user-trash-full','trash-full'],
 'folder':['folder','inode-directory'],'Folder download':['folder-download','folder-downloads'],
 'Terminal':['utilities-terminal'], 'Calculator':['accessories-calculator','org.gnome.calculator'],
 'Calendar':['x-office-calendar','org.gnome.calendar'], 'Clock':['org.gnome.clocks'],
 'TextEdit':['accessories-text-editor','org.gnome.texteditor'], 'Preview':['document-preview'],
 'Spotify':['spotify','spotify-client'], 'Firefox':['firefox','firefox-nightly'],
 'Telegram':['telegram','telegram-desktop','org.telegram.desktop'],
 'code':['code','vscode','visual-studio-code'], 'obs':['obs','com.obsproject.studio'],
}
for mode in ['light','dark']:
 for area in ['apps','places']:
  for p in sorted((fallback/'prebuilt'/mode.title()/area).rglob('*.svg')):
   if p.is_file():bank[mode][norm(p.stem)]=str(p)
# The repository identifies this directory as Apple's design-resource artwork.
for mode in bank:
 for directory in [apple/'icon'/mode.title(),apple/'macOS Tahoe 26/icons'/mode.title()]:
  if not directory.exists():continue
  for p in sorted(directory.glob('*.png')):
   keys=[p.stem]+aliases.get(p.stem,[])
   for key in keys:bank[mode][norm(key)]=str(p)
# No fabricated dark folder: share the provided light rendition when absent.
for key in ['folder','inode-directory','folder-download','folder-downloads']:
 if key in bank['light']:bank['dark'].setdefault(key,bank['light'][key])
(root/'layered-icons/bank.json').write_text(json.dumps(bank,separators=(',',':')))
# Desktop-file icon names differ between distributions and Discord channels.
compat={'zen':'zen-browser','app.zen-browser.zen':'zen-browser','zen-twilight':'zen-browser','brave-browser':'brave','com.brave.browser':'brave','discord-canary':'discord','discord-ptb':'discord','com.discordapp.discord':'discord','discordcanary':'discord','discordptb':'discord','org.gnome.nautilus':'finder'}
for mode,table in bank.items():
 for alias,target in compat.items():
  if target in table:table[alias]=table[target]
(root/'layered-icons/bank.json').write_text(json.dumps(bank,separators=(',',':')))

# QtSvg supports fewer SVG features than librsvg. Rasterize downloaded artwork
# once at build time; retain original vectors for material-mask preparation.
vectors={}
def prepare_native(item):
 mode,source=item;p=Path(source);dest=root/'layered-icons/native'/mode/(norm(p.stem)+'.png');dest.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run([sys.argv[4],'-w','192','-h','192',str(p),'-o',str(dest)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 return mode,source,str(dest)
items={(mode,path) for mode in ['light','dark'] for path in bank[mode].values() if path.endswith('.svg')}
with ThreadPoolExecutor(max_workers=4) as pool:
 for mode,source,dest in pool.map(prepare_native,sorted(items)):
  vectors[dest]=source
  for key,value in list(bank[mode].items()):
   if value==source:bank[mode][key]=dest
bank['vectors']=vectors
(root/'layered-icons/bank.json').write_text(json.dumps(bank,separators=(',',':')))
