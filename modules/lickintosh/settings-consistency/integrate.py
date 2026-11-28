"""Final Settings consistency pass, after all page contributors are assembled."""
from pathlib import Path
import json
import re
import sys

root = Path(sys.argv[1])


def write(relative, transform):
    p = root / relative
    text = p.read_text()
    updated = transform(text)
    if p.is_symlink():
        p.unlink()
    else:
        p.chmod(0o644)
    p.write_text(updated)


def content(s):
    # An unknown current value is not the first item in a menu.
    s = s.replace('selection:Math.max(0,index)', 'selection:index')
    s = s.replace('selection:modelData.selection || 0', 'selection:modelData.selection===undefined ? -1:modelData.selection')
    s = s.replace("value:String(value),number:Number(value)", "value:value===undefined ? '':String(value),number:Number.isFinite(Number(value)) ? Number(value):0")
    s = s.replace("number:Number(value),checked:!!value", "number:Number.isFinite(Number(value)) ? Number(value):0,checked:!!value")
    s = s.replace("number:source.volume || 0,minimum:0", "number:source.volume || 0,value:Math.round((source.volume || 0)*100)+'%',minimum:0")
    s = s.replace("minimum:2000,maximum:15000,step:1000,", "minimum:2000,maximum:15000,step:1000,value:(SettingsPreferences.notifications.duration/1000)+' s',")
    s = s.replace("minimum:.85,maximum:1.5,step:.05,", "minimum:.85,maximum:1.5,step:.05,value:Math.round(SettingsPreferences.accessibility.textScale*100)+'%',")
    s = s.replace("minimum:60,maximum:3600,step:60,", "minimum:60,maximum:3600,step:60,available:SettingsPreferences.session.autoLock,value:Math.round(SettingsPreferences.session.lockAfter/60)+' min',")
    s = s.replace("row('From','field',{value:p.start,action:'focus-edit',key:'start'})", "row('From','field',{value:p.start,action:'focus-edit',key:'start',available:!!p.schedule})")
    s = s.replace("row('To','field',{value:p.end,action:'focus-edit',key:'end'})", "row('To','field',{value:p.end,action:'focus-edit',key:'end',available:!!p.schedule})")
    s = s.replace("'focus-profile-day',{target:index}", "'focus-profile-day',{target:index,available:!!p.schedule}")
    s = s.replace("SettingsPreferences.focus.endAt>0 ? 1:0,'focus-duration'", "SettingsPreferences.focus.endAt>0 ? 1:0,'focus-duration',{available:ShellConfig.options.session.focus}")
    s = s.replace("if(name==='focus-edit'){FocusState.edit(row.key,value);return}", """if(name==='focus-edit'){
   if(['start','end'].includes(row.key) && !/^([01]\\d|2[0-3]):[0-5]\\d$/.test(value)){SettingsState.error=I18n.tr('Enter a valid time in 24-hour format.');return}
   if(row.key==='name' && !String(value).trim()){SettingsState.error=I18n.tr('Enter a profile name.');return}
   FocusState.edit(row.key,value);return
  }""")
    # Each input page restores only what it owns; accessibility links still lead here.
    s = s.replace("if(name==='input-reset'){SettingsPreferences.inputOverrides=({});return}", """if(name==='input-reset'){
   const next=Object.assign({},SettingsPreferences.inputOverrides)
   for(const key of Object.keys(next)){
    const owner=key.startsWith('input:touchpad:') ? 'trackpad':key.startsWith('input:kb_') || key.startsWith('input:repeat_') ? 'keyboard':(key.startsWith('cursor:') || key.startsWith('qi-cursor:')) || ['input:sensitivity','input:accel_profile','input:natural_scroll','input:scroll_factor'].includes(key) ? 'mouse':''
    if(owner===pageId)delete next[key]
   }
   SettingsPreferences.inputOverrides=next;return
  }""")
    # App rules cannot make a disabled global banner policy appear active.
    s = s.replace("key:'banners',available:!!notificationApp", "key:'banners',available:!!notificationApp && SettingsPreferences.notifications.banners && SettingsPreferences.appRule(notificationApp).allowed!==false")
    s = s.replace("if(name==='permission-app'){selectedPermissionApp=stateData.privacy.flatpaks[value].id;", "if(name==='permission-app'){const app=stateData.privacy?.flatpaks?.[value];if(!app)return;selectedPermissionApp=app.id;")
    s = s.replace("SettingsState.change('audio-default',{id:list[value].id})", "if(list?.[value])SettingsState.change('audio-default',{id:list[value].id})")
    s = s.replace("info('Automatic Time',stateData.datetime?.NTP==='yes' ? 'On':'Off')", "info('Automatic Time',stateData.datetime?.NTP===undefined ? undefined:stateData.datetime.NTP==='yes' ? 'On':'Off')")
    s = s.replace("info('Clock Synchronization',stateData.datetime?.NTPSynchronized==='yes' ? 'Synchronized':'Not synchronized')", "info('Clock Synchronization',stateData.datetime?.NTPSynchronized===undefined ? undefined:stateData.datetime.NTPSynchronized==='yes' ? 'Synchronized':'Not synchronized')")
    s = s.replace("card('App & Website Activity'", "card('App Activity'")
    # Network service listings and VPN controls have separate homes.
    s = s.replace("pageId==='vpn' ? vpn:profiles", "pageId==='vpn' ? vpn:profiles.filter(p=>!['vpn','wireguard'].includes(p.type))")
    s = s.replace("result.push(card('Configuration',[button('Connections'", "if(pageId!=='sharing')result.push(card('Configuration',[button('Connections'")
    # Last calculated disk data is also used by the capacity header.
    s = s.replace("root.stateData.storage?.total", "(root.stateData['storage-details'] || root.stateData.storage)?.total")
    s = s.replace("root.stateData.storage?.free", "(root.stateData['storage-details'] || root.stateData.storage)?.free")
    return s

write('settingsapp/SettingsContent.qml', content)


def rows(s):
    # Values, paths and user names are data, never translation keys.
    s = s.replace('text:I18n.tr(root.value)', 'text:root.value')
    s = s.replace('onEditingFinished:if(text!==root.value)root.edited(text)', 'onEditingFinished:if(acceptableInput && text!==root.value)root.edited(text);Keys.onEscapePressed:{text=root.value;focus=false}')
    s = s.replace("currentIndex:root.selection;", "currentIndex:root.selection;displayText:currentIndex<0 ? I18n.tr('Not selected'):currentText;")
    s = s.replace("Layout.preferredWidth:visible ? Math.max(44,implicitWidth):0", "Layout.preferredWidth:visible ? Math.max(44,Math.min(74,implicitWidth)):0")
    s = s.replace('font.pixelSize:11;horizontalAlignment:Text.AlignRight', "font.family:'SF Pro Text';font.pixelSize:12;horizontalAlignment:Text.AlignRight")
    s = s.replace('Qt.Key_Home,Qt.Key_End]', 'Qt.Key_Home,Qt.Key_End,Qt.Key_Up,Qt.Key_Down,Qt.Key_PageUp,Qt.Key_PageDown]')
    s = s.replace("opacity:available ? 1:0.5", "opacity:available ? 1:0.5\n Accessible.name:root.label\n Accessible.description:root.description\n Accessible.role:root.kind==='navigate' ? Accessible.Link:Accessible.Group\n Accessible.onPressAction:if(root.available && root.kind==='navigate')root.activated()")
    s = s.replace('MouseArea{anchors.fill:parent;enabled:root.available', "Rectangle{anchors.fill:parent;radius:6;color:Theme.fillHover;visible:rowMouse.containsMouse && root.kind==='navigate';z:-1}\n MouseArea{id:rowMouse;anchors.fill:parent;enabled:root.available")
    return s

write('settingsapp/SettingsRow.qml', rows)
# Titles describe actual capabilities rather than Apple-only services.
p = root/'settingsapp/catalog.json'
pages = json.loads(p.read_text())
for page in pages:
    if page['id'] in ['defaults', 'login', 'about', 'games']:
        page['parent'] = 'general'
    if page['id'] == 'login':
        page['title'] = 'Login Items'
    if page['id'] == 'accounts':
        page['title'] = 'File Servers'
    if page['id'] == 'activity':
        page['title'] = 'App Activity'
    if page['id'] == 'weather':
        page['parent'] = 'widgets'
write('settingsapp/catalog.json', lambda _:json.dumps(pages,ensure_ascii=False,indent=1)+'\n')
# General must still expose the routes moved out of the sidebar.
write('settingsapp/SettingsContent.qml', lambda s:s.replace("nav('defaults'),nav('login')", "nav('defaults'),nav('login'),nav('games')"))

# Advanced options must not duplicate dedicated forms above them.
write('ui/settings/pages/RosaPage.qml', lambda s:s.replace('name!=="eatPopups" &&', 'name!=="eatPopups" && !["privacy","voiceDuration","reserveClockSpace","voiceLayout","enabled","idleAutoHide","idleHideSeconds","dashboardEnabled","dashboardCamera","dashboardWeatherLocation"].includes(name) &&'))

# Legacy pages navigate within this window, preserving Back/Forward.
for relative in ['ui/settings/pages/DockPage.qml','ui/settings/pages/RosaPage.qml','ui/settings/pages/WidgetsPage.qml']:
    def local_navigation(s):
        if 'signal navigate(string page)' not in s:
            s=re.sub(r'\bid:\s*root', 'id: root\n    signal navigate(string page)',s,count=1)
        return s.replace("SettingsLauncher.open('widgets')", "root.navigate('widgets')").replace("SettingsLauncher.open('weather')", "root.navigate('weather')").replace("SettingsLauncher.open('appearance')", "root.navigate('appearance')")
    write(relative, local_navigation)

# Search by real control labels, including localized titles and diacritics.
# Only source literals are indexed; private current values never enter this index.
for page in pages:
    if page.get('legacy'):
        p=root/'ui/settings/pages'/(page['legacy']+'.qml')
        if p.exists():
            literals=re.findall(r'(?:text|title|label):\s*(?:I18n.tr\()?([\'"])([^\n]*?)\1',p.read_text())
            labels=[value for _,value in literals if len(value)>2 and not value.startswith(('#','file:','http'))]
            page['terms']=list(dict.fromkeys(labels))
            page['keywords']=' '.join(dict.fromkeys([page.get('keywords','')]+labels))
write('settingsapp/catalog.json',lambda _:json.dumps(pages,ensure_ascii=False,indent=1)+'\n')
write('services/SettingsCatalog.qml',lambda s:re.sub(r' function search\(query\).*', lambda _:r""" function search(query){
  const needle=fold(query).trim(),words=needle.split(/\s+/)
  if(!needle)return []
  return pages.filter(page=>words.every(word=>fold(page.title+' '+I18n.tr(page.title)+' '+page.keywords+' '+(page.terms || []).map(term=>I18n.tr(term)).join(' ')).includes(word)))
   .sort((a,b)=>Number(fold(b.title).startsWith(needle))-Number(fold(a.title).startsWith(needle)))
 }""",s))

# Source data in text fields must never be translated (paths, app names, URLs).
# Use one font scale and accessible names for all common control types.
write('settingsapp/SettingsRow.qml',lambda s:s.replace('text:I18n.tr(root.value)','text:root.value').replace('text:root.buttonText;','text:I18n.tr(root.buttonText);'))

# Preserve every appearance mode, but edit the shared style only in Appearance.
def widgets(s):
    line=next(line for line in s.splitlines() if "label:I18n.tr('Appearance');kind:'choice'" in line)
    return s.replace(line,"  SettingsRow{label:I18n.tr('Appearance');kind:'navigate';value:I18n.tr('Icons & Widgets');onActivated:root.navigate('appearance')}")
write('ui/settings/pages/WidgetsPage.qml',widgets)

# Friendly units for input options; a missing option is never displayed as NaN.
write('settingsapp/SettingsContent.qml',lambda s:s.replace("function input(label,key,kind,extra){", """function inputLabel(key,value){
  if(value===undefined || value===null)return ''
  if(key==='input:repeat_delay')return value+' ms'
  if(key==='input:repeat_rate')return value+' /s'
  if(key==='cursor:inactive_timeout')return Number(value)===0 ? I18n.tr('Never'):value+' s'
  return String(value)
 }
 function focusDurationSelection(){const date=new Date();date.setHours(20,0,0,0);return SettingsPreferences.focus.endAt<=0 ? 0:Math.abs(SettingsPreferences.focus.endAt-date.getTime())<1000 ? 2:1}
 function input(label,key,kind,extra){""").replace("value:value===undefined ? '':String(value),available:value!==undefined", "value:inputLabel(key,value),available:value!==undefined").replace("SettingsPreferences.focus.endAt>0 ? 1:0,'focus-duration'", "focusDurationSelection(),'focus-duration'"))

# Restore controls report their scope instead of implying a system-wide reset.
write('settingsapp/SettingsContent.qml',lambda s:s.replace("button('Restore Input Settings','Restore Original Settings','input-reset')", "button(pageId==='keyboard' ? 'Restore Keyboard Settings':pageId==='trackpad' ? 'Restore Trackpad Settings':'Restore Mouse Settings','Restore Original Settings','input-reset',{available:Object.keys(SettingsPreferences.inputOverrides).some(key=>pageId==='trackpad' ? key.startsWith('input:touchpad:'):pageId==='keyboard' ? key.startsWith('input:kb_') || key.startsWith('input:repeat_'):(key.startsWith('cursor:') || key.startsWith('qi-cursor:')) || ['input:sensitivity','input:accel_profile','input:natural_scroll','input:scroll_factor'].includes(key))})"))

# Do not leave a control indefinitely busy when its worker is unavailable.
write('services/SettingsState.qml',lambda s:s.replace("function change(name,args){error='';changing=true;send('action',name,args)}", "function change(name,args){if(!ready){error=I18n.tr('The settings service is not ready. Try again shortly.');return}error='';changing=true;send('action',name,args)}"))

# Empty search and dismissible query errors use the same typography as the forms.
def window(s):
    s=s.replace('margins:12}text:I18n.tr(SettingsState.error)', 'margins:12;rightMargin:42}text:I18n.tr(SettingsState.error)')
    anchor='text:I18n.tr(SettingsState.error);color:Theme.textPrimary;font.pixelSize:12;wrapMode:Text.WordWrap}'
    s=s.replace(anchor,anchor+"\n      TahoeButton{anchors{right:parent.right;top:parent.top;rightMargin:8;topMargin:6}text:'×';implicitWidth:26;Accessible.name:I18n.tr('Dismiss error');onClicked:SettingsState.error=''}")
    return s
write('settings.qml',window)

translations={'File Servers':'Servidores de arquivos','App Activity':'Atividade de aplicativos','Login Items':'Itens de início','Not selected':'Não selecionado','No settings found':'Nenhum ajuste encontrado','Dismiss error':'Dispensar erro','Restore Keyboard Settings':'Restaurar ajustes do teclado','Restore Mouse Settings':'Restaurar ajustes do mouse','Restore Trackpad Settings':'Restaurar ajustes do trackpad','Enter a profile name.':'Digite um nome para o perfil.','Icons & Widgets':'Ícones e widgets'}
write('assets/i18n/pt_BR.json',lambda s:json.dumps(dict(json.loads(s),**translations),ensure_ascii=False,indent=1)+'\n')
# Same normalization in source assemblies created before the backend update.
write('settingsapp/backend.py',lambda s:s.replace("values[key] = bool(value) if INPUTS[key][0] == 'bool' and value is not None else value", "values[key] = bool(value) if INPUTS[key][0] == 'bool' and value is not None else '' if value == '[[EMPTY]]' else value"))

# Game Mode mutations use the serialized worker and refresh the reported state.
write('settingsapp/SettingsContent.qml',lambda s:s.replace("if(name==='game-mode'){SettingsState.open(['lickintosh','ipc','call','rice','gameMode']);return}","if(name==='game-mode'){SettingsState.change('game-mode',{enabled:!!value});return}").replace("function onCompleted(name,result){", "function onCompleted(name,result){if(name==='game-mode')SettingsState.query('main',true);"))

def game_backend(s):
    if "if name == 'game-mode':" not in s:
        s=s.replace("    if name == 'shortcut-save':","    if name == 'game-mode':\n        enabled = args.get('enabled')\n        if not isinstance(enabled, bool):\n            raise ValueError('Game Mode must be on or off.')\n        cli = os.environ.get('LICKINTOSH_CLI', 'lickintosh')\n        current = json.loads(run([cli, 'ipc', 'call', 'rice', 'state']))\n        if bool(current.get('gameMode')) != enabled:\n            run([cli, 'ipc', 'call', 'rice', 'gameMode'])\n        return json.loads(run([cli, 'ipc', 'call', 'rice', 'state']))\n"+"    if name == 'shortcut-save':")
    return s
write('settingsapp/backend.py',game_backend)

# Changing a reused generic route starts at the top, like native Settings.
write('settingsapp/SettingsContent.qml',lambda s:s.replace("onPageIdChanged:{selectedApp='';selectedPermissionApp='';", "onPageIdChanged:{if(contentItem)contentItem.contentY=0;selectedApp='';selectedPermissionApp='';"))
# The section index also follows disclosures, not only added/removed children.
write('ui/settings/widgets/ContentPage.qml',lambda s:s.replace('    onVisibleChanged:if(visible)sectionRebuild.restart()', '    onVisibleChanged:if(visible)sectionRebuild.restart()\n    onContentHeightChanged:sectionRebuild.restart()'))
# Avoid the second Appearance link after the canonical style control above it.
write('ui/settings/pages/WidgetsPage.qml',lambda s:s.replace("  SettingsRow{label:I18n.tr('Appearance');kind:'navigate';onActivated:root.navigate('appearance');separator:false}\n",'').replace("onActivated:root.navigate('weather')}","onActivated:root.navigate('weather');separator:false}"))

# These labels are emitted by the blur schema rather than literal form rows.
blur_labels={'Taille du flou':'Blur radius','Bruit':'Noise','Contraste':'Contrast','Vibrance des zones sombres':'Dark-area vibrance','Flou xray':'X-ray blur','Optimisations du flou':'Blur optimizations','Flou des menus contextuels':'Context menu blur'}
write('assets/i18n/en.json',lambda s:json.dumps(dict(json.loads(s),**blur_labels),ensure_ascii=False,indent=1)+'\n')
