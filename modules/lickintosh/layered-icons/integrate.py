from pathlib import Path
import shutil,sys
r=Path(sys.argv[1]);h=Path(__file__).parent
out=r/'layered-icons';out.mkdir(exist_ok=True)
for n in ['artwork.py','fast-renderer.py']:shutil.copyfile(h/n,out/n)
s=(h/'LayeredIcons.qml').read_text()
for a,b in zip(['@PYTHON@','@RSVG@'],sys.argv[2:4]):s=s.replace(a,b)
(r/'services/LayeredIcons.qml').write_text(s)
def save(n,s):
 p=r/n;p.chmod(p.stat().st_mode|0o200);p.write_text(s)
p=r/'services/qmldir';save('services/qmldir',p.read_text()+'\nsingleton LayeredIcons LayeredIcons.qml\n')
# The previous full-image treatment is removed, never stacked with materials.
for name in ['tahoedock/DockTile.qml','ui/desktop/DesktopIcon.qml','ui/dock/Dock.qml','ui/topbar/statusarea/spotlight/SpotlightResults.qml']:
 p=r/name;s=p.read_text();import re
 s=re.sub(r'layer.enabled:AppearanceState.treatment>0[^\n]*','layer.enabled:false',s)
 if name=='tahoedock/DockTile.qml':s=s.replace("source:root.entry.icon || ''","source:LayeredIcons.resolve(root.entry.icon || '',root.entry.key || root.entry.name)")
 if name=='ui/dock/Dock.qml':s=s.replace('source:          iconItem.appIconPath','source:          LayeredIcons.resolve(iconItem.appIconPath,iconItem.groupKey || iconItem.appName)')
 save(name,s)
p=r/'services/IconResolver.qml';s=p.read_text().replace('var value = root.retheme(Quickshell.iconPath(name, true))','var value = root.retheme(Quickshell.iconPath(name, true))');s=s.replace('return root.iconCache[key]','return LayeredIcons.resolve(root.iconCache[key],name)').replace('        return value\n','        return LayeredIcons.resolve(value,name)\n');save('services/IconResolver.qml',s)
p=r/'ui/settings/pages/AppearanceControls.qml';s=p.read_text();s=s.replace("label:'Style intensity'","label:'Layer material intensity'");save('ui/settings/pages/AppearanceControls.qml',s)

# Every surface resolves through the same reactive service, including the
# previously hardcoded Launchpad tile and app grid.
p=r/'tahoedock/DockIcons.qml';s=p.read_text();s=s.replace("return path ? 'file://'+Quickshell.shellDir+'/'+path : IconResolver.byName(name)","return LayeredIcons.resolve(path ? 'file://'+Quickshell.shellDir+'/'+path : IconResolver.byName(name),name)");save('tahoedock/DockIcons.qml',s)
p=r/'ui/dock/Dock.qml';s=p.read_text().replace('return Qt.resolvedUrl("file://" + Quickshell.shellDir + "/assets/pngs/launchpad.png")','return LayeredIcons.resolve("file://" + Quickshell.shellDir + "/assets/pngs/launchpad.png","launchpad")');save('ui/dock/Dock.qml',s)
# IconResolver's absolute-path branch must be reactive too.
p=r/'services/IconResolver.qml';s=p.read_text().replace('return root.retheme(source)','return LayeredIcons.resolve(root.retheme(source),source)').replace('return root.retheme("file://" + source)','return LayeredIcons.resolve(root.retheme("file://" + source),source)');save('services/IconResolver.qml',s)

p=r/'ui/topbar/statusarea/spotlight/SpotlightCategoryGrid.qml';s=p.read_text();s=re.sub(r'layer.enabled:AppearanceState.tinted[^\n]*','layer.enabled:false',s);save('ui/topbar/statusarea/spotlight/SpotlightCategoryGrid.qml',s)
