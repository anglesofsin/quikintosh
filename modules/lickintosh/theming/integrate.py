from pathlib import Path
import shutil,sys
root=Path(sys.argv[1]);here=Path(__file__).parent
shutil.copytree(here,root/'theming',ignore=shutil.ignore_patterns('integrate.py','__pycache__'))
p=root/'theming/WallpaperTheming.qml';p.chmod(0o644);p.write_text(p.read_text().replace('@PYTHON@',sys.argv[2]).replace('@LEGACY@',sys.argv[3]))
p=root/'shell.qml';s=p.read_text();s='import qs.theming\n'+s;s=s.replace('    id: appRoot','    id: appRoot\n    WallpaperTheming {enabled:appRoot.interfaceShown && !lockScreen.locked}',1);p.write_text(s)
