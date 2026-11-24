"""Remove onboarding, debug controls and repeated explanations from Settings."""
from pathlib import Path
import re
import sys
root=Path(sys.argv[1])


def block_end(text,start):
    depth=0;quote=None;escaped=False;i=start
    while i<len(text):
        char=text[i]
        if quote:
            if escaped:escaped=False
            elif ord(char)==92:escaped=True
            elif char==quote:quote=None
        elif ord(char) in (34,39,96):quote=char
        elif text.startswith('//',i):
            end=text.find(chr(10),i);i=len(text) if end<0 else end;continue
        elif text.startswith('/*',i):
            end=text.find('*/',i+2);i=len(text) if end<0 else end+2;continue
        elif char=='{':depth+=1
        elif char=='}':
            depth-=1
            if depth==0:return i+1
        i+=1
    raise ValueError('Unbalanced Settings block')


def remove(name,kind,markers):
    path=root/name;text=path.read_text();spans=[]
    for match in re.finditer(r'\b'+kind+r'\s*\{',text):
        end=block_end(text,text.index('{',match.start()))
        body=text[match.start():end]
        if any(marker in body for marker in markers):spans.append((match.start(),end))
    for start,end in reversed(spans):text=text[:start]+text[end:]
    path.write_text(text)


pages='ui/settings/pages/'
remove(pages+'RosaPage.qml','RowLayout',['Test animations'])
remove(pages+'RosaPage.qml','ContentSection',['title: "Voice integration"'])
remove(pages+'AiSettingsPage.qml','ContentSection',['title: I18n.tr("Accès rapide")','title: I18n.tr("Commandes slash")'])
remove(pages+'CapturePage.qml','ContentSection',["title:'Editor shortcuts'"])
remove(pages+'CapturePage.qml','CFText',['Super+Shift+S selects a region','Filename fields:'])
remove(pages+'TopBarPage.qml','CFText',['Automatic mode chooses a light or dark foreground'])
for name in ['AppearancePage.qml','LegacyAppearancePage.qml']:
    remove(pages+name,'CFText',["Chaque réglage s'applique à l'élément choisi.",'Applique le flou choisi à toutes les fenêtres et aux couches Quickshell'])
# Keep the empty state, but remove repeated instructions for the same menu.
p=root/(pages+'DockPage.qml');s=p.read_text().replace('No blocked apps. Right-click a recent app and choose Never Show in Recents.','No excluded apps.');p.write_text(s)
p=root/'settingsapp/SettingsContent.qml';s=p.read_text().replace(",description:'The name shown by Lickintosh.'",'').replace("{description:'Path to your profile picture.'}",'{}').replace(",description:'Time before a notification banner disappears.'",'');p.write_text(s)

# Successful compositor acknowledgements are debugging information; errors stay.
for name in ['AppearancePage.qml','LegacyAppearancePage.qml']:
    p=root/(pages+name);s=p.read_text().replace(
        'visible: Theme.compositorBlur && ShellConfig.options.appearance.blurStatus.length > 0',
        'visible: Theme.compositorBlur && ShellConfig.options.appearance.blurStatus.length > 0 && ShellConfig.options.appearance.blurStatus !== "ok"')
    p.write_text(s)
