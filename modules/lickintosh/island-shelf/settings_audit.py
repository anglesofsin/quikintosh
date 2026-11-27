"""Tahoe settings consistency and bounded island handoff, preserving all actions."""
from pathlib import Path

def local(root,relative):
 p=root/relative
 if p.is_symlink():
  target=p.resolve();p.unlink();p.mkdir()
  for entry in target.iterdir():(p/entry.name).symlink_to(entry,target_is_directory=entry.is_dir())
 return p

def edit(root,relative,transform):
 p=root/relative;s=p.read_text()
 if p.is_symlink():p.unlink()
 else:p.chmod(0o644)
 p.write_text(transform(s))

def integrate(root):
 root=Path(root)
 edit(root,'rosa/overlays/IslandWindow.qml',lambda s:s.replace('(win.dashboardCover ? 0 : 1)','1'))
 edit(root,'rosa/overlays/IslandDashboard.qml',lambda s:s.replace('    onCollapsedChanged:if(collapsed)collapseFinished()','    onCollapsedChanged:if(collapsed)collapseFinished()\n    Connections{target:body;function onWidthChanged(){panel.queueCollapseHandoff()}function onHeightChanged(){panel.queueCollapseHandoff()}}\n    function queueCollapseHandoff(){if(!expanded && collapsed)Qt.callLater(function(){if(panel.collapsed)panel.collapseFinished()})}'))
 for relative in ['ui','ui/settings','ui/settings/pages','ui/settings/widgets','settingsapp']:
  local(root,relative)
 edit(root,'settingsapp/SettingsCard.qml',lambda s:s.replace('spacing:7','spacing:8').replace('implicitHeight:column.implicitHeight+4;radius:10','implicitHeight:column.implicitHeight+16;radius:12').replace("'#2b2b2d'","'#252527'").replace('topMargin:2;leftMargin:14;rightMargin:14','topMargin:8;leftMargin:16;rightMargin:16'))
 edit(root,'settingsapp/SettingsContent.qml',lambda s:s.replace('id:column;width:root.availableWidth-48;x:24;y:16;spacing:18','id:column;width:Math.min(760,root.availableWidth-48);x:(root.availableWidth-width)/2;y:16;spacing:20'))
 edit(root,'settingsapp/SettingsRow.qml',lambda s:s.replace('import QtQuick.Controls\n','import QtQuick.Controls.Basic\n').replace('Math.max(description ? 60:44,labels.implicitHeight+20)','Math.max(description ? 64:44,labels.implicitHeight+20)').replace('Text{Layout.maximumWidth:260;', 'Text{id:detailValue;Layout.preferredWidth:Math.max(80,Math.min(260,root.width*.42));wrapMode:Text.Wrap;maximumLineCount:3;').replace('elide:Text.ElideMiddle','elide:Text.ElideRight').replace('implicitHeight:30\n  Text{id:detailValue','implicitHeight:Math.max(30,detailValue.implicitHeight)\n  Text{id:detailValue').replace('Math.max(description ? 64:44,labels.implicitHeight+20)','Math.max(description ? 64:44,labels.implicitHeight+20,controlLoader.item ? controlLoader.item.implicitHeight+16:0)').replace('  Loader{\n   Layout.maximumWidth:', '  Loader{\n   id:controlLoader\n   Layout.maximumWidth:').replace('Layout.preferredWidth:visible ? 34:0','Layout.preferredWidth:visible ? Math.max(44,implicitWidth):0'))
 edit(root,'ui/settings/widgets/ContentPage.qml',lambda s:s.replace('width: root.width - 48','width: Math.min(760,root.width - 48)').replace('x: 24','x: (root.width-width)/2').replace('spacing: 18','spacing: 20').replace('contentHeight: _col.implicitHeight + 56','contentHeight: _col.implicitHeight + 48'))
 edit(root,'ui/settings/pages/RosaPage.qml',island_page)
 edit(root,'ui/settings/pages/BatteryPage.qml',lambda _:Path(__file__).with_name('BatterySettingsPage.qml').read_text())
 edit(root,'settingsapp/SettingsPathRow.qml',path_row)
 edit(root,'settingsapp/SettingsContent.qml',scroll_style)
 edit(root,'ui/settings/pages/WifiPage.qml',wifi_layout)
 edit(root,'services/SettingsState.qml',error_scope)
 # Basic style makes customized controls reliable regardless of runtime style.
 edit(root,'ui/settings/pages/AppearanceControls.qml',lambda s:s.replace('source:QuickLookState.urlFor(ShellConfig.options.wallpaper.path);','source:ShellConfig.options.wallpaper.path ? QuickLookState.urlFor(ShellConfig.options.wallpaper.path):\"\";'))
 edit(root,'ui/settings/pages/ConfigSwitch.qml',lambda s:s.replace('import QtQuick.Controls\n','import QtQuick.Controls.Basic\n'))
 # The common error state must offer a working retry, rather than a dead-end footer.
 edit(root,'settings.qml',settings_window)

def island_page(s):
 old='    ContentSection{ShelfAppearance{Layout.fillWidth:true;settingsPage:true}}'
 replacement='''    ContentSection{title:I18n.tr("Shape & Material");ShelfAppearance{Layout.fillWidth:true;settingsPage:true;showAdvancedSections:false}}
    ContentSection{title:I18n.tr("Navigation & Favorites");NavigationSettings{Layout.fillWidth:true;settingsPage:true}}
    ContentSection{title:I18n.tr("Contextual Icons");IconSettings{Layout.fillWidth:true;settingsPage:true}}
'''
 s=s.replace(old,replacement)
 # Existing switches remain available, but internal/tuning controls are disclosed
 # only when requested, rather than filling the first screen with a raw schema.
 s=s.replace('    Repeater {\n        model: Rosa.IslandConfig.groups','''    property bool advancedOptions:false
    ContentSection{title:I18n.tr("Advanced")
        ConfigSwitch{text:I18n.tr("Show advanced activity and animation controls");checked:root.advancedOptions;onToggled:value=>root.advancedOptions=value}
    }
    Repeater {
        model: root.advancedOptions ? Rosa.IslandConfig.groups:[]''',1)
 # Frequently used and safety controls keep their own sections above Advanced.
 insertion='''    ContentSection{title:I18n.tr("Calls & Privacy")
        ConfigSwitch{text:I18n.tr("Show privacy indicator");checked:Rosa.IslandConfig.s("privacy");onToggled:value=>Rosa.IslandConfig.setStyle("privacy",value)}
        ConfigSwitch{text:I18n.tr("Show call duration");checked:Rosa.IslandConfig.s("voiceDuration");onToggled:value=>Rosa.IslandConfig.setStyle("voiceDuration",value)}
        ConfigSwitch{text:I18n.tr("Reserve the clock space");checked:Rosa.IslandConfig.s("reserveClockSpace");onToggled:value=>Rosa.IslandConfig.setStyle("reserveClockSpace",value)}
        SettingsFormRow{Layout.fillWidth:true
            Text{Layout.fillWidth:true;text:I18n.tr("Call presentation");color:Theme.textPrimary;font.family:'SF Pro Text';font.pixelSize:13}
            TahoeCombo{model:[I18n.tr("Automatic"),I18n.tr("Expanded"),I18n.tr("Side indicator")];currentIndex:["auto","focus","minimized"].indexOf(Rosa.IslandConfig.s("voiceLayout"));onActivated:index=>Rosa.IslandConfig.setStyle("voiceLayout",["auto","focus","minimized"][index])}
        }
    }
'''
 s=s.replace('    property bool advancedOptions:false',insertion+'    property bool advancedOptions:false')
 return s

def settings_window(s):
 s=s.replace("  route=next;query='';","  SettingsState.beginPage();route=next;query='';",1)
 s=s.replace("Rectangle{Layout.fillWidth:true;visible:!!SettingsState.error;implicitHeight:errorLabel.implicitHeight+24;","Rectangle{Layout.fillWidth:true;Layout.leftMargin:24;Layout.rightMargin:24;radius:10;visible:!!SettingsState.error;implicitHeight:errorLabel.implicitHeight+24;",1)
 # Keep compatibility with sources with a slightly different message formatting.
 a=s.find('     Text{\n      Layout.fillWidth:true;Layout.leftMargin:24;Layout.rightMargin:24\n      visible:loader.status===Loader.Error')
 if a>=0:
  b=s.index('\n     }',a)+len('\n     }')
  s=s[:a]+'''     ColumnLayout{
      visible:loader.status===Loader.Error && !window.query;Layout.fillWidth:true;Layout.fillHeight:true;spacing:12
      Item{Layout.fillHeight:true}
      Text{Layout.alignment:Qt.AlignHCenter;text:I18n.tr('Unable to open this page');color:Theme.textPrimary;font.family:'SF Pro Text';font.pixelSize:16;font.weight:Font.DemiBold}
      TahoeButton{Layout.alignment:Qt.AlignHCenter;text:I18n.tr('Try Again');onClicked:{loader.active=false;Qt.callLater(()=>loader.active=!window.query)}}
      Item{Layout.fillHeight:true}
     }'''+s[b:]
 return s

def path_row(s):
 s=s.replace('RowLayout {','Item {',1).replace('Layout.fillWidth:true;Layout.minimumHeight:48;spacing:14','Layout.fillWidth:true;implicitHeight:48\n RowLayout{anchors.fill:parent;spacing:14',1)
 s=s.replace('Layout.preferredWidth:190;Layout.maximumWidth:root.width*.47','Layout.preferredWidth:Math.min(190,root.width*.32)')
 s=s.replace(' FolderDialog{id:folder;', ' }\n FolderDialog{id:folder;',1)
 return s


def scroll_style(s):
 return s.replace(' ScrollBar.horizontal.policy:ScrollBar.AlwaysOff', """ ScrollBar.horizontal.policy:ScrollBar.AlwaysOff
 ScrollBar.vertical:ScrollBar{width:5;policy:ShellConfig.options.appearance.scrollbarVisibility==='always' ? ScrollBar.AlwaysOn:ScrollBar.AsNeeded;contentItem:Rectangle{implicitWidth:5;radius:2.5;color:Theme.isLight ? '#66000000':'#66ffffff';opacity:parent.active || parent.hovered ? 1:.45}background:Item{}}
""",1)


def wifi_layout(s):
 start=s.index('            MouseArea {',s.index('id: _activeRow'))
 end=s.index('                z: 10',start)
 s=s[:start]+"""            MouseArea {
                parent:activeNetworkIcon
                x:-parent.x;y:-parent.y
                width:Math.max(0,_activeRow.width-(_detailsBtn.visible ? _detailsBtn.width+10:0))
                height:_activeRow.height
"""+s[end:]
 start=s.index('            Rectangle {',start)
 s=s[:start]+s[start:].replace('            Rectangle {','            Rectangle {\n                id:activeNetworkIcon',1)
 return s


def error_scope(s):
 s=s.replace(" property string error:''", " property int pageEpoch:0\n function beginPage(){pageEpoch++;error=''}\n property string error:''",1)
 s=s.replace('requests[token]={kind:kind,name:name}', 'requests[token]={kind:kind,name:name,epoch:pageEpoch}',1)
 s=s.replace("if(event.type==='error'){root.error=event.message;return}","if(event.type==='error'){if(!request || request.kind==='action' || request.epoch===root.pageEpoch)root.error=event.message;return}",1)
 return s
