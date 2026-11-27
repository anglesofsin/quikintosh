from PIL import Image,ImageOps,ImageDraw,ImageFont
from pathlib import Path
root=Path('/home/pg/.local/state/quickintosh/reviews/droppy-design-review')
font=ImageFont.truetype('/nix/store/qs383gjr4y3sdirbm0gndygcrb8q2i2r-quickintosh-sf-fonts/share/fonts/opentype/SFPT/SF-Pro-Text-Regular.otf',18)
files=sorted(root.glob('page-*.png'))+sorted(root.glob('widget-*.png'))
cols=3;rows=(len(files)+cols-1)//cols
board=Image.new('RGB',(1440,rows*245),'#151518');draw=ImageDraw.Draw(board)
for i,path in enumerate(files):
 picture=Image.open(path).convert('RGB').crop((350,0,1570,600));picture=ImageOps.contain(picture,(460,205),Image.Resampling.LANCZOS)
 x=(i%cols)*480;y=(i//cols)*245
 draw.text((x+12,y+5),path.stem.replace('page-','').replace('widget-','Widget: '),font=font,fill='white');board.paste(picture,(x+10+(460-picture.width)//2,y+35))
board.save(root/'all-surfaces.png')
print(len(files),'isolated captures',root/'all-surfaces.png')
