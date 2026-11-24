"""Extract editable layers from local SVG artwork; never redraw or trace logos."""
import copy,json,re,sys,xml.etree.ElementTree as ET
from pathlib import Path
ET.register_namespace('','http://www.w3.org/2000/svg');ET.register_namespace('xlink','http://www.w3.org/1999/xlink')
SVG='{http://www.w3.org/2000/svg}'
def number(s,default=0):
 try:return float(re.sub(r'[^\d.eE+\-]','',str(s)))
 except ValueError:return default
def color(s):
 if s and re.fullmatch(r'#[a-fA-F0-9]{6}',s):return s.lower()
 return None
def luminance(c):return sum(int(c[i:i+2],16)*k for i,k in [(1,.2126),(3,.7152),(5,.0722)])/255

def extract(path):
 if path.suffix.lower()!='.svg':raise ValueError('A layered SVG is required; flattened bitmap artwork is preserved unchanged')
 root=ET.parse(path).getroot()
 for node in root.iter():
  for key,value in node.attrib.items():
   if key.lower().startswith('on') or ((key.endswith('href') or key=='src') and value.startswith(('https:','http:','file:','//'))):raise ValueError('External resources are not allowed in icon artwork')
 vb=root.get('viewBox')
 if vb:coords=list(map(float,vb.replace(',',' ').split()));w,h=coords[2:]
 else:w,h=number(root.get('width'),64),number(root.get('height'),64);vb=f'0 0 {w} {h}'
 defs=[copy.deepcopy(n) for n in root if n.tag.rsplit('}',1)[-1] in ['defs','style']]
 shapes=[n for n in root if n.tag.rsplit('}',1)[-1] in ['g','path','rect','circle','ellipse','polygon','image','use']]
 background=None;bgindex=-1
 for i,n in enumerate(shapes):
  if n.tag.endswith('rect') and number(n.get('width'))*number(n.get('height'))>=w*h*.55:background=n;bgindex=i
 # Some authoring tools wrap the full document in one group. Keep its inherited
 # transforms/styles while exposing its original children as individual layers.
 if len(shapes)==1 and shapes[0].tag.endswith('g'):
  group=shapes[0];children=[]
  for n in group:
   wrap=ET.Element(SVG+'g',group.attrib);wrap.append(copy.deepcopy(n));children.append(wrap)
  shapes=children
 candidate=background is None and bool(shapes) and shapes[0].tag.endswith('path') and shapes[0].get('fill','').startswith('url(')
 bgfill=background.get('fill') if background is not None else shapes[0].get('fill') if candidate else None
 brand=color(bgfill);gradient=[]
 if bgfill and bgfill.startswith('url('):
  identifier=bgfill.split('#',1)[-1].rstrip(')')
  for n in root.iter():
   if n.get('id')==identifier:
    gradient=[color(x.get('stop-color')) for x in n if color(x.get('stop-color'))]
  if gradient:brand=gradient[-1]
 bgcolors=[gradient[0],gradient[-1]] if gradient else [brand or '#f1f1f5']*2
 layers=[]
 for i,node in enumerate(shapes):
  if i<=bgindex:continue
  opacity=number(node.get('opacity'),1)
  if opacity<=.15:continue
  if len(layers)>=24:raise ValueError('Artwork needs layer grouping (over 24 independent surfaces)')
  canvas=ET.Element(SVG+'svg',{'width':'1024','height':'1024','viewBox':vb})
  for d in defs:canvas.append(copy.deepcopy(d))
  canvas.append(copy.deepcopy(node))
  fills=[color(n.get('fill')) for n in node.iter() if color(n.get('fill'))]
  dark=bool(fills) and all(luminance(c)<.22 for c in fills)
  layers.append({'name':node.get('id') or f'Artwork {i+1}','src':ET.tostring(canvas,encoding='unicode'),'layout':{'scale':100,'x':0,'y':0},'liquidGlass':{'enabled':True,'specular':True,'refraction':{'enabled':False},'translucency':{'enabled':False},'shadow':{'enabled':True,'value':12}},'inkDark':dark})
 if not layers:raise ValueError('No separable foreground geometry; original artwork retained')
 return {'backgroundCandidate':candidate,'brand':brand,'layers':len(layers),'recipe':{'name':path.stem,'background':{'colors':bgcolors},'layers':list(reversed(layers))}}
if __name__=='__main__':
 try:print(json.dumps(extract(Path(sys.argv[1]))))
 except Exception as e:print(str(e),file=sys.stderr);raise SystemExit(1)
