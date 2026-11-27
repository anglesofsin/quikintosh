"""Contact sheets and reference comparisons from unaltered native UI captures."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFont
import math
root=Path('/home/pg/.local/state/quickintosh/reviews/media-polish');out=root/'comparisons';out.mkdir(exist_ok=True)
font=ImageFont.truetype('/nix/store/qs383gjr4y3sdirbm0gndygcrb8q2i2r-quickintosh-sf-fonts/share/fonts/opentype/SFPT/SF-Pro-Text-Regular.otf',20)
def crop(path):
 im=Image.open(path).convert('RGB');background=Image.new('RGB',im.size,im.getpixel((0,0)));bbox=ImageChops.difference(im,background).convert('L').point(lambda x:255 if x>12 else 0).getbbox()
 return im.crop(bbox) if bbox else im
paths=sorted(root.glob('*.png'))
for start in range(0,len(paths),8):
 sheet=Image.new('RGB',(1600,math.ceil(len(paths[start:start+8])/2)*420),'#18181b');d=ImageDraw.Draw(sheet)
 for n,path in enumerate(paths[start:start+8]):
  x=n%2*800;y=n//2*420;d.text((x+16,y+12),path.stem,font=font,fill='white');im=crop(path);im.thumbnail((768,366),Image.Resampling.LANCZOS);sheet.paste(im,(x+(800-im.width)//2,y+48))
 sheet.save(out/f'sheet-{start//8+1}.png')
refs=[('queue','/home/pg/Desktop/Screenshot_2026-11-27_15-29-27_405x566.png','floating-player-queue.png'),('calendar','/tmp/codex-clipboard-6ON18v.png','calendar.png'),('floating','/tmp/codex-clipboard-Agyie7.png','floating-player-player.png')]
for key,ref,ours in refs:
 if not Path(ref).exists():continue
 sheet=Image.new('RGB',(1040,740),'#18181b');d=ImageDraw.Draw(sheet)
 for x,label,path in [(0,'DROPPY · referência fornecida',Path(ref)),(520,'QUICKINTOSH · captura isolada',root/ours)]:
  d.text((x+18,16),label,font=font,fill='white');im=crop(path);im.thumbnail((480,650),Image.Resampling.LANCZOS);sheet.paste(im,(x+(520-im.width)//2,66))
 sheet.save(out/(key+'.png'))
lines=['# Media — revisão visual','','Capturas nativas em compositor privado, com serviço MPRIS de teste. Conteúdos e estados não representam a fila ou os dados pessoais da sessão real.','', '## Comparações com referência','']
lines += [f'- [{key}]({out}/{key}.png)' for key,_,_ in refs]
lines += ['','## Visões gerais','']+[f'- [Folha {i}]({out}/sheet-{i}.png)' for i in range(1,math.ceil(len(paths)/8)+1)]
lines += ['','## Capturas individuais','']+[f'- [{path.stem}]({path})' for path in paths]
(root/'INDEX.md').write_text('\n'.join(lines)+'\n');print('NATIVE_MEDIA_CAPTURES',len(paths))
