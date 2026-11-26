"""Opt-in Matugen colors layered over the existing Tahoe GTK/icon artwork."""
import colorsys
import configparser
import hashlib
import json
import re
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

VERSION=6
HEX=re.compile(r'#[0-9a-fA-F]{6}$')
COLOR=re.compile(r'#[0-9a-fA-F]{6}(?![0-9a-zA-Z])|#[0-9a-fA-F]{3}(?![0-9a-zA-Z])')
STYLE=re.compile(r'((?:fill|stroke|stop-color|flood-color|color)\s*:\s*)(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})(?![0-9a-zA-Z])')

def write(path,text):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 if path.is_file() and not path.is_symlink() and path.read_text()==text:return
 temp=path.with_name(path.name+'.tmp');temp.write_text(text);temp.replace(path)

def palette_for(palette,mode):
 colors=palette.get(mode,{})
 required=['primary','on_primary','surface','on_surface','surface_container','surface_container_low','surface_container_high','surface_container_highest','outline_variant']
 if not all(HEX.fullmatch(str(colors.get(k,''))) for k in required):return {}
 return {k:v for k,v in colors.items() if isinstance(v,str) and HEX.fullmatch(v)}

def gtk_colors(c,full=True):
 names={
 'accent_color':'primary','accent_bg_color':'primary','accent_fg_color':'on_primary',
 'window_bg_color':'surface_container_low','window_fg_color':'on_surface',
 'view_bg_color':'surface','view_fg_color':'on_surface','headerbar_bg_color':'surface_container',
 'headerbar_fg_color':'on_surface','headerbar_backdrop_color':'surface_container_low',
 'sidebar_bg_color':'surface_container','sidebar_fg_color':'on_surface',
 'sidebar_backdrop_color':'surface_container_low','sidebar_border_color':'outline_variant',
 'card_bg_color':'surface_container','card_fg_color':'on_surface',
 'popover_bg_color':'surface_container_high','popover_fg_color':'on_surface',
 'dialog_bg_color':'surface_container_high','dialog_fg_color':'on_surface',
 'theme_bg_color':'surface_container_low','theme_fg_color':'on_surface',
 'theme_base_color':'surface','theme_text_color':'on_surface',
 'selected_bg_color':'primary','selected_fg_color':'on_primary',
 'theme_selected_bg_color':'primary','theme_selected_fg_color':'on_primary',
 'theme_unfocused_bg_color':'surface_container_low','theme_unfocused_fg_color':'on_surface',
 'theme_unfocused_base_color':'surface','theme_unfocused_text_color':'on_surface',
 'theme_unfocused_selected_bg_color':'surface_container_highest','theme_unfocused_selected_fg_color':'on_surface',
 'borders':'outline_variant','unfocused_borders':'outline_variant',
 }
 if not full:names={k:v for k,v in names.items() if k.startswith('accent') or 'selected' in k}
 return '\n/* Quickintosh wallpaper palette; Tahoe geometry remains unchanged. */\n'+''.join('@define-color '+key+' '+('#ffffff' if key in ['accent_fg_color','selected_fg_color','theme_selected_fg_color','theme_unfocused_selected_fg_color'] else c[role])+';\n' for key,role in names.items())+'''
selection { background-color: @accent_bg_color; color: @accent_fg_color; }
:root { --accent-bg-color: @accent_bg_color; --accent-color: @accent_color; --accent-fg-color: @accent_fg_color; }
window.nautilus-window .navigation-sidebar row:selected,
window.nautilus-window .navigation-sidebar row:selected label,
window.nautilus-window .navigation-sidebar row:selected image { color: #ffffff; }
window.nautilus-window .nautilus-grid-view child:selected label,
window.nautilus-window .nautilus-list-view row:selected label { color: #ffffff; }
window.nautilus-window .nautilus-grid-view child:selected:focus,
window.nautilus-window .nautilus-grid-view child:selected:focus-within,
window.nautilus-window .nautilus-grid-view child:selected > * { outline-color: @accent_color; }
window.nautilus-window .nautilus-grid-view child:selected { outline-color: @accent_color; border-color: @accent_color; }
button.suggested-action { background-image: none; background-color: @accent_bg_color; color: @accent_fg_color; }
switch:checked { background-color: @accent_bg_color; border-color: @accent_bg_color; }
'''

def gtk_accent_overrides(source):
 # Tahoe hard-codes its accent into rules as well as named colors. Override
 # only those declarations, retaining original layout, assets and materials.
 output=[]
 for match in re.finditer(r'([^{}]+)\{([^{}]*)\}',source):
  declarations=[]
  for declaration in match[2].split(';'):
   if re.search(r'#0088ff\b',declaration,re.I):declarations.append(re.sub(r'#0088ff\b','@accent_bg_color',declaration,flags=re.I).strip()+';')
  if declarations:output.append(match[1].strip()+' { '+' '.join(declarations)+' }')
 return '\n'.join(output)+'\n'

def recolor_svg(text,accent):
 rgb=tuple(int(accent[i:i+2],16)/255 for i in (1,3,5));hue,light,saturation=colorsys.rgb_to_hls(*rgb)
 def color(value):
  if not COLOR.fullmatch(value):return value
  raw=value[1:];raw=''.join(c*2 for c in raw) if len(raw)==3 else raw
  r,g,b=(int(raw[i:i+2],16)/255 for i in (0,2,4));h,l,s=colorsys.rgb_to_hls(r,g,b)
  # Recolor the theme's blue/cyan material, retaining paper, glyphs, shadows,
  # colored MIME badges and the original gradient/geometry.
  if not (.47<=h<=.73 and s>.18):return value
  target_l=max(.18,min(.94,light+(l-.65)*.7))
  target_s=max(.12,min(1,saturation))
  return '#'+''.join(f'{round(v*255):02x}' for v in colorsys.hls_to_rgb(hue,target_l,target_s))
 # Keep namespaces, gradient references, filters and serialization untouched.
 # QtSvg and GTK must read exactly the same original artwork structure.
 ET.fromstring(text)  # Reject malformed input before producing an overlay.
 changed=False
 def attribute(match):
  nonlocal changed
  original=match[3];updated=color(original)
  if updated!=original:changed=True
  return match[1]+match[2]+updated+match[2]
 output=re.sub(r'((?:fill|stroke|stop-color|flood-color|color)\s*=\s*)(["\'])(#[0-9a-fA-F]{3,6})\2',attribute,text)
 def style(match):
  nonlocal changed
  updated=color(match[2])
  if updated!=match[2]:changed=True
  return match[1]+updated
 output=STYLE.sub(style,output)
 return output if changed else None

def managed_slot(parent,current):
 name='Quickintosh-Wallpaper-'+('B' if current=='Quickintosh-Wallpaper-A' else 'A')
 path=parent/name
 if path.exists():
  if not (path/'.quickintosh-generated.json').is_file():raise ValueError('Refusing to replace a user theme: '+str(path))
  shutil.rmtree(path)
 path.mkdir(parents=True)
 return name,path

def prepare(home,theme_root,icon_root,mode,options,palette):
 home=Path(home);theme_root=Path(theme_root);icon_root=Path(icon_root)
 base_theme='MacTahoe-'+mode.title();base_icons='MacTahoe-'+mode
 state=home/'.local/state/lickintosh/theming/finder.json'
 try:previous=json.loads(state.read_text())
 except (OSError,ValueError):previous={}
 colors=palette_for(palette,mode)
 signature=hashlib.sha256(json.dumps([VERSION,mode,colors,str(theme_root),str(icon_root),bool(options.get("wallpaperGtk"))],sort_keys=True).encode()).hexdigest()
 result={'gtkTheme':base_theme,'iconTheme':base_icons,'gtkEnabled':False,'iconsEnabled':False,'icons':{},'signature':signature}
 if colors and (options.get('wallpaperGtk',False) or options.get('wallpaperTintedAccents',False)):
  if previous.get('gtkEnabled') and previous.get('signature')==signature and (home/'.local/share/themes'/previous['gtkTheme']/'gtk-4.0/gtk.css').is_file():
   result['gtkTheme']=previous['gtkTheme']
  else:
   name,folder=managed_slot(home/'.local/share/themes',previous.get('gtkTheme'))
   for version in ['gtk-3.0','gtk-4.0']:
    source=theme_root/'share/themes'/base_theme/version/'gtk.css'
    overlay=gtk_colors(colors,options.get('wallpaperGtk',False))+gtk_accent_overrides(source.read_text())
    if version=='gtk-3.0':overlay=re.sub(r':root\s*\{[^}]*\}','',overlay).replace(':focus-within',':focus')
    write(folder/version/'gtk.css','@import url("'+str(source)+'");\n'+overlay)
   write(folder/'.quickintosh-generated.json',json.dumps({'signature':signature,'base':base_theme}))
   result['gtkTheme']=name
  result['gtkEnabled']=True
 if colors and options.get('wallpaperFileIcons',False):
  if previous.get('iconsEnabled') and previous.get('signature')==signature and (home/'.local/share/icons'/previous['iconTheme']/'index.theme').is_file():
   result.update(iconTheme=previous['iconTheme'],icons=previous['icons'],iconsEnabled=True)
  else:
   name,folder=managed_slot(home/'.local/share/icons',previous.get('iconTheme'));source=icon_root/'share/icons'/base_icons
   directories=set();icons={};converted={};names={}
   for area in ['places','mimes','places@2x','mimes@2x']:
    if not (source/area).is_dir():continue
    for svg in sorted((source/area).rglob('*.svg')):
     if 'symbolic' in svg.parts:continue
     # Preserve explicit named folder-color alternatives chosen by the user.
     if re.fullmatch(r'folder-(?:black|blue|brown|cyan|green|grey|orange|pink|purple|red|violet|white|yellow)',svg.stem):continue
     real=svg.resolve()
     if real not in converted:
      try:converted[real]=recolor_svg(svg.read_text(),colors['primary'])
      except (OSError,ET.ParseError):converted[real]=None
     text=converted[real]
     if text is None:continue
     relative=svg.relative_to(source);write(folder/relative,text);directories.add(str(relative.parent))
     priority=2 if 'scalable' in svg.parts and '@2x' not in area else 1
     if priority>names.get(svg.stem,0):icons[svg.stem]=str(folder/relative);names[svg.stem]=priority
   parser=configparser.ConfigParser(interpolation=None);parser.optionxform=str;parser.read(source/'index.theme')
   parser['Icon Theme']['Name']=name;parser['Icon Theme']['Inherits']=base_icons+',hicolor'
   parser['Icon Theme']['Directories']=','.join(sorted(directories));parser['Icon Theme'].pop('ScaledDirectories',None)
   for section in list(parser.sections()):
    if section!='Icon Theme' and section not in directories:parser.remove_section(section)
   import io
   out=io.StringIO();parser.write(out);write(folder/'index.theme',out.getvalue())
   write(folder/'.quickintosh-generated.json',json.dumps({'signature':signature,'base':base_icons}))
   result.update(iconTheme=name,icons=icons,iconsEnabled=True)
 result['css']=gtk_colors(colors,options.get('wallpaperGtk',False)) if result['gtkEnabled'] else ''
 write(state,json.dumps({k:v for k,v in result.items() if k!='css'},sort_keys=True))
 return result
