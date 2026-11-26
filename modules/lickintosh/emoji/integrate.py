from pathlib import Path
import shutil,sys,json
root=Path(sys.argv[1]);source=Path(__file__).parent
out=root/'emoji';out.mkdir(exist_ok=True)
for name in ['catalog.json','paste.py','SOURCES.md']:shutil.copyfile(source/name,out/name)
for name,destination in [('EmojiState.qml','services'),('EmojiPicker.qml','components')]:
 p=root/destination/name;shutil.copyfile(source/name,p)
 if name=='EmojiState.qml':p.write_text(p.read_text().replace('@PYTHON@',sys.argv[2]))
 module=root/destination/'qmldir';module.write_text(module.read_text()+'\n'+('singleton ' if name=='EmojiState.qml' else '')+name[:-4]+' '+name+'\n')
p=root/'shell.qml';s=p.read_text().replace('    id: appRoot','    id: appRoot\n    EmojiPicker{}',1)
s=s.replace('function emoji(): void { LauncherState.pendingAction = "emoji"; LauncherState.requested() }','function emoji(): void { appRoot.spotlightOpened=false;appRoot.ccOpened=false;appRoot.notifCenterOpened=false;appRoot.appleMenuOpened=false;EmojiState.toggle() }',1)
s=s.replace('            appRoot.spotlightOpened = false\n            appRoot.ccOpened = false', '            EmojiState.close()\n            appRoot.spotlightOpened = false\n            appRoot.ccOpened = false',1);p.write_text(s)
p=root/'ui/topbar/statusarea/spotlight/SpotlightWindow.qml';s=p.read_text().replace('''        function onRequested() {
            if (!root.opened)''','''        function onRequested() {
            if(LauncherState.pendingAction==='emoji'){LauncherState.pendingAction='';root.closeRequested();EmojiState.toggle();return}
            if (!root.opened)''',1)
s=s.replace('function clickAction(action) {','function clickAction(action) { if(action==="emoji"){root.closeRequested();EmojiState.toggle();return} ',1);p.write_text(s)
p=root/'assets/i18n/pt_BR.json';data=json.loads(p.read_text());data.update({'Search emojis':'Buscar emojis','No emojis found':'Nenhum emoji encontrado','Skin tone':'Tom de pele','Frequently used':'Mais usados','Smileys & Emotion':'Carinhas e emoções','People & Body':'Pessoas e corpo','Animals & Nature':'Animais e natureza','Food & Drink':'Comidas e bebidas','Travel & Places':'Viagens e lugares','Activities':'Atividades','Objects':'Objetos','Symbols':'Símbolos','Flags':'Bandeiras'});p.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n')
