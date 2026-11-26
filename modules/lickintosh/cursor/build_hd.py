"""Package upstream vector art as Hyprcursor assets; never upscale small PNGs."""
import json,shutil,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
source=Path(sys.argv[1]);out=Path(sys.argv[2]);work=Path(sys.argv[3])
for variant,svgdir in [('MacTahoe-cursors','svg'),('MacTahoe-dark-cursors','svg-dark')]:
 root=work/variant;shapes=root/'hyprcursors';shapes.mkdir(parents=True)
 (root/'manifest.hl').write_text(f'name = {variant}-HD\ndescription = MacTahoe original vector cursors\nversion = 1\ncursors_directory = hyprcursors\n')
 aliases={}
 for p in (source/'scalable').iterdir():
  if p.is_symlink():aliases.setdefault(p.resolve().name,[]).append(p.name)
 for p in (source/'scalable').iterdir():
  if not p.is_dir() or p.is_symlink():continue
  metadata=json.loads((p/'metadata.json').read_text());dest=shapes/p.name;dest.mkdir()
  first=source/svgdir/metadata[0]['filename'];element=ET.parse(first).getroot()
  side=float(element.get('viewBox','0 0 32 32').split()[2])
  lines=['resize_algorithm = bilinear',f"hotspot_x = {metadata[0]['hotspot_x']/side}",f"hotspot_y = {metadata[0]['hotspot_y']/side}"]
  for alias in aliases.get(p.name,[]):lines.append('define_override = '+alias)
  for frame in metadata:
   file=source/svgdir/frame['filename'];shutil.copyfile(file,dest/file.name)
   lines.append(f"define_size = 0, {file.name}, {frame.get('delay',100)}")
  (dest/'meta.hl').write_text('\n'.join(lines)+'\n')
 subprocess.run(['hyprcursor-util','--create',str(root),'--output',str(work)],check=True)
 compiled=work/('theme_'+variant+'-HD')
 shutil.copytree(compiled,out/(variant+'-HD'),dirs_exist_ok=True)
