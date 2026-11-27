# Runs last, against the fully assembled UI.
focus=Path(sys.argv[3])
for name in ['FocusState.qml','FocusPolicy.js']:
 shutil.copyfile(focus/name,root/'services'/name)
p=root/'services/qmldir';p.write_text(p.read_text()+'\nsingleton FocusState FocusState.qml\n')
p=root/'settingsapp/SettingsRuntime.qml';s=p.read_text().replace(' property bool workerReady:false',' readonly property var focusController:FocusState\n property bool workerReady:false')
a=s.index('  const start=minutes(focus.start)');b=s.index('  if(SettingsPreferences.profile.autoAppearance)',a)
s=s[:a]+s[b:];p.write_text(s)
p=root/'ui/topbar/statusarea/notifcenter/NotifService.qml';s=p.read_text().replace('(!root.dndEnabled || critical)','(!root.dndEnabled || FocusState.permits(notification))');p.write_text(s)
p=root/'rosa/services/IslandConfig.qml';s=p.read_text().replace('        enabled:     {', '''        mediaGradient:{type:"bool",def:true},
        mediaGradientCustom:{type:"bool",def:false},
        mediaGradientEnd:{type:"text",def:"#bf5af2"},
        mediaColorMode:{type:"pick",def:"album",values:["album","system","custom"]},
        mediaCustomColor:{type:"text",def:"#64d2ff"},
        enabled:     {''',1);p.write_text(s)
p=root/'rosa/overlays/IslandWindow.qml';s=p.read_text().replace('IslandConfig.s("artTint") && artTint.found ? artTint.color : Colors.accent', '''IslandConfig.s("mediaColorMode")==="custom" ? IslandConfig.s("mediaCustomColor"):
        IslandConfig.s("mediaColorMode")==="system" ? NativeSettings.Theme.accent:
        IslandConfig.s("artTint") && artTint.found ? artTint.color : Colors.accent''');p.write_text(s)
p=root/'ui/settings/pages/RosaPage.qml';s=p.read_text().replace('    ContentSection {','''    ContentSection {
        title:I18n.tr("Media color")
        RowLayout {
            Layout.fillWidth:true
            Text{Layout.fillWidth:true;text:I18n.tr("Color source");color:Theme.textPrimary;font.pixelSize:13}
            TahoeCombo{model:["Album artwork","System accent","Custom"];currentIndex:["album","system","custom"].indexOf(Rosa.IslandConfig.s("mediaColorMode"));onActivated:index=>Rosa.IslandConfig.setStyle("mediaColorMode",["album","system","custom"][index])}
        }
        ColorSetting{visible:Rosa.IslandConfig.s("mediaColorMode")==="custom";label:I18n.tr("Media color");value:Rosa.IslandConfig.s("mediaCustomColor");onPicked:value=>Rosa.IslandConfig.setStyle("mediaCustomColor",String(value))}
        ConfigSwitch{text:I18n.tr("Audio indicator gradient");checked:Rosa.IslandConfig.s("mediaGradient");onToggled:value=>Rosa.IslandConfig.setStyle("mediaGradient",value)}
        ConfigSwitch{visible:Rosa.IslandConfig.s("mediaGradient");text:I18n.tr("Custom gradient color");checked:Rosa.IslandConfig.s("mediaGradientCustom");onToggled:value=>Rosa.IslandConfig.setStyle("mediaGradientCustom",value)}
        ColorSetting{visible:Rosa.IslandConfig.s("mediaGradient") && Rosa.IslandConfig.s("mediaGradientCustom");label:I18n.tr("Gradient end color");value:Rosa.IslandConfig.s("mediaGradientEnd");onPicked:value=>Rosa.IslandConfig.setStyle("mediaGradientEnd",String(value))}
        ConfigSwitch{text:I18n.tr("Do Not Disturb while screen sharing");checked:SettingsPreferences.focus.autoDndSharing;onToggled:value=>SettingsPreferences.focus.autoDndSharing=value}
    }
    ContentSection {''',1);p.write_text(s)
p=root/'assets/i18n/pt_BR.json'
catalog=json.loads(p.read_text())
catalog.update({
 'Audio indicator gradient':'Gradiente do indicador de áudio','Custom gradient color':'Cor personalizada do gradiente','Gradient end color':'Cor final do gradiente',
 'Media color':'Cor da mídia','Color source':'Origem da cor','Album artwork':'Capa do álbum','System accent':'Cor de destaque do sistema','Custom':'Personalizada',
 'Do Not Disturb while screen sharing':'Não Perturbe durante compartilhamento de tela',
 'Do Not Disturb While Screen Sharing':'Não Perturbe durante compartilhamento de tela',
 'Focus':'Foco','Profile':'Perfil','Enable Focus':'Ativar Foco','New Profile':'Novo perfil','Delete Profile':'Apagar perfil',
 'Custom Focus':'Foco personalizado','Work':'Trabalho','Personal':'Pessoal','Sleep':'Sono','Allow Selected':'Permitir selecionados','Silence Selected':'Silenciar selecionados',
 'People':'Pessoas','Critical Alerts':'Alertas críticos','Time-Sensitive Notifications':'Notificações urgentes',
 'For apps that provide sender information.':'Para aplicativos que informam o remetente.',
 'Schedule & Automation':'Horário e automação','When Using Apps':'Ao usar aplicativos','Selected':'Selecionado'
})
p.write_text(json.dumps(catalog,ensure_ascii=False,indent=1)+'\n')
