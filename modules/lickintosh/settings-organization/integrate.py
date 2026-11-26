"""Adapt MacShell's Settings grouping to Quickintosh's existing real pages."""
from pathlib import Path
import json,shutil,sys
root=Path(sys.argv[1]);source=Path(__file__).parent
p=root/'settingsapp/catalog.json';pages=json.loads(p.read_text())
groups=[
 ['account'],
 ['wifi','bluetooth','network','vpn'],
 ['general','appearance','wallpaper','displays','battery','accessibility'],
 ['desktop','menubar','controlcenter','widgets','island','spotlight','capture','compositor'],
 ['notifications','sound','focus','activity'],
 ['lock','privacy','users','passwords','accounts'],
 ['keyboard','mouse','trackpad','printers'],
 ['defaults','login','ai','games','about']]
pages.append(dict(id='widgets',title='Widgets',icon='dock.svg',group=3,legacy='WidgetsPage',keywords='desktop widgets gallery clock photo media lyrics weather layout edit'))
rank={name:(group,index) for group,names in enumerate(groups) for index,name in enumerate(names)}
for page in pages:
 if page['id'] in rank:
  page.pop('parent',None);page['group']=rank[page['id']][0]
pages.sort(key=lambda page:rank.get(page['id'],(99,0)))
p.write_text(json.dumps(pages,ensure_ascii=False,indent=1)+'\n')
shutil.copyfile(source/'WidgetsPage.qml',root/'ui/settings/pages/WidgetsPage.qml')
p=root/'services/SettingsCatalog.qml';s=p.read_text().replace('readonly property var sidebar:pages.filter(page=>!page.parent)','readonly property var sidebar:pages.filter(page=>!page.parent && page.id!=="account")');p.write_text(s)
p=root/'settings.qml';s=p.read_text().replace('Layout.preferredWidth:252;','Layout.preferredWidth:232;',1)
s=s.replace("'#202124';radius:0","'#1e1e1e';radius:0",1)
s=s.replace('Layout.preferredHeight:74','Layout.preferredHeight:56',1)
s=s.replace("font.family:'SF Pro Display';font.pixelSize:23;font.weight:Font.Bold", "font.family:'SF Pro Text';font.pixelSize:16;font.weight:Font.DemiBold",1)
s=s.replace('implicitHeight:32;leftPadding:13;rightPadding:10;', 'implicitHeight:28;leftPadding:11;rightPadding:10;',1)
s=s.replace("background:Rectangle{radius:16;color:Theme.isLight ? '#18000000':'#15ffffff'}", "background:Rectangle{radius:7;color:Theme.isLight ? '#18000000':'#15ffffff';border.width:search.activeFocus ? 2:0;border.color:Qt.rgba(Theme.accent.r,Theme.accent.g,Theme.accent.b,.6)}",1)
needle='     ListView{\n      id:sidebar;'
profile='''     Rectangle{
      Layout.fillWidth:true;Layout.preferredHeight:62;radius:8
      color:window.route==='account' ? Theme.accent:accountMouse.containsMouse ? Theme.fillHover:'transparent'
      RowLayout{anchors.fill:parent;anchors.margins:7;spacing:10
       ProfileAvatar{Layout.preferredWidth:38;Layout.preferredHeight:38;source:ProfileState.avatarUrl || Quickshell.shellDir+'/assets/icons/settings/user.svg'}
       ColumnLayout{Layout.fillWidth:true;spacing:3
        Text{Layout.fillWidth:true;text:ProfileState.displayName || I18n.tr('Your Account');font.family:'SF Pro Text';font.pixelSize:13;font.weight:Font.DemiBold;color:window.route==='account' ? 'white':Theme.textPrimary;elide:Text.ElideRight}
        Text{text:I18n.tr('Local Account');font.family:'SF Pro Text';font.pixelSize:11;color:window.route==='account' ? '#cfffffff':Theme.textSecondary}
       }
      }
      MouseArea{id:accountMouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:window.navigate('account')}
     }
'''
assert needle in s;s=s.replace(needle,profile+needle,1)
s=s.replace("? 14:0)+(modelData.id==='account' ? 64:35)","? 12:0)+(modelData.id==='account' ? 64:33)",1)
s=s.replace("height:modelData.id==='account' ? 60:35;radius:8", "height:modelData.id==='account' ? 60:33;radius:6",1)
p.write_text(s)
p=root/'settingsapp/SettingsCard.qml';s=p.read_text().replace('radius:14','radius:10').replace("'#f3f3f6':'#25272a'","'#ffffff':'#2b2b2d'").replace('increaseContrast ? 2:0','increaseContrast ? 2:1').replace("'#15000000':'#20ffffff'","'#12000000':'#10ffffff'").replace('column.implicitHeight+12','column.implicitHeight+4').replace('topMargin:6','topMargin:2').replace('leftMargin:16;rightMargin:16','leftMargin:14;rightMargin:14');p.write_text(s)
p=root/'settingsapp/SettingsRow.qml';s=p.read_text().replace('description ? 64:48','description ? 60:44').replace('labels.implicitHeight+22','labels.implicitHeight+20');p.write_text(s)
p=root/'ui/settings/widgets/ContentPage.qml';s=p.read_text().replace('y: 20','y: 16').replace('spacing: 20','spacing: 18');p.write_text(s)
p=root/'settingsapp/SettingsContent.qml';s=p.read_text().replace('y:12;spacing:22','y:16;spacing:18')
s=s.replace("result.push(card('',SettingsCatalog.childPages('general').map(page=>nav(page.id))))", """result.push(card('System',[nav('about'),nav('updates'),nav('storage')]))
   result.push(card('Language & Time',[nav('language'),nav('datetime')]))
   result.push(card('Applications',[nav('defaults'),nav('login')]))
   result.push(card('Services',[nav('sharing'),nav('backups')]))""")
p.write_text(s)
p=root/'assets/i18n/pt_BR.json';data=json.loads(p.read_text());data.update({'Services':'Serviços','Language & Time':'Idioma e hora','Show Widgets':'Mostrar widgets','Dim Widgets Behind Windows':'Escurecer widgets atrás das janelas','Free Placement with Control':'Posicionamento livre com Control','Avoid Desktop Icons':'Evitar ícones da mesa','Widget Gallery':'Galeria de widgets','Personalization':'Personalização'});p.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n')
