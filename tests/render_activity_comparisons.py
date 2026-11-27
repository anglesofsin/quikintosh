"""Compose actual screenshot crops; never synthesizes interface or icon artwork."""
from pathlib import Path
import json, math
from PIL import Image, ImageDraw, ImageFont
ROOT=Path('/home/pg/.local/state/quickintosh/reviews/activity-redesign')
OUT=ROOT/'comparisons';OUT.mkdir(exist_ok=True)
FONT='/nix/store/qs383gjr4y3sdirbm0gndygcrb8q2i2r-quickintosh-sf-fonts/share/fonts/opentype/SFPT/SF-Pro-Text-Regular.otf'
f=ImageFont.truetype(FONT,18);small=ImageFont.truetype(FONT,13)
reference=Image.open('/home/pg/Desktop/Screenshot_2026-11-27_09-19-27_1755x729.png').convert('RGB')
refs={
 'power':(513,101,835,176),'full':(256,241,903,382),'timer':(790,142,1064,211),'vpn':(915,236,1529,370),
 'record':(300,471,920,623),'notif':(927,461,1513,638),'brightness':(158,390,469,458),
 'volume':(1441,641,1753,727),'mute':(28,641,347,727),'focus':(539,641,725,726),'net':(727,641,1010,726),
 'tray':(1016,641,1216,726)}
oldmap={'power':'power','full':'power','low':'low','timer':'timer','alarm':'alarm','vpn':'vpn','record':'record','notif':'notif','volume':'osd','mute':'osd','brightness':'osd','bt':'bt','net':'net','focus':'focus','download':'download','cmd':'cmd','done':'done','fail':'fail','clip':'clip','print':'print','peri':'peri','keys':'keys','desk':'desk','route':'route','remind':'timer','weather':'rain'}
fixtures=json.loads((ROOT/'new/fixtures.json').read_text())
images=[]
def paste_fit(canvas,img,box,upscale=False):
 x,y,w,h=box;scale=min(w/img.width,h/img.height,2 if upscale else 1)
 img=img.resize((round(img.width*scale),round(img.height*scale)),Image.Resampling.LANCZOS)
 canvas.paste(img,(x+(w-img.width)//2,y+(h-img.height)//2))
for index,item in enumerate(fixtures):
 kind=item['kind'];key='full' if index==1 else 'volume' if index==8 else 'mute' if index==9 else 'brightness' if index==10 else kind
 old=ROOT/'old/compact'/f'{oldmap.get(key,kind)}.png';new=ROOT/'new'/f'{index:02}-{kind}.png'
 if not new.exists():continue
 columns=([('Antiga · compacta',Image.open(old).crop((710,0,1210,85)))] if old.exists() else [])
 columns.append(('Nova · compacta / expandida / laterais',Image.open(new).crop((345,45,1020,185))))
 if key in refs:columns.append(('Droppy · referência fornecida',reference.crop(refs[key])))
 canvas=Image.new('RGB',(len(columns)*520,260),'#161618');d=ImageDraw.Draw(canvas)
 d.text((20,12),item.get('title',kind),font=f,fill='white')
 for n,(title,img) in enumerate(columns):
  d.text((n*520+20,45),title,font=small,fill='#b4b4be');paste_fit(canvas,img,(n*520+12,80,496,140))
 d.text((20,238),'Capturas reais. Conteúdos e escalas de origem diferentes; referência ajustada para leitura.',font=small,fill='#a1a1a6')
 path=OUT/f'{index:02}-{key}.png';canvas.save(path);images.append(path)
for start in range(0,len(images),7):
 batch=images[start:start+7];sheet=Image.new('RGB',(1560,len(batch)*260),'#161618')
 for row,path in enumerate(batch):sheet.paste(Image.open(path),(0,row*260))
 sheet.save(ROOT/f'comparison-sheet-{start//7+1}.png')
# Contact sheets of actual integrated compact states and side combinations.
for folder in ['compact','expanded']:
 paths=sorted((ROOT/folder).glob('*.png'))
 for start in range(0,len(paths),18):
  batch=paths[start:start+18];sheet=Image.new('RGB',(1320,math.ceil(len(batch)/3)*170),'#161618');d=ImageDraw.Draw(sheet)
  for i,path in enumerate(batch):
   x=i%3*440;y=i//3*170;d.text((x+12,y+8),path.stem,font=f,fill='white')
   im=Image.open(path).crop((660,0,1260,200 if folder=='expanded' else 95));paste_fit(sheet,im,(x+6,y+34,428,130))
  sheet.save(ROOT/f'{folder}-sheet-{start//18+1}.png')
links=['# Revisão de atividades','', 'Capturas nativas em compositor privado. Dados de teste identificados; nenhuma alteração na sessão ativa.','', '## Comparações antiga | nova | Droppy','']
links += [f'- [{p.stem}]({p})' for p in images]
for folder in ['compact','expanded','new']:
 links += ['',f'## {folder}','']+[f'- [{p.stem}]({p})' for p in sorted((ROOT/folder).glob('*.png'))]
(ROOT/'INDEX.md').write_text('\n'.join(links)+'\n')
print(f'{len(images)} comparisons; index: {ROOT}/INDEX.md')

# Per-presentation comparisons keep the cards at the same pixel height so that
# reference screenshot DPI is not mistaken for a typography/size difference.
mode_links=[]
compact_ref={'power':'power','timer':'timer','brightness':'brightness','mute':'mute','volume':'volume','focus':'focus','net':'net','tray':'tray'}
expanded_ref={'full':'full','vpn':'vpn','record':'record','notif':'notif'}
old_geometry=json.loads((ROOT/'old/compact/geometry.json').read_text())
def black_bounds(im):
 rgb=im.convert('RGB');mask=Image.new('L',rgb.size)
 mask.putdata([255 if max(pixel)<12 else 0 for pixel in rgb.getdata()]);bbox=mask.getbbox()
 return rgb.crop(bbox) if bbox else rgb
for index,item in enumerate(fixtures):
 kind=item['kind'];key='full' if index==1 else 'volume' if index==8 else 'mute' if index==9 else 'brightness' if index==10 else kind
 path=ROOT/'new'/f'{index:02}-{kind}.png'
 if not path.exists():continue
 new=Image.open(path);oldkind=oldmap.get(key,kind)
 for mode in ['compact','expanded','left','right']:
  if mode=='compact':newcrop=black_bounds(new.crop((396,65,610,105)))
  elif mode=='expanded':newcrop=black_bounds(new.crop((615,45,945,350 if item.get('image') else 210)))
  elif mode=='left':newcrop=new.crop((358,68,388,98))
  else:newcrop=new.crop((978,68,1008,98))
  cols=[];old=ROOT/'old'/('expanded' if mode=='expanded' else 'compact')/(oldkind+'.png')
  if mode in ['compact','expanded'] and old.exists():
   if mode=='compact':
    geo=old_geometry.get(oldkind,{});x=geo.get('stageX',800);w=geo.get('pillWidth',280)
    crop=black_bounds(Image.open(old).crop((int(x)-4,0,int(x+w)+4,45)))
   else:
    geo=json.loads((ROOT/'old/expanded/geometry.json').read_text()).get(oldkind,{})
    x=geo.get('stageX',660);w=geo.get('pillWidth',600)
    crop=Image.open(old).crop((int(x)-8,0,int(x+w)+8,120))
   cols.append(('Antiga',crop))
  cols.append(('Nova',newcrop))
  mapping=compact_ref if mode=='compact' else expanded_ref if mode=='expanded' else {}
  if key in mapping:
   crop=black_bounds(reference.crop(refs[mapping[key]]));target=26 if mode=='compact' else 88 if key=='notif' else 64
   crop=crop.resize((round(crop.width*target/crop.height),target),Image.Resampling.LANCZOS);cols.append(('Droppy',crop))
  height=350 if item.get('image') and mode=='expanded' else 200
  card=Image.new('RGB',(len(cols)*420,height),'#161618');d=ImageDraw.Draw(card);d.text((16,8),f'{item.get("title",kind)} · {mode}',font=f,fill='white')
  for n,(label,crop) in enumerate(cols):
   d.text((n*420+16,40),label,font=small,fill='#b4b4be');paste_fit(card,crop,(n*420+12,66,396,height-90),True)
  name=f'{index:02}-{key}-{mode}.png';card.save(OUT/name);mode_links.append((name,OUT/name))
with (ROOT/'INDEX.md').open('a') as stream:
 stream.write('\n## Cada apresentação separada\n\n')
 for name,path in mode_links:stream.write(f'- [{name}]({path})\n')
print(f'{len(mode_links)} individual presentation comparisons')
