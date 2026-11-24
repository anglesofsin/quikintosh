from pathlib import Path
import sys,json
root=Path(sys.argv[1]);here=Path(__file__).parent
for p in root.rglob('*'):
 if not p.is_symlink():p.chmod(p.stat().st_mode|0o200)
(root/'services/ExtraControls.qml').write_text((here/'ExtraControls.qml').read_text());p=root/'services/qmldir';p.write_text(p.read_text()+'\nsingleton ExtraControls ExtraControls.qml\n')
(root/'ui/widgets/types/UtilityWidget.qml').write_text((here/'UtilityWidget.qml').read_text());p=root/'ui/widgets/types/qmldir';p.write_text(p.read_text()+'\nUtilityWidget UtilityWidget.qml\n')
widgets=[('display','Display','sun-small.svg'),('storageinfo','Storage','notch/database.svg'),('systeminfo','Activity','notch/zap.svg'),('microphone','Microphone','notch/mic.svg'),('shortcuts','Shortcuts','notch/zap.svg')]
for kind,title,icon in widgets:
 mode={'storageinfo':'storage','systeminfo':'system'}.get(kind,kind);name=kind.title()+'Utility'
 (root/'ui/widgets/types'/f'{name}.qml').write_text('import QtQuick\nimport qs.ui.widgets.types\nUtilityWidget{mode:'+json.dumps(mode)+'}\n')
 p=root/'ui/widgets/types/qmldir';p.write_text(p.read_text()+f'\n{name} {name}.qml\n')
p=root/'services/WidgetRegistry.qml';s=p.read_text();anchor='    readonly property var types: [';assert anchor in s
entries=[dict(type=kind,title=title,file=kind.title()+'Utility',sizes=['s','m'],icon=icon,tint='#0a84ff') for kind,title,icon in widgets]
s=s.replace(anchor,anchor+'\n'+',\n'.join(json.dumps(e) for e in entries)+',',1);p.write_text(s)
p=root/'services/ControlCatalog.qml';s=p.read_text();anchor='    readonly property var controls: [';assert anchor in s;s=s.replace(anchor,'    readonly property var controls: ExtraControls.entries.concat([',1);end=s.index('\n    ]',s.index('    readonly property var controls:'));s=s[:end]+s[end:].replace('\n    ]','\n    ])',1);p.write_text(s)
p=root/'shell.qml';s=p.read_text().replace('        function settings(): void {','        function quickNote(): void { quickNote.open() }\n        function settings(): void {',1);p.write_text(s)
p=root/'ui/topbar/statusarea/controlcenter/ControlCenter.qml';s=p.read_text();i=s.index('values: ControlCatalog.instancesOfType("wifiWidget")');i=s.rfind('                    Repeater {',0,i)
s=s[:i]+'''                    Repeater{
                        model:ScriptModel{values:ControlCatalog.items.filter(item=>String(item.type || item.id || '').startsWith('extra_'));objectProp:'uid'}
                        delegate:BoxButton{
                            id:extra;required property var modelData
                            widgetId:modelData.uid
                            readonly property string kind:ControlCatalog.typeOfUid(widgetId)
                            xPos:root.packedX(widgetId);yPos:root.packedY(widgetId)
                            width:root.box;height:root.box;radius:32
                            enabled:ExtraControls.active(kind)
                            hideCause:root.subOpened
                            CFVI{anchors.centerIn:parent;size:25;icon:ControlCatalog.infoOf(extra.kind)?.icon || '';color:ExtraControls.active(extra.kind) ? Theme.accent:'#ffffff'}
                            MouseArea{anchors.fill:parent;enabled:ExtraControls.available(extra.kind);onClicked:ExtraControls.run(extra.kind);onPressed:extra.isPressed=true;onReleased:extra.isPressed=false;onCanceled:extra.isPressed=false}
                        }
                    }
'''+s[i:];p.write_text(s)
