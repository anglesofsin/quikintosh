"""Strict compositor policy: typed options, named window rules, reversible runtime."""
import json,math,re
from pathlib import Path
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

HYPRIMATE_FIELDS = json.loads(Path(__file__).with_name('hyprimate-settings.json').read_text())
HYPRIMATE_OPTIONS = {}
for field in HYPRIMATE_FIELDS:
 key = 'plugin:hyprimate:' + field['path'].replace('.', ':')
 field['key'] = key
 kind = field['type']
 if kind == 'boolean':
  spec = ('bool',)
 elif kind in ('float', 'int'):
  spec = ('number' if kind == 'float' else 'int', field.get('min', -10000), field.get('max', 10000))
 elif kind == 'color':
  spec = ('plugin-color',)
 elif kind == 'set':
  spec = ('plugin-set', field['choices'])
 elif kind == 'string' and field.get('choices'):
  spec = ('choice', field['choices'])
 else:
  spec = ('plugin-text',)
 HYPRIMATE_OPTIONS[key] = spec

OPTIONS.update({
 'plugin:hyprglass:windows:background_cache': ('bool',),
 'plugin:hyprglass:windows:live_resample': ('bool',),
 'plugin:hyprglass:windows:live_resample_fps': ('int', 0, 360),
})

def equivalent(key, first, second):
 if HYPRIMATE_OPTIONS.get(key, (None,))[0] == 'plugin-color':
  return option_value(key, first) == option_value(key, second)
 if key in {'general:gaps_in', 'general:gaps_out'}:
  if isinstance(first, (int, float)):
   first = {side: first for side in ('top', 'right', 'bottom', 'left')}
  else:
   first = option_value(key, first)
  if isinstance(second, (int, float)):
   second = {side: second for side in ('top', 'right', 'bottom', 'left')}
  else:
   second = option_value(key, second)
 if isinstance(first, float) or isinstance(second, float):
  if isinstance(first, (int, float)) and isinstance(second, (int, float)):
   return math.isclose(first, second, rel_tol=1e-6, abs_tol=1e-6)
 return first == second


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
 if HYPRIMATE_OPTIONS.get(key, (None,))[0] == 'plugin-color' and isinstance(value, str):
  return int(value.removeprefix('#').removeprefix('0x'), 16)
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

NATIVE_PREFIX = 'workspace-animation:'
NATIVE_STYLES = ('slide', 'slidevert', 'fade', 'slidefade', 'slidefadevert')
NATIVE_LEAVES = ('workspacesIn', 'workspacesOut')


def native_workspace_info(api):
    animations, curves = json.loads(api.run(['hyprctl', 'animations', '-j']))
    items = {item['name']: item for item in animations}
    parent = next((items[name] for name in ('workspaces', 'global') if items.get(name, {}).get('overridden')), {})
    leaves = {name: items[name] if items.get(name, {}).get('overridden') else parent for name in NATIVE_LEAVES}
    return leaves, sorted({'default', *(item['name'] for item in curves)})


def native_workspace_values(api, state=None):
    leaves, curves = state if state is not None else native_workspace_info(api)
    entry = leaves[NATIVE_LEAVES[0]]
    style = (entry.get('style') or 'slide').split()
    distance = int(style[-1][:-1]) if re.fullmatch(r'[0-9]+%', style[-1]) else 100
    direction = next((word for word in style[1:] if word in ('left', 'right', 'top', 'bottom')), '')
    return dict(
        style=style[0] if style[0] in NATIVE_STYLES else 'slide',
        speed=entry.get('speed') or 5, curve=entry.get('bezier') or 'default',
        distance=distance, direction=direction, enabled=entry.get('enabled', True),
        curves=curves,
    )


def native_leaf_command(leaf, settings):
    assert leaf in NATIVE_LEAVES
    enabled = settings.get('enabled', True)
    table = {'leaf': leaf, 'enabled': enabled}
    if enabled:
        curve = settings.get('bezier') or 'default'
        table.update(speed=settings.get('speed') or 5, style=settings.get('style') or '')
        if curve.startswith('spring:'):
            table['spring'] = curve.removeprefix('spring:')
        else:
            table['bezier'] = curve
    return 'hl.animation(' + lua(table) + ')'


def apply_native_workspace(api, overrides, restore=False):
    path = api.STATE / 'workspace-animation-runtime.json'
    instance = api.os.environ.get('HYPRLAND_INSTANCE_SIGNATURE', '')
    saved = api.read_json(path)
    same_instance = saved.get('instance') == instance
    if restore or not overrides:
        if same_instance:
            result = api.run(['hyprctl', 'eval', ';'.join(
                native_leaf_command(leaf, saved['original'][leaf]) for leaf in NATIVE_LEAVES)])
            if 'error' in result.lower():
                raise RuntimeError(result)
        path.unlink(missing_ok=True)
        return
    leaves, curves = native_workspace_info(api)
    if not same_instance:
        saved = {'instance': instance, 'original': leaves}
    current = native_workspace_values(api, (leaves, curves))
    current.update(overrides)
    style = typed(current['style'], ('choice', NATIVE_STYLES))
    enabled = typed(current['enabled'], ('bool',))
    speed = typed(current['speed'], ('number', .1, 100))
    distance = typed(current['distance'], ('int', 0, 200))
    direction = typed(current['direction'], ('choice', ('', 'left', 'right', 'top', 'bottom')))
    curve = typed(current['curve'], ('choice', [*curves, *(leaf.get('bezier') for leaf in leaves.values())]))
    if style != 'fade':
        style = ' '.join(filter(None, (style, direction, f'{int(distance)}%')))
    target = {'style': style, 'enabled': enabled, 'speed': speed, 'bezier': curve}
    if saved.get('applied') == target and all(
        item.get('enabled') == enabled and (not enabled or
        (item.get('style') == style and item.get('bezier') == curve and item.get('speed') == speed))
        for item in leaves.values()
    ):
        return
    api.write_json(path, saved)
    result = api.run(['hyprctl', 'eval', ';'.join(native_leaf_command(leaf, target) for leaf in NATIVE_LEAVES)])
    if 'error' in result.lower():
        raise RuntimeError(result)
    api.write_json(path, dict(saved, applied=target))


def query(api):
 plugins=json.loads(api.run(['hyprctl','plugins','list','-j']))
 hyprimate=any(p.get('name')=='hyprimate' for p in plugins)
 values=api.input_values(OPTIONS.keys() | (HYPRIMATE_OPTIONS.keys() if hyprimate else set()))
 for key in ['general:gaps_in','general:gaps_out']:
  if isinstance(values.get(key),str):
   parts=values[key].split();values[key]=int(parts[0]) if parts and len(set(parts))==1 else None
 clients=json.loads(api.run(['hyprctl','clients','-j']))
 return {'values':values,'options':OPTIONS,'rules':read_config(api.HOME/'.config/lickintosh/core/compositor.json').get('rules',[]),
         'applications':sorted({c.get('class','') for c in clients if c.get('class')}),
         'workspaceNative':native_workspace_values(api), 'hyprimate':hyprimate,'animationFields':HYPRIMATE_FIELDS if hyprimate else []}

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
