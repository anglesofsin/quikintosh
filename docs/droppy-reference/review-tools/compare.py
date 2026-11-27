from PIL import Image,ImageOps,ImageDraw,ImageFont
from pathlib import Path
out=Path('/home/pg/.local/state/quickintosh/reviews/droppy-design-review/comparisons');out.mkdir(parents=True,exist_ok=True)
qa=out.parent
font=ImageFont.truetype('/nix/store/qs383gjr4y3sdirbm0gndygcrb8q2i2r-quickintosh-sf-fonts/share/fonts/opentype/SFPT/SF-Pro-Text-Regular.otf',18)
pairs=[
 ('menu','/tmp/codex-clipboard-5r2OzT.png',(418,85,747,320),'menu-toggle-final.png',(1240,50,1510,265)),
 ('player','/tmp/codex-clipboard-zuTEgB.png',(45,10,560,290),'notch-media.png',(700,0,1220,285)),
 ('navigation','/tmp/codex-clipboard-zuTEgB.png',(230,255,435,300),'notch-media.png',(873,231,1047,276)),
 ('personalization','/tmp/codex-clipboard-YRVpQ6.png',(0,10,825,352),'personalization-refined.png',(386,0,1535,320)),
 ('files','/tmp/codex-clipboard-gYkKBF.png',(30,35,740,305),'page-tray.png',(590,0,1330,260)),
 ('audio','/tmp/codex-clipboard-HqcBwd.png',(20,10,454,320),'audio-rounded-fill.png',(730,0,1190,190)),
 ('clipboard','/tmp/codex-clipboard-TQU2rS.png',(35,30,1290,344),'page-clipboard.png',(450,0,1470,310)),
]
for name,reference,reference_crop,actual,actual_crop in pairs:
 path=qa/actual
 if not path.exists():continue
 left=Image.open(reference).convert('RGB').crop(reference_crop);right=Image.open(path).convert('RGB').crop(actual_crop)
 board=Image.new('RGB',(1440,570),'#161619');draw=ImageDraw.Draw(board)
 draw.text((24,16),'DROPPY · referência fornecida',font=font,fill='white');draw.text((744,16),'QUICKINTOSH · captura isolada atual',font=font,fill='white')
 for picture,x in [(left,20),(right,740)]:
  fitted=ImageOps.contain(picture,(680,450),Image.Resampling.LANCZOS);board.paste(fitted,(x+(680-fitted.width)//2,60+(450-fitted.height)//2))
 draw.text((24,535),'Comparação visual; conteúdos e escalas de origem diferem. Sem alterações na sessão ativa.',font=font,fill='#aaaab4')
 board.save(out/(name+'.png'))
 print(out/(name+'.png'))
