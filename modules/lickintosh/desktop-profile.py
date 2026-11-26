"""Reversible GTK and directory defaults, selected only for Lickintosh."""
import base64, configparser, fcntl, json, os, shutil, subprocess, sys
from pathlib import Path
from quicklook.mime_types import supported_mimes,DESKTOP_ID
os.environ.setdefault('XDG_RUNTIME_DIR','/run/user/'+str(os.getuid()))
if (Path(os.environ['XDG_RUNTIME_DIR'])/'bus').exists():os.environ.setdefault('DBUS_SESSION_BUS_ADDRESS','unix:path='+os.environ['XDG_RUNTIME_DIR']+'/bus')
HOME=Path.home(); CONFIG=HOME/'.config'; STATE=HOME/'.local/state/lickintosh/desktop-profile'
STATE.mkdir(parents=True,exist_ok=True)
FILES=['gtk-3.0/settings.ini','gtk-3.0/gtk.css','gtk-4.0/settings.ini','gtk-4.0/quickintosh-live.css','gtk-4.0/gtk.css','mimeapps.list','gtk-3.0/bookmarks','fontconfig/conf.d/60-quickintosh-fonts.conf','kitty/quickintosh-fonts.conf','kitty/kitty.conf','../.local/share/dbus-1/services/org.gnome.Nautilus.service','Code/User/settings.json','Code - Insiders/User/settings.json','VSCodium/User/settings.json','Cursor/User/settings.json','Antigravity/User/settings.json','zed/settings.json']
# Include generated application colors so leaving this rice restores previous app themes.
try:
 import tomllib
 templates=tomllib.loads((HOME/'.local/state/lickintosh/theming/templates.toml').read_text()).get('templates',{})
 for item in templates.values():
  output=Path(item['output_path']).expanduser()
  if output.is_relative_to(HOME):FILES.append(os.path.relpath(output,CONFIG))
except (OSError,ValueError,KeyError):pass
FILES=list(dict.fromkeys(FILES+['qt5ct/qt5ct.conf','qt6ct/qt6ct.conf','kdeglobals']))
NAUTILUS_KEYS=[('org.gnome.nautilus.preferences',k) for k in ['default-folder-viewer','show-image-thumbnails']]+[('org.gnome.nautilus.icon-view','default-zoom-level')]
KEYS=NAUTILUS_KEYS+[('org.gnome.desktop.interface',k) for k in ['gtk-theme','icon-theme','color-scheme','font-name','document-font-name','monospace-font-name']]+[('org.gnome.desktop.wm.preferences','button-layout')]+[('org.nemo.window-state',k) for k in ['start-with-menu-bar','start-with-status-bar','start-with-sidebar']]
def run(*args):
 try:
  return subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3)
 except (subprocess.TimeoutExpired,OSError) as error:
  # Theme services may be unavailable during login or a D-Bus reload. The
  # file-based profile still applies; optional desktop IPC must not abort login.
  print('Quickintosh profile: '+str(args[0])+' unavailable; continuing with file settings.',file=sys.stderr)
  return subprocess.CompletedProcess(args,124,stdout='',stderr=str(error))
def write(path,data):
 if path.is_file() and not path.is_symlink() and path.read_bytes()==data:return
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.rice-tmp');tmp.write_bytes(data);tmp.replace(path)
def capture():
 files={}
 for name in FILES:
  p=CONFIG/name
  files[name]={'link':os.readlink(p)} if p.is_symlink() else {'data':base64.b64encode(p.read_bytes()).decode()} if p.exists() else None
 try:rounding=json.loads(run('hyprctl','getoption','decoration:rounding','-j').stdout).get('int',12)
 except (ValueError,TypeError):rounding=12
 return {'rounding':rounding,'files':files,'settings':[[s,k,run('gsettings','get',s,k).stdout.strip()] for s,k in KEYS]}
def restore(snapshot):
 run('hyprctl','eval','hl.config({decoration={rounding='+str(int(snapshot.get("rounding",12)))+'}})')
 for name,value in snapshot['files'].items():
  p=CONFIG/name;p.parent.mkdir(parents=True,exist_ok=True)
  if value is None:p.unlink(missing_ok=True)
  elif 'link' in value:
   p.unlink(missing_ok=True);p.symlink_to(value['link'])
  else:write(p,base64.b64decode(value['data']))
 for schema,key,value in snapshot['settings']:
  if value:run('gsettings','set',schema,key,value)
def ini(path):
 c=configparser.ConfigParser(interpolation=None,strict=False);c.optionxform=str
 if path.exists():c.read(path)
 return c
def saveini(path,c):
 import io
 out=io.StringIO();c.write(out,space_around_delimiters=False);write(path,out.getvalue().encode())
def quicklook_defaults(c):
 path=STATE/'previous-openers.json'
 try:previous=json.loads(path.read_text())
 except (OSError,ValueError):previous={}
 try:
  from gi.repository import Gio
 except ImportError:Gio=None
 for mime in supported_mimes():
  configured=c['Default Applications'].get(mime,'').split(';')[0]
  app=Gio.AppInfo.get_default_for_type(mime,False) if Gio else None
  original=app.get_id() if app else configured
  if original and original!=DESKTOP_ID:previous[mime]=original
  c['Default Applications'][mime]=DESKTOP_ID+';'
  associated=[v for v in c['Added Associations'].get(mime,'').split(';') if v and v!=DESKTOP_ID]
  c['Added Associations'][mime]=';'.join([DESKTOP_ID]+associated)+';'
 write(path,json.dumps(previous).encode())
def mode():
 try:return 'light' if json.loads((CONFIG/'lickintosh/shell-config.json').read_text()).get('appearance',{}).get('mode')=='light' else 'dark'
 except (OSError,ValueError):return 'dark'
def apply(theme_root,icon_root,color):
 from wallpaper_theme import prepare
 try:options=json.loads((CONFIG/'lickintosh/shell-config.json').read_text()).get('appearance',{})
 except (OSError,ValueError):options={}
 try:palette=json.loads((HOME/'.local/state/lickintosh/theming/palette.json').read_text())
 except (OSError,ValueError):palette={}
 try:tinted=json.loads((CONFIG/'lickintosh/core/widgets.json').read_text()).get('widgetStyle')=='tinted'
 except (OSError,ValueError):tinted=False
 options=dict(options,wallpaperFileIcons=options.get('wallpaperFileIcons',False) or tinted,wallpaperTintedAccents=tinted)
 themed=prepare(HOME,theme_root,icon_root,color,options,palette)
 theme=themed['gtkTheme'];icons=themed['iconTheme']
 # Availability does not select the theme in any other rice.
 for source,dest in [(Path(theme_root)/'share/themes',HOME/'.local/share/themes'),(Path(icon_root)/'share/icons',HOME/'.local/share/icons')]:
  dest.mkdir(parents=True,exist_ok=True)
  for p in source.iterdir():
   target=dest/p.name
   if target.is_symlink():target.unlink()
   if not target.exists():target.symlink_to(p)
 for version in ['gtk-3.0','gtk-4.0']:
  c=ini(CONFIG/version/'settings.ini')
  if not c.has_section('Settings'):c.add_section('Settings')
  for key,value in {'gtk-theme-name':theme,'gtk-icon-theme-name':icons,'gtk-application-prefer-dark-theme':str(color!='light').lower(),'gtk-decoration-layout':'close,minimize,maximize:','gtk-font-name':'SF Pro Text 10'}.items():c['Settings'][key]=value
  if version=='gtk-4.0':c['Settings'].pop('gtk-application-prefer-dark-theme',None)
  saveini(CONFIG/version/'settings.ini',c)
  css=(HOME/'.local/share/themes'/theme/version/'gtk.css') if themed['gtkEnabled'] else Path(theme_root)/'share/themes'/theme/version/'gtk.css'
  stylesheet='@import url("'+str(css)+'");\n'
  if version=='gtk-4.0':
   material=(Path(__file__).with_name('finder-glass.css')).read_text()
   stylesheet+=material+'\n'+material.replace('window.nautilus-window','#NautilusFileChooser')
  write(CONFIG/version/'gtk.css',stylesheet.encode())
  if version=='gtk-4.0':
   live=themed['css']
   if themed['gtkEnabled']:
    from wallpaper_theme import gtk_accent_overrides
    live+=gtk_accent_overrides((Path(theme_root)/'share/themes'/('MacTahoe-'+color.title())/version/'gtk.css').read_text())
   material=(Path(__file__).with_name('finder-glass.css')).read_text()
   live+=material+'\n'+material.replace('window.nautilus-window','#NautilusFileChooser')
   write(CONFIG/version/'quickintosh-live.css',live.encode())
 for schema,key,value in [('org.gnome.desktop.interface','font-name','SF Pro Text 10'),('org.gnome.desktop.interface','document-font-name','SF Pro Text 10'),('org.gnome.desktop.interface','monospace-font-name','SF Mono 10'),('org.gnome.desktop.interface','gtk-theme',theme),('org.gnome.desktop.interface','icon-theme',icons),('org.gnome.desktop.interface','color-scheme','prefer-light' if color=='light' else 'prefer-dark'),('org.gnome.desktop.wm.preferences','button-layout','close,minimize,maximize:')]:run('gsettings','set',schema,key,value)
 finder_executable=shutil.which('quickintosh-finder') or shutil.which('lickintosh-finder')
 if finder_executable:
  write(HOME/'.local/share/dbus-1/services/org.gnome.Nautilus.service',('[D-BUS Service]\nName=org.gnome.Nautilus\nExec='+finder_executable+' --gapplication-service\n').encode())
 from font_preferences import apply as apply_fonts
 apply_fonts(HOME,write)
 fontconf=CONFIG/'fontconfig/conf.d/60-quickintosh-fonts.conf'
 write(fontconf,b'<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig><match target="pattern"><test name="family" compare="eq"><string>sans-serif</string></test><edit name="family" mode="prepend" binding="strong"><string>SF Pro Text</string></edit></match><match target="pattern"><test name="family" compare="eq"><string>SF Pro</string></test><edit name="family" mode="prepend" binding="strong"><string>SF Pro Text</string></edit></match><match target="pattern"><test name="family" compare="eq"><string>monospace</string></test><edit name="family" mode="prepend" binding="strong"><string>SF Mono</string></edit></match></fontconfig>')
 write(CONFIG/'kitty/quickintosh-fonts.conf',b'font_family SF Mono\nbold_font auto\nitalic_font auto\nbold_italic_font auto\n')
 kitty=CONFIG/'kitty/kitty.conf'
 if kitty.exists():
  content=kitty.read_text();line='include quickintosh-fonts.conf'
  if line not in content:write(kitty,(content.rstrip()+'\n'+line+'\n').encode())
 for app in ['qt5ct/qt5ct.conf','qt6ct/qt6ct.conf','kdeglobals']:
  path=CONFIG/app
  if not path.exists():continue
  c=ini(path);section='Icons' if app=='kdeglobals' else 'Appearance'
  if not c.has_section(section):c.add_section(section)
  c[section]['Theme' if app=='kdeglobals' else 'icon_theme']=icons
  font_section='General' if app=='kdeglobals' else 'Fonts'
  if not c.has_section(font_section):c.add_section(font_section)
  for key,family in ([('font','SF Pro Text'),('menuFont','SF Pro Text'),('toolBarFont','SF Pro Text'),('fixed','SF Mono')] if app=='kdeglobals' else [('general','SF Pro Text'),('fixed','SF Mono')]):
   c[font_section][key]=family+',10,-1,5,400,0,0,0,0,0'
  saveini(path,c)
 # Keep a separate Nautilus preference set while this rice is selected.
 if action=='enter':
  try:
   previous=json.loads((STATE/'last-lickintosh.json').read_text())
   preferences=[(s,k,v) for s,k,v in previous['settings'] if s.startswith('org.gnome.nautilus') and v]
  except (OSError,ValueError,KeyError):preferences=[]
  if not preferences:
   preferences=[('org.gnome.nautilus.preferences','default-folder-viewer','icon-view'),('org.gnome.nautilus.preferences','show-image-thumbnails','local-only'),('org.gnome.nautilus.icon-view','default-zoom-level','medium')]
  for schema,key,value in preferences:run('gsettings','set',schema,key,value)
  bookmarks=CONFIG/'gtk-3.0/bookmarks'
  text=bookmarks.read_text() if bookmarks.exists() else ''
  for name in ['Desktop','Downloads','Documents','Pictures','Music','Videos']:
   folder=HOME/name
   if folder.is_dir() and folder.as_uri() not in text:text+=('' if not text or text.endswith('\n') else '\n')+folder.as_uri()+' '+name+'\n'
  write(bookmarks,text.encode())
 c=ini(CONFIG/'mimeapps.list')
 for section in ['Default Applications','Added Associations']:
  if not c.has_section(section):c.add_section(section)
  c[section]['inode/directory']='lickintosh-finder.desktop;'
 if shutil.which('quickintosh-mac'):
  for mime in ['application/x-apple-diskimage','application/vnd.apple.installer+xml','application/x-quickintosh-macos-package','application/x-xar']:
   c['Default Applications'][mime]='quickintosh-mac-installer.desktop;'
   c['Added Associations'][mime]='quickintosh-mac-installer.desktop;'
 quicklook_defaults(c)
 try:
  overrides=json.loads((CONFIG/'lickintosh/core/settings-preferences.json').read_text()).get('defaultApps',{})
  from gi.repository import Gio
  for mime,desktop in overrides.items():
   if isinstance(mime,str) and isinstance(desktop,str) and Gio.DesktopAppInfo.new(desktop):
    c['Default Applications'][mime]=desktop+';'
    if mime=='x-scheme-handler/http':c['Default Applications']['x-scheme-handler/https']=desktop+';'
 except (OSError,ValueError,ImportError):pass
 saveini(CONFIG/'mimeapps.list',c)
with (STATE/'lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 active=STATE/'active.json';action=sys.argv[1]
 if action=='enter':
  if not active.exists():
   write(active,json.dumps(capture()).encode())
   status=HOME/'.local/state/lickintosh/theming/status.json'
   if status.exists():
    value=json.loads(status.read_text());value['success']=False;write(status,json.dumps(value).encode())
  run('hyprctl','eval','hl.config({decoration={rounding=20}})')
  try:apply(sys.argv[2],sys.argv[3],sys.argv[4] if len(sys.argv)>4 else mode())
  except Exception:
   restore(json.loads(active.read_text()));active.unlink();raise
 elif action=='leave' and active.exists():
  write(STATE/'last-lickintosh.json',json.dumps(capture()).encode())
  restore(json.loads(active.read_text()));active.unlink()
 elif action=='mode' and active.exists():apply(sys.argv[2],sys.argv[3],sys.argv[4])
