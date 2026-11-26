"""Final per-page design review. Retains every existing backend and setting."""
from pathlib import Path
import json,re,shutil,sys
root=Path(sys.argv[1]);source=Path(__file__).parent
for name in ['SettingsFormRow.qml','SettingsPathRow.qml']:
 shutil.copyfile(source/name,root/'settingsapp'/name)
 p=root/'settingsapp/qmldir';p.write_text(p.read_text()+'\n'+name[:-4]+' '+name+'\n')
shutil.copyfile(source/'CapturePage.qml',root/'ui/settings/pages/CapturePage.qml')

# Direct child form rows had heights as small as the combo's 28 px between
# full-height switches. Normalize those rows without touching nested grids,
# dialogs, device delegates or the behavior inside the control.
def blocks(text):
 tokens=re.finditer(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[{}]',text)
 stack=[];result=[]
 for token in tokens:
  if token[0]=='{':
   prefix=text[max(0,token.start()-90):token.start()]
   m=re.search(r'([A-Za-z_][\w.]*)\s*$',prefix)
   kind=m[1] if m else ''
   start=token.start()-len(prefix)+m.start() if m else token.start()
   parent=stack[-1][1] if stack else ''
   stack.append((start,kind,parent))
  elif token[0]=='}' and stack:
   start,kind,parent=stack.pop();result.append((start,token.end(),kind,parent))
 return result
for p in (root/'ui/settings/pages').glob('*.qml'):
 text=p.read_text();changes=[]
 for a,b,kind,parent in blocks(text):
  if kind=='RowLayout' and parent in ['ContentSection','SettingsCard']:
   changes.append((a,a+len('RowLayout'),'SettingsFormRow'))
 if changes:
  if 'import qs.settingsapp\n' not in text:
   at=text.index('import ');text=text[:at]+'import qs.settingsapp\n'+text[at:];shift=len('import qs.settingsapp\n')
  else:shift=0
  for a,b,replacement in sorted(changes,reverse=True):text=text[:a+shift]+replacement+text[b+shift:]
  p.write_text(text)

# Give long pages a useful compact index. This changes only scrolling and
# exposes every existing section, including dynamically generated island groups.
p=root/'ui/settings/widgets/ContentPage.qml';text=p.read_text()
text=text.replace('    property string pageTitle: ""','''    property string pageTitle: ""
    property var sectionItems:[]
    function rebuildSections(){sectionItems=_col.children.filter(item=>item!==sectionIndex && item.visible && typeof item.title==='string' && item.title.length>0)}
    function jumpToSection(item){root.contentItem.contentY=Math.max(0,Math.min(root.contentHeight-root.availableHeight,item.y+_col.y-8))}
    onVisibleChanged:if(visible)sectionRebuild.restart()
    Timer{id:sectionRebuild;interval:40;onTriggered:root.rebuildSections()}''')
text=text.replace('        spacing: 18','''        spacing: 18
        onChildrenChanged:sectionRebuild.restart()
        RowLayout{
            id:sectionIndex;Layout.fillWidth:true;visible:root.sectionItems.length>3
            Text{text:I18n.tr('Section');font.family:'SF Pro Text';font.pixelSize:12;color:Theme.textSecondary}
            Item{Layout.fillWidth:true}
            TahoeCombo{model:root.sectionItems.map(item=>I18n.tr(item.title));currentIndex:-1;displayText:I18n.tr('Jump to…');onActivated:index=>root.jumpToSection(root.sectionItems[index])}
        }''',1)
# The shared page previously had only qs.services imported.
text=text.replace('import qs.services\n','import qs.services\nimport qs.components\n',1);p.write_text(text)

# Legacy switch/slider wrappers use the same row separators as the compact
# native forms. The card adds no extra visual boxes or explanatory paragraphs.
for name in ['ConfigSwitch.qml','ConfigSlider.qml']:
 p=root/'ui/settings/widgets'/name;text=p.read_text().replace('separator:false','separator:true');p.write_text(text)

# Widgets dimming is a three-state enum, not a boolean switch.
p=root/'ui/settings/pages/WidgetsPage.qml';text=p.read_text().replace("SettingsRow{label:I18n.tr('Dim Widgets Behind Windows');kind:'switch';checked:WidgetState.dimWidgets;onToggled:value=>WidgetState.dimWidgets=value}","SettingsRow{label:I18n.tr('Dim Widgets');kind:'choice';choices:['Automatically','Always','Never'];selection:Math.max(0,['auto','always','never'].indexOf(WidgetState.dimWidgets));onPicked:index=>WidgetState.dimWidgets=['auto','always','never'][index]}")
text=text.replace(' id:root',''' id:root
 Component.onCompleted:{if(String(WidgetState.dimWidgets)==='true')WidgetState.dimWidgets='auto';else if(String(WidgetState.dimWidgets)==='false')WidgetState.dimWidgets='never'}''',1);p.write_text(text)

# Put the lock-screen preview first, followed by typography; keep the safety,
# notification and media controls grouped afterwards.
p=root/'ui/settings/pages/LockScreenPage.qml';text=p.read_text()
sections=[entry for entry in blocks(text) if entry[2]=='ContentSection' and entry[3]=='ContentPage']
order=['Aperçu',"Apparence de l",'Notifications','Mini lecteur','Centre de contrôle','Lock Screen Message','Automatic Locking','Démarrage']
def order_key(entry):
 content=text[entry[0]:entry[1]]
 title=re.search(r'title:\s*I18n.tr\((.*)',content)
 title=title[1] if title else ''
 return next((i for i,value in enumerate(order) if value in title),len(order))
sorted_sections=sorted(sections,key=order_key)
# Store substrings before replacement so source offsets remain valid.
replacements=[(old[0],old[1],text[new[0]:new[1]]) for old,new in zip(sections,sorted_sections)]
for a,b,content in sorted(replacements,reverse=True):text=text[:a]+content+text[b:]
p.write_text(text)

# All informational cards use the same aligned footer and restrained description
# style; multiline labels get room before their right-hand control.
p=root/'settingsapp/SettingsRow.qml';text=p.read_text().replace("font.pixelSize:11;wrapMode:Text.WordWrap","font.pixelSize:12;wrapMode:Text.WordWrap")
text=text.replace("Layout.preferredWidth:root.kind==='switch'", "Layout.maximumWidth:root.kind==='switch' ? 38:root.width*.48\n   Layout.preferredWidth:root.kind==='switch'");p.write_text(text)
p=root/'assets/i18n/pt_BR.json';data=json.loads(p.read_text());data.update({'Section':'Seção','Jump to…':'Ir para…','Screen Recording':'Gravação de tela','Save location':'Local para salvar','Recording location':'Local das gravações','File name':'Nome do arquivo','Maximum duration':'Duração máxima','Text Recognition & Translation':'Reconhecimento de texto e tradução','Recognition languages':'Idiomas de reconhecimento','Translation language':'Idioma da tradução','Dim Widgets':'Escurecer widgets'});p.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n')

# Separate Dock appearance, behavior, folders and recent apps instead of a
# single long stack of unrelated options. Preserve each existing control body.
p=root/'ui/settings/pages/DockPage.qml';text=p.read_text();entries=blocks(text)
sections=[e for e in entries if e[2]=='ContentSection' and e[3]=='ContentPage']
# Use explicit title matching to avoid interpreting labels inside the section.
selected=[e for e in sections if re.search(r'title:\s*I18n.tr\("(?:Tahoe Dock|Dock)"\)',text[e[0]:e[1]][:120])]
controls=[]
for a,b,kind,parent in entries:
 if parent=='ContentSection' and kind in ['ConfigSwitch','ConfigSlider','SettingsFormRow','RowLayout','Text','Flow','Repeater'] and any(a>section[0] and b<section[1] for section in selected):controls.append((a,b,text[a:b]))
categories={'Dock':[],'Size & Magnification':[],'Behavior':[],'Folders & Trash':[],'Recent Applications':[],'Icon Treatment':[]}
for a,b,content in sorted(controls):
 if any(key in content for key in ['recentApp','Recent application','excluded','No excluded']):group='Recent Applications'
 elif any(key in content for key in ['showTrash','confirmEmptyTrash','showDownloads','stackDisplay','showRecentFiles','stackView','stackSort']):group='Folders & Trash'
 elif any(key in content for key in ['iconSize','magnification']):group='Size & Magnification'
 elif any(key in content for key in ['iconScale','iconOverflow','iconTint','monochromeIcons']):group='Icon Treatment'
 elif any(key in content for key in ['position','dockAppearance.enable','showPinButton']):group='Dock'
 else:group='Behavior'
 categories[group].append(content)
new='\n'.join('    ContentSection{title:I18n.tr('+json.dumps(title)+')\n'+'\n'.join(content)+'\n    }' for title,content in categories.items() if content)
if selected:
 for i,(a,b,kind,parent) in reversed(list(enumerate(selected))):text=text[:a]+(new if i==0 else '')+text[b:]
 text=text.replace('    id: root','    id: root\n    DockSettingsPreview{}',1)
 p.write_text(text)
shutil.copyfile(source/'DockSettingsPreview.qml',root/'settingsapp/DockSettingsPreview.qml')
p=root/'settingsapp/qmldir';p.write_text(p.read_text()+'\nDockSettingsPreview DockSettingsPreview.qml\n')

# Put the menu-bar's most-used visibility switches before detail styling.
p=root/'ui/settings/pages/TopBarPage.qml';text=p.read_text();sections=[e for e in blocks(text) if e[2] in ['ContentSection','SettingsCard'] and e[3]=='ContentPage']
priority=['Éléments affichés','Horloge','Batterie','Menu bar background','Menu bar colors','Menu bar logo','Comportement']
def bar_key(entry):
 title=re.search(r'title:\s*I18n.tr\((.*)',text[entry[0]:entry[1]])
 value=title[1] if title else ''
 return next((i for i,name in enumerate(priority) if name in value),len(priority))
ordered=sorted(sections,key=bar_key);replacements=[(old[0],old[1],text[new[0]:new[1]]) for old,new in zip(sections,ordered)]
for a,b,content in sorted(replacements,reverse=True):text=text[:a]+content+text[b:]
p.write_text(text)

# Use the same typography for bare form labels as for SettingsRow. Previously
# these Text items inherited the platform default (often 16 px).
for p in (root/'ui/settings/pages').glob('*.qml'):
 text=p.read_text();changes=[]
 for a,b,kind,parent in blocks(text):
  if kind=='Text' and parent=='SettingsFormRow' and 'font.pixelSize' not in text[a:b]:
   at=text.index('{',a,b)+1;changes.append((at,"font.family:'SF Pro Text';font.pixelSize:13;"))
 for at,value in sorted(changes,reverse=True):text=text[:at]+value+text[at:]
 p.write_text(text)

# Keep the Dock preview beside its controls, then the desktop and widget options.
p=root/'ui/settings/pages/DockPage.qml';text=p.read_text();sections=[e for e in blocks(text) if e[2]=='ContentSection' and e[3]=='ContentPage']
def dock_key(entry):
 title=re.search(r'title:\s*I18n.tr\((.*)',text[entry[0]:entry[1]])
 value=title[1] if title else ''
 names=['Dock','Size & Magnification','Behavior','Folders & Trash','Recent Applications','Icon Treatment','Desktop','Widgets']
 return next((i for i,name in enumerate(names) if ('"'+name+'"') in value),len(names))
ordered=sorted(sections,key=dock_key);replacements=[(old[0],old[1],text[new[0]:new[1]]) for old,new in zip(sections,ordered)]
for a,b,value in sorted(replacements,reverse=True):text=text[:a]+value+text[b:]
p.write_text(text)

# Wrap type samples instead of squeezing every font into one unscrollable row.
p=root/'ui/settings/pages/LockScreenPage.qml';text=p.read_text()
text=text.replace('''            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Repeater {
                    model: LockClockStyle.styles''','''            Flow {
                Layout.fillWidth: true
                spacing: 8

                Repeater {
                    model: LockClockStyle.styles''',1)
text=text.replace('''                        Layout.fillWidth: true
                        Layout.preferredHeight: 52''','''                        width: 56
                        height: 52''',1).replace('tile.selected ? "#3478f6"','tile.selected ? Theme.accent')
p.write_text(text)
# A page-owned timer cancels the queued refresh when navigation destroys it.
p=root/'settingsapp/SettingsContent.qml';text=p.read_text().replace("onPageIdChanged:{selectedApp='';selectedPermissionApp='';Qt.callLater(root.refresh)}","onPageIdChanged:{selectedApp='';selectedPermissionApp='';pageRefresh.restart()}\n Timer{id:pageRefresh;interval:0;onTriggered:root.refresh()}");p.write_text(text)
