"""Bounded, shared-schema preferences; never accepts icon paths or executable data."""
import json,math
from pathlib import Path
SPEC=json.loads(Path(__file__).with_name('icon_policy.json').read_text())
def sanitize(values):
 result={}
 for key,default in SPEC['defaults'].items():
  if key not in values:continue
  value=values[key]
  if isinstance(default,bool):
   if not isinstance(value,bool):raise ValueError('Icon option must be boolean')
   result[key]=value
  elif key in SPEC['sizes']:
   if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('Icon size must be finite')
   lo,hi=SPEC['sizes'][key];result[key]=max(lo,min(hi,round(value)))
  else:
   if not isinstance(value,dict):raise ValueError('Icon overrides must be an object')
   allowed=SPEC['statuses'] if key=='iconPolicyStatusOverrides' else SPEC['kinds']
   result[key]={kind:icon for kind,icon in value.items() if kind in allowed and icon in SPEC['icons'] and kind not in ('record','power','low')}
 return result
