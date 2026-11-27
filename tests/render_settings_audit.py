"""Build comparisons exclusively from actual private Settings captures."""
from pathlib import Path
import json,math,os
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(os.environ.get('QI_SETTINGS_REVIEW_DIR','/home/pg/.local/state/quickintosh/reviews/settings-tahoe-audit'))
f=ImageFont.truetype('/nix/store/qs383gjr4y3sdirbm0gndygcrb8q2i2r-quickintosh-sf-fonts/share/fonts/opentype/SFPT/SF-Pro-Text-Regular.otf',20)
s=ImageFont.truetype('/nix/store/qs383gjr4y3sdirbm0gndygcrb8q2i2r-quickintosh-sf-fonts/share/fonts/opentype/SFPT/SF-Pro-Text-Regular.otf',13)
a=json.loads((ROOT/'before/report.json').read_text());b=json.loads((ROOT/'after/report.json').read_text())
out=ROOT/'comparisons';out.mkdir(exist_ok=True)
notes={
'battery':'Página refeita: resumo da alimentação, saúde, economia, histórico real e dispositivos conectados.',
'wifi':'Corrigida a sobreposição de clique gerenciada indevidamente pelo layout.',
'glass':'Rota de compatibilidade: abre Appearance, conforme o catálogo existente.',
'island':'Corrigido carregamento; formato, navegação, ícones, chamadas e controles avançados separados.',
'appearance':'Prévia sem wallpaper vazio; margens e grupos consistentes.',
'capture':'Campos de pasta sem layout recursivo; dimensões estáveis.',
'desktop':'Valores dos controles legíveis; espaçamento e cartões consistentes.',
'compositor':'Unidades dos controles sem corte; grupos e margens consistentes.',
'lock':'Porcentagens legíveis; espaçamento e cartões consistentes.',
'mouse':'Tempos sem truncamento; proporções e cartões consistentes.',
'about':'Informações longas podem quebrar linha; valores legíveis.',
}
paths=[]
def crop(im,geo):
 w,h=round(geo['width']),round(geo['height']);x=(im.width-w)//2;y=(im.height-h)//2
 return im.crop((x,y,x+w,y+h))
for key,old in a.items():
 if key not in b:continue
 for suffix in ['', '-bottom']:
  before=ROOT/'before'/(key+suffix+'.png');after=ROOT/'after'/(key+suffix+'.png')
  if not before.exists() or not after.exists():continue
  title=old['page']['title'];canvas=Image.new('RGB',(2040,840),'#161618');d=ImageDraw.Draw(canvas)
  d.text((20,12),title+(' · final da página' if suffix else ''),font=f,fill='white');d.text((20,48),'ANTES',font=s,fill='#b4b4be');d.text((1040,48),'DEPOIS',font=s,fill='#b4b4be')
  for phase,pos,geo in [('before',20,old['geometry']),('after',1040,b[key]['geometry'])]:
   im=crop(Image.open(ROOT/phase/(key+suffix+'.png')),geo);im.thumbnail((980,740),Image.Resampling.LANCZOS);canvas.paste(im,(pos,78))
  path=out/(key+suffix+'.png');canvas.save(path)
  if not suffix:paths.append(path)
for start in range(0,len(paths),8):
 batch=paths[start:start+8];sheet=Image.new('RGB',(2040,math.ceil(len(batch)/2)*420),'#161618')
 for i,path in enumerate(batch):
  im=Image.open(path);im.thumbnail((1020,420));sheet.paste(im,(i%2*1020,i//2*420))
 sheet.save(ROOT/f'comparison-sheet-{start//8+1}.png')
lines=['# Settings — revisão visual','',f'{len(paths)} rotas conferidas em compositor privado (48 páginas e a rota de compatibilidade glass → Appearance). Antes e depois nativos, sem mockups.','',
'As páginas usam os componentes compartilhados corrigidos. Os estados de hardware refletem a sessão isolada; não foram feitas alterações de rede, contas, segurança ou arquivos do usuário.','', '| Página | Resultado | Comparação |','|---|---|---|']
for path in paths:
 key=path.stem;title=a[key]['page']['title'];note=notes.get(key,'Página revisada; organização existente preservada, com ajustes compartilhados quando aplicáveis.')
 lines.append(f'| {title} | {note} | [Antes e depois]({path}) |')
if (ROOT/'after/battery-notebook.png').exists():lines+=['',f'Bateria com dados de notebook de teste: [prévia]({ROOT}/after/battery-notebook.png).']
lines+=['','## Visões gerais','']+[f'- [Folha {i}]({ROOT}/comparison-sheet-{i}.png)' for i in range(1,math.ceil(len(paths)/8)+1)]+['','## Relatórios','',f'- [Antes]({ROOT}/before/report.json)',f'- [Depois]({ROOT}/after/report.json)']
(ROOT/'INDEX.md').write_text('\n'.join(lines)+'\n');print('SETTINGS_COMPARISONS',len(paths))
