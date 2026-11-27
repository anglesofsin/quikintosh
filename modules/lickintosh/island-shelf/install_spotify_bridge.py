"""Install the queue extension in an existing Spicetify setup, preserving config."""
from pathlib import Path
import datetime,os,re,secrets,shutil

def install(home=Path.home()):
 directory=Path(home)/'.config/spicetify';config=directory/'config-xpui.ini'
 if not config.is_file():return False
 state=Path(home)/'.local/state/quickintosh/island-shelf';state.mkdir(parents=True,exist_ok=True,mode=0o700)
 token=state/'spotify-bridge-token'
 if token.is_symlink():raise ValueError('Bridge token must be a regular file')
 if not token.exists():
  fd=os.open(token,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'w') as stream:stream.write(secrets.token_urlsafe(32))
 token.chmod(0o600)
 source=(Path(__file__).with_name('quickintosh-queue.js')).read_text().replace('@LOCAL_BRIDGE_KEY@',token.read_text().strip())
 extensions=directory/'Extensions';extensions.mkdir(exist_ok=True)
 output=extensions/'quickintosh-queue.js';output.write_text(source);output.chmod(0o600)
 text=config.read_text();match=re.search(r'^(extensions\s*=\s*)(.*)$',text,re.M)
 if not match:raise ValueError('Spicetify extensions setting was not found')
 names=[item for item in match[2].strip().split('|') if item]
 if 'quickintosh-queue.js' not in names:
  backup=state/('spicetify-before-queue-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.ini');shutil.copy2(config,backup)
  names.append('quickintosh-queue.js');text=text[:match.start()]+match[1]+'|'.join(names)+text[match.end():];config.write_text(text)
 return True
if __name__=='__main__':print('Queue extension installed' if install() else 'Spicetify is not configured')

def prepare_nix_runtime(home=Path.home(),launcher=Path('/run/current-system/sw/bin/spotify')):
 """Retain the installed Nix theme; inject only our local queue extension."""
 home=Path(home);wrapper=launcher.read_text()
 match=re.search(r'"(/nix/store/[^"\n]+/share/spotify/\.spotify-wrapped)"',wrapper)
 if not match:raise ValueError('Spotify launcher does not expose a compatible Nix runtime')
 original=Path(match[1]).parent;target=home/'.local/share/spotify-spicetify/share/spotify'
 if not target.exists():shutil.copytree(original,target,symlinks=True)
 xpui=target/'Apps/xpui'
 if not (xpui/'helper/spicetifyWrapper.js').exists():raise ValueError('Installed Spotify does not include the Spicetify API')
 for directory in [target,target/'Apps',xpui]:directory.chmod(directory.stat().st_mode|0o700)
 index=xpui/'index.html';text=index.read_text()
 if 'quickintosh-queue.js' not in text:
  index.chmod(index.stat().st_mode|0o600)
  text=text.replace('</body>',"<script defer src='quickintosh-queue.js'></script></body>")
  index.write_text(text)
 extension=xpui/'quickintosh-queue.js';extension.unlink(missing_ok=True);shutil.copyfile(home/'.config/spicetify/Extensions/quickintosh-queue.js',extension);extension.chmod(0o600)
 executable=home/'.local/bin/spotify';executable.parent.mkdir(parents=True,exist_ok=True)
 executable.write_text(wrapper.replace(match[1],str(target/'.spotify-wrapped')));executable.chmod(0o700)
 desktop=home/'.local/share/applications/spotify.desktop'
 if desktop.exists():
  before=desktop.read_text();backup=home/'.local/state/quickintosh/island-shelf/spotify-desktop-before-queue.desktop'
  if not backup.exists():shutil.copy2(desktop,backup)
  after=re.sub(r'^Exec=.*$',f'Exec={executable} %U',before,flags=re.M);after=re.sub(r'^TryExec=.*$',f'TryExec={executable}',after,flags=re.M);desktop.write_text(after)
 return executable
