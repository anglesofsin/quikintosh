from pathlib import Path
import shutil,sys
root=Path(sys.argv[1]);here=Path(__file__).parent
shutil.copyfile(here/'WallpaperFiles.qml',root/'services/WallpaperFiles.qml')
p=root/'services/qmldir';p.write_text(p.read_text()+'\nsingleton WallpaperFiles WallpaperFiles.qml\n')
p=root/'services/ShellConfig.qml';s=p.read_text();anchor='property JsonObject appearance: JsonObject {';assert anchor in s
s=s.replace(anchor,anchor+'\n                property bool wallpaperGtk:false\n                property bool wallpaperFileIcons:false',1);p.write_text(s)
p=root/'services/IconResolver.qml';s=p.read_text();anchor='    function byName(name) {';assert anchor in s
s=s.replace(anchor,anchor+"\n        const wallpaperIcon=WallpaperFiles.resolve(name)\n        if(wallpaperIcon)return wallpaperIcon",1)
anchor='    function resolve(source) {';assert anchor in s
s=s.replace(anchor,anchor+"\n        const wallpaperIcon=WallpaperFiles.forSource(source)\n        if(wallpaperIcon)return wallpaperIcon",1);p.write_text(s)
p=root/'services/LayeredIcons.qml';s=p.read_text();anchor="  let path=String(source || '')";assert anchor in s
s=s.replace(anchor,anchor+"\n  if(path.indexOf('/icons/Quickintosh-Wallpaper-')>=0)return source",1);p.write_text(s)

for p in root.rglob('*.qml'):
 if p.is_symlink():continue
 s=p.read_text()
 updated=s.replace('font.family: "JetBrainsMono Nerd Font ExtraBold"','font.family: "SF Pro Text"').replace("font.family:'JetBrainsMono Nerd Font ExtraBold'","font.family:'SF Pro Text'")
 if updated!=s:p.write_text(updated)
