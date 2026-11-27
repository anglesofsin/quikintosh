"""Typed native glass profiles; no frame polling or client screenshot shaders."""
import math
PREFIX='native-glass:'
TARGETS=[
 {'id':'windows','label':'Application windows','namespaces':[]},
 {'id':'dock','label':'Dock','namespaces':['quickshell:dock'],'base':'quickintosh-dock','threshold':.015},
 {'id':'menubar','label':'Menu bar','namespaces':['quickshell']},
 {'id':'menus','label':'Menus and popovers','namespaces':['quickshell:applemenu','quickshell:globalmenu','quickshell:statusmenu','quickintosh-status-popover','quickintosh-sharing-panel','quickintosh:desktop-menu'],'threshold':.18},
 {'id':'cc','label':'Control Center','namespaces':['quickshell:cc']},
 {'id':'notifications','label':'Notification Center','namespaces':['quickshell:notifcenter']},
 {'id':'banners','label':'Notification banners','namespaces':['quickintosh:notification-banners']},
 {'id':'spotlight','label':'Spotlight and Launchpad','namespaces':['quickshell:spotlight']},
 {'id':'widgets','label':'Desktop widgets','namespaces':['quickshell:desktop']},
 {'id':'editor','label':'Widget editor and gallery','namespaces':['quickintosh:widget-editor','lickintosh:widget-gallery']},
 {'id':'island','label':'Dynamic Island panels','namespaces':['quickintosh-island-dashboard'],'base':'quickintosh-island','threshold':.004},
 {'id':'quickshot','label':'QuickShot controls','namespaces':['quickintosh-quickshot-controls']},
 {'id':'assistant','label':'Assistant','namespaces':['quickshell:ai']},
 {'id':'power','label':'Power and about panels','namespaces':['quickshell:power','quickshell:about']},
 {'id':'osd','label':'Volume and brightness indicators','namespaces':['quickshell:osd','quickshell:batteryosd','quickshell:btbattery']},
]
PRESETS=['pomme','clear','subtle','glass','high_contrast','default']
# name, label, group, minimum, maximum, default, step
FIELDS=[
 ('blur_strength','Blur strength','Material',0,8,1,.05),
 ('blur_iterations','Blur passes','Material',1,5,2,1),
 ('glass_opacity','Glass opacity','Material',0,1,1,.01),
 ('refraction_strength','Refraction','Material',0,8,2,.05),
 ('refraction_flow','Refraction flow','Material',0,4,1,.05),
 ('refraction_spread','Refraction spread','Material',0,4,1,.05),
 ('lens_distortion','Lens distortion','Material',0,4,0,.05),
 ('chromatic_aberration','Chromatic dispersion','Material',0,2,0,.01),
 ('edge_thickness_px','Edge width','Edges',0,80,4,1),
 ('edge_height','Edge depth','Edges',0,4,0,.05),
 ('fresnel_strength','Edge highlights','Edges',0,2,.1,.01),
 ('specular_strength','Specular highlights','Edges',0,2,.4,.01),
 ('specular_angle','Highlight angle','Edges',0,360,0,1),
 ('bevel_strength','Bevel strength','Edges',0,2,.5,.01),
 ('bevel_size','Bevel width','Edges',0,40,4,.5),
 ('bevel_angle','Bevel angle','Edges',0,360,315,1),
 ('bevel_shadow','Bevel shadow','Edges',0,1,0,.01),
 ('brightness','Brightness','Color',0,2,1,.01),
 ('contrast','Contrast','Color',0,2,1,.01),
 ('saturation','Saturation','Color',0,3,1,.01),
 ('vibrancy','Vibrancy','Color',0,2,0,.01),
 ('noise_strength','Glass grain','Color',0,1,0,.01),
]
SPECS={name:('int' if name=='blur_iterations' else 'number',lo,hi) for name,_,_,lo,hi,_,_ in FIELDS}
SPECS.update(enabled=('bool',),live_resample=('bool',),preset=('choice',PRESETS),tint_color=('int',0,0xffffffff))
OPTIONS={PREFIX+t['id']+':'+name:spec for t in TARGETS for name,spec in SPECS.items()}
GLOBAL_KEYS=['plugin:hyprglass:enabled','plugin:hyprglass:layers:enabled','plugin:hyprglass:windows:background_cache','plugin:hyprglass:windows:live_resample','plugin:hyprglass:windows:live_resample_fps','plugin:hyprglass:layers:live_resample_fps','plugin:hyprglass:layers:force_live_resample']
def validate(values):
 result={}
 for key,value in values.items():
  if key not in OPTIONS:raise ValueError('Unsupported native glass target or parameter')
  spec=OPTIONS[key]
  if spec[0]=='bool':valid=isinstance(value,bool)
  elif spec[0]=='choice':valid=value in spec[1]
  else:valid=isinstance(value,(float,int)) and not isinstance(value,bool) and math.isfinite(value) and spec[1]<=value<=spec[2] and (spec[0]!='int' or int(value)==value)
  if not valid:raise ValueError('Invalid native glass parameter: '+key)
  _,target,field=key.split(':');result.setdefault(target,{})[field]=value
 return result

def commands(api,values,previous=()):
 profiles=validate(values)
 if not profiles and not previous:return ''
 commands=['hl.plugin.hyprglass.preset("quickintosh-dock",'+api.lua({'inherits':'pomme','blur_strength':.65,'bevel_strength':.18,'specular_strength':.22,'dark':{'brightness':1.,'contrast':1.,'tint_color':0},'light':{'brightness':1.,'contrast':1.,'tint_color':0}})+')']
 commands.append('hl.plugin.hyprglass.preset("quickintosh-island",'+api.lua({'inherits': 'pomme', 'blur_strength': 0.65, 'bevel_strength': 0.18, 'specular_strength': 0.22, 'dark': {'brightness': 1.0, 'contrast': 1.0, 'tint_color': 0}, 'light': {'brightness': 1.0, 'contrast': 1.0, 'tint_color': 0}})+')')
 # hyprglass.layer replaces the whole namespace registry at commit time. Always
 # submit the complete Quickintosh baseline and all currently customized areas.
 layers={ns:{'mask_mode':'contour','mask_threshold':.18,'live_resample':True} for ns in ['quickintosh-quickshot-controls','quickintosh-sharing-panel','quickintosh-status-popover']}
 layers['quickintosh-island-dashboard']={'preset':'quickintosh-island','mask_mode':'contour','mask_threshold':.004,'live_resample':True}
 layers['quickshell:dock']={'preset':'quickintosh-dock','mask_mode':'contour','mask_threshold':.015,'live_resample':True}
 for t in TARGETS:
  target=t['id'];p=profiles.get(target);base=t.get('base','pomme');name='quickintosh-ui-'+target
  if p is None:
   if target=='windows' and target in previous:commands+=['hl.plugin.hyprglass.config({default_preset="pomme",windows={live_resample=true,background_cache=false}})','hl.window_rule({name="quickintosh-glass-windows-disabled",enabled=false})']
   continue
  definition={'inherits':p.get('preset',base)};definition.update({k:v for k,v in p.items() if k not in ('preset','enabled','live_resample')})
  if target=='menubar':definition.update(refraction_strength=0,lens_distortion=0,chromatic_aberration=0,fresnel_strength=0,specular_strength=0,bevel_strength=0)
  commands.append('hl.plugin.hyprglass.preset('+api.lua(name)+','+api.lua(definition)+')')
  if target=='windows':
   commands.append('hl.plugin.hyprglass.config('+api.lua({'default_preset':name,'windows':{'live_resample':p.get('live_resample',True)}})+')')
   commands.append('hl.window_rule('+api.lua({'name':'quickintosh-glass-windows-disabled','enabled':not p.get('enabled',True),'match':{'title':'.*'},'tag':'+hyprglass_disabled'})+')')
  else:
   layer={'preset':name,'mask_mode':'contour','mask_threshold':t.get('threshold',.001),'live_resample':p.get('live_resample',True),'exclude':not p.get('enabled',True)}
   for namespace in t['namespaces']:layers[namespace]=layer
 for namespace,settings in layers.items():commands.append('hl.plugin.hyprglass.layer('+api.lua(namespace)+','+api.lua(settings)+')')
 return 'if hl.plugin.hyprglass then '+';'.join(commands)+' end'

def apply(api,values,restore=False):
 # preset()/layer() enqueue declarations; only config.reloaded commits them.
 # A complete generated include is evaluated during the real config reload.
 path=api.STATE/'native-glass-runtime.json'
 include=api.STATE/'native-glass-config.lua'
 instance=api.os.environ.get('HYPRLAND_INSTANCE_SIGNATURE','')
 canonical={k:values[k] for k in sorted(values)} if not restore else {}
 profiles=validate(canonical)
 command=commands(api,canonical) if profiles else ''
 desired=('-- Generated native material profiles. Do not edit.\n'+command+'\n') if command else None
 previous=include.read_text() if include.exists() else None
 if desired!=previous:
  errors_before=api.run(['hyprctl','configerrors']).strip()
  def write(content):
   if content is None:include.unlink(missing_ok=True)
   else:
    temporary=include.with_suffix('.tmp')
    temporary.write_text(content);temporary.chmod(0o600);temporary.replace(include)
  write(desired)
  try:
   result=api.run(['hyprctl','reload'])
   errors=api.run(['hyprctl','configerrors']).strip()
   if 'error' in result.lower() or (errors and errors!=errors_before):raise RuntimeError(errors or result)
  except Exception:
   write(previous)
   api.run(['hyprctl','reload'])
   raise
 if restore or not profiles:path.unlink(missing_ok=True)
 else:api.write_json(path,{'instance':instance,'targets':list(profiles)})

def query(api):
 values=api.input_values(GLOBAL_KEYS)
 return {'values':values,'available':values.get('plugin:hyprglass:enabled') is not None,'targets':TARGETS,'presets':PRESETS,'fields':[dict(key=n,label=l,group=g,min=lo,max=hi,default=d,step=s) for n,l,g,lo,hi,d,s in FIELDS]}
