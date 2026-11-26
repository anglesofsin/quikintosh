"""Apply the Settings presentation after behavior and compatibility patches."""
from pathlib import Path
import shutil,sys,json
root=Path(sys.argv[1]);source=Path(__file__).parent
shutil.copyfile(source/'AppearanceControls.qml',root/'ui/settings/pages/AppearanceControls.qml')
p=root/'ui/settings/pages/LegacyAppearancePage.qml';s=p.read_text().replace('property bool advanced:false','readonly property bool advanced:appearanceControls.advanced')
s=s.replace('AppearanceControls{}','AppearanceControls{id:appearanceControls}')
s=s.replace('    TahoeButton{text:root.advanced ? "Hide advanced settings":"Advanced settings…";onClicked:root.advanced=!root.advanced}\n','')
s=s.replace('title: I18n.tr("Interface Scale")','title: I18n.tr("Interface Scale")\n        visible:root.advanced',1);p.write_text(s)
p=root/'settings.qml';s=p.read_text()
s=s.replace('Layout.preferredWidth:248;Layout.fillHeight:true;Layout.margins:9;Layout.rightMargin:0;radius:16','''Layout.preferredWidth:252;Layout.fillHeight:true;Layout.margins:0;radius:0''')
s=s.replace("color:window.nativeGlass ? (Theme.isLight ? '#b8e9e9ed':'#b828282d') : (Theme.isLight ? '#e9e9ed':'#28282d');border.width:1;border.color:Theme.isLight ? '#12000000':'#14ffffff'", """color:window.nativeGlass ? (Theme.isLight ? '#80e9e9ed':'#70202022') : (Theme.isLight ? '#e9e9ed':'#222326')
    Rectangle{anchors{right:parent.right;top:parent.top;bottom:parent.bottom}width:1;color:Theme.isLight ? '#16000000':'#12ffffff'}""")
s=s.replace('anchors.fill:parent;anchors.margins:11;spacing:10','anchors.fill:parent;anchors.margins:12;spacing:13',1)
s=s.replace("TahoeField{id:search;Layout.fillWidth:true;", """TahoeField{id:search;Layout.fillWidth:true;implicitHeight:32;leftPadding:13;rightPadding:10;
      background:Rectangle{radius:16;color:Theme.isLight ? '#18000000':'#15ffffff'}
      """,1)
s=s.replace("height:modelData.id==='account' ? 60:35;radius:7", "height:modelData.id==='account' ? 60:35;radius:8",1)
s=s.replace("color:Theme.isLight ? '#fafafa':'#1c1c1e';radius:18", "color:Theme.isLight ? '#fafafa':'#202124';radius:0",1)
a=s.index('       RowLayout{spacing:2')
b=s.index('       Text{Layout.fillWidth:true;text:window.query',a)
s=s[:a]+"""       Item{
        Layout.preferredWidth:70;Layout.preferredHeight:34
        Rectangle{anchors.fill:parent;radius:17;color:Theme.isLight ? '#0c000000':'#0cffffff';border.width:1;border.color:Theme.isLight ? '#16000000':'#16ffffff'}
        Rectangle{anchors.centerIn:parent;width:1;height:20;color:Theme.isLight ? '#18000000':'#18ffffff'}
        Row{anchors.fill:parent
         TahoeButton{text:I18n.tr('‹');width:35;height:34;background:Item{} enabled:window.canBack;onClicked:window.back()}
         TahoeButton{text:I18n.tr('›');width:35;height:34;background:Item{} enabled:window.canForward;onClicked:window.forward()}
        }
       }
"""+s[b:]
s=s.replace("font.weight:modelData.id==='account' ? Font.DemiBold:Font.Normal", "font.weight:entry.selected || modelData.id==='account' ? Font.DemiBold:Font.Normal")
p.write_text(s)
p=root/'settingsapp/SettingsCard.qml';s=p.read_text().replace('radius:12','radius:14').replace("'#252529'","'#25272a'").replace('border.width:SettingsPreferences.accessibility.increaseContrast ? 2:1','border.width:SettingsPreferences.accessibility.increaseContrast ? 2:0');p.write_text(s)
p=root/'components/ColorSetting.qml';s=p.read_text().replace(" property string label:'Color'"," function open(){chooser.chosen=root.value;chooser.open()}\n property string label:'Color'",1);p.write_text(s)
p=root/'assets/i18n/pt_BR.json';d=json.loads(p.read_text());d.update({'Auto':'Auto','Theme':'Tema','Icon & widget style':'Estilo de ícones e widgets','Custom color':'Cor personalizada','Color':'Cor','Transparent widgets':'Widgets transparentes'});p.write_text(json.dumps(d,ensure_ascii=False,indent=1)+'\n')
