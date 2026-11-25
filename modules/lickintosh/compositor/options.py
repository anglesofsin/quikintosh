"""Strict compositor policy: typed options, named window rules, reversible runtime."""
import json,math,re
OPTIONS={
 'decoration:rounding':('int',0,50), 'decoration:rounding_power':('number',2,10),
 'general:border_size':('int',0,12),'general:gaps_in':('int',0,80),'general:gaps_out':('int',0,120),
 'general:layout':('choice',['dwindle','master','scrolling']),
 'decoration:active_opacity':('number',.1,1),'decoration:inactive_opacity':('number',.1,1),'decoration:fullscreen_opacity':('number',.1,1),
 'decoration:dim_inactive':('bool',),'decoration:dim_strength':('number',0,1),
 'decoration:blur:enabled':('bool',),'decoration:blur:size':('int',1,40),'decoration:blur:passes':('int',1,8),
 'decoration:blur:new_optimizations':('bool',),'decoration:blur:ignore_opacity':('bool',),
 'decoration:blur:xray':('bool',),'decoration:blur:noise':('number',0,1),
 'decoration:blur:contrast':('number',0,2),'decoration:blur:brightness':('number',0,2),'decoration:blur:vibrancy':('number',0,1),
 'decoration:shadow:enabled':('bool',),'decoration:shadow:range':('int',0,100),'decoration:shadow:render_power':('number',1,5),
 'animations:enabled':('bool',),'input:follow_mouse':('int',0,3),'misc:focus_on_activate':('bool',),
 'misc:vfr':('bool',),'misc:animate_manual_resizes':('bool',),'misc:animate_mouse_windowdragging':('bool',),
}
OPTIONS.update({
 'plugin:hyprglass:enabled':('bool',),
 'plugin:hyprglass:default_preset':('choice',['default','clear','subtle','glass','pomme','high_contrast']),
 'plugin:hyprglass:blur_strength':('number',0,8), 'plugin:hyprglass:blur_iterations':('int',1,5),
 'plugin:hyprglass:refraction_strength':('number',0,8),'plugin:hyprglass:chromatic_aberration':('number',0,2),
 'plugin:hyprglass:glass_opacity':('number',0,1),'plugin:hyprglass:noise_strength':('number',0,1),
 'plugin:hyprglass:specular_strength':('number',0,2),'plugin:hyprglass:fresnel_strength':('number',0,2),
 'plugin:hyprglass:self_sample':('number',0,1),'plugin:hyprglass:xray':('bool',),
 'plugin:hyprglass:edge_thickness_px':('number',0,80),
})

RULE_FIELDS={'glass':('choice',['inherit','off','clear','subtle','glass','pomme','high_contrast']),'activeOpacity':('number',.1,1),'inactiveOpacity':('number',.1,1),'rounding':('int',0,50),'borderSize':('int',0,12),'noBlur':('bool',),'noShadow':('bool',),'noAnimations':('bool',)}
def typed(value,spec):
 if spec[0]=='bool':
  if not isinstance(value,bool):raise ValueError('Expected boolean')
 elif spec[0]=='choice':
  if value not in spec[1]:raise ValueError('Unsupported choice')
 else:
  if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not spec[1]<=value<=spec[2]:raise ValueError('Value outside supported range')
  if spec[0]=='int' and int(value)!=value:raise ValueError('Expected integer')
 return value

def lua(value):
 if isinstance(value,dict):return '{'+','.join('['+json.dumps(k)+']='+lua(v) for k,v in value.items())+'}'
 if isinstance(value,bool):return 'true' if value else 'false'
 return json.dumps(value,ensure_ascii=False)

def rule_table(rule,index):
 if not isinstance(rule,dict):raise ValueError('Invalid window rule')
 app=rule.get('app','');title=rule.get('title','')
 if not isinstance(app,str) or not 1<=len(app)<=200 or not isinstance(title,str) or len(title)>200:raise ValueError('Choose an application class')
 if any(ord(c)<32 for c in app+title):raise ValueError('Control characters are not supported')
 match={'class':'^'+re.escape(app)+'$','title':'.*'}
 if title:match['title']='^'+re.escape(title)+'$'
 data={'name':'quickintosh-user-'+str(index),'match':match,'enabled':True}
 for k,spec in RULE_FIELDS.items():
  if k in rule:typed(rule[k],spec)
 if 'activeOpacity' in rule or 'inactiveOpacity' in rule:data['opacity']=f"{rule.get('activeOpacity',1):.3f} {rule.get('inactiveOpacity',1):.3f}"
 for key,target in [('rounding','rounding'),('borderSize','border_size'),('noBlur','no_blur'),('noShadow','no_shadow'),('noAnimations','no_anim')]:
  if key in rule:data[target]=rule[key]
 return data

def rule_commands(rules,previous=0):
 if not isinstance(rules,list) or len(rules)>100:raise ValueError('At most 100 rules are supported')
 commands=[]
 for i in range(max(len(rules),previous)):
  name='quickintosh-user-'+str(i)
  if i<len(rules):
   table=rule_table(rules[i],i);commands.append('hl.window_rule('+lua(table)+')')
   style=rules[i].get('glass','inherit')
   tags=['+hyprglass_disabled'] if style=='off' else [] if style=='inherit' else ['+hyprglass_enabled','+hyprglass_preset_'+style]
   for j in range(2):
    tagRule={'name':name+'-glass-'+str(j),'enabled':j<len(tags)}
    if j<len(tags):tagRule.update(match=table['match'],tag=tags[j])
    commands.append('hl.window_rule('+lua(tagRule)+')')
  else:
   for suffix in ['', '-glass-0','-glass-1']:commands.append('hl.window_rule('+lua({'name':name+suffix,'enabled':False})+')')
 return ';'.join(commands)

def option_value(key,value):
 if key in {'general:gaps_in','general:gaps_out'} and isinstance(value,str):
  parts=[int(n) for n in value.split()]
  if len(parts)==1:parts*=4
  elif len(parts)==2:parts*=2
  elif len(parts)==3:parts.append(parts[1])
  if len(parts)!=4:raise ValueError('Invalid four-sided spacing')
  return dict(zip(['top','right','bottom','left'],parts))
 return value

def read_config(path):
 try:value=json.loads(path.read_text())
 except (OSError,ValueError):value={}
 return value if isinstance(value,dict) else {}

def query(api):
 values=api.input_values(OPTIONS)
 for key in ['general:gaps_in','general:gaps_out']:
  if isinstance(values.get(key),str):
   parts=values[key].split();values[key]=int(parts[0]) if parts and len(set(parts))==1 else None
 clients=json.loads(api.run(['hyprctl','clients','-j']))
 return {'values':values,'options':OPTIONS,'rules':read_config(api.HOME/'.config/lickintosh/core/compositor.json').get('rules',[]),
         'applications':sorted({c.get('class','') for c in clients if c.get('class')}),
         'hyprimate':any(p.get('name') in ['hyprimate','liquid-glass'] for p in json.loads(api.run(['hyprctl','plugins','list','-j'])))}

def apply_rules(api,rules=None,restore=False):
 path=api.STATE/'compositor-rules-runtime.json';record=api.read_json(path)
 instance=api.os.environ.get('HYPRLAND_INSTANCE_SIGNATURE','')
 if record.get('instance')!=instance:record={'instance':instance,'count':0}
 if rules is None:rules=read_config(api.HOME/'.config/lickintosh/core/compositor.json').get('rules',[])
 if restore:rules=[]
 command=rule_commands(rules,record.get('count',0))
 if command:
  result=api.run(['hyprctl','eval',command])
  if 'error' in result.lower():raise RuntimeError(result)
 api.write_json(path,{'instance':instance,'count':len(rules)})

def save_rules(api,rules):
 rule_commands(rules)
 previous=read_config(api.HOME/'.config/lickintosh/core/compositor.json')
 apply_rules(api,rules)
 api.write_json(api.HOME/'.config/lickintosh/core/compositor.json',dict(previous,rules=rules))
 return query(api)
