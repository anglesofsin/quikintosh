from pathlib import Path
import sys
r=Path(sys.argv[1]);name='ui/dock/Dock.qml';p=r/name;s=p.read_text()
def replace(old,new,count=1):
 global s
 if s.count(old)!=count:raise ValueError('Dock identity anchor '+old[:70]+' '+str(s.count(old)))
 s=s.replace(old,new)
replace('import QtQuick\n','import QtQuick\nimport "../../tahoedock/AppIdentity.js" as AppIdentity\n')
replace('    function resolveAppId(c) {','    function resolveAppId(c) {\n        const process=tahoeSurface.processIdentities[String(c.pid)];if(process)return process.key')
replace('    function resolveIconForClient(c) {','''    function resolveIconForClient(c) {
        const process=tahoeSurface.processIdentities[String(c.pid)]
        if(process?.icon){const resolved=DockIcons.byName(process.icon);if(resolved)return resolved}''')
replace('displayName: appId,','displayName: tahoeSurface.processIdentities[String(c.pid)]?.name || appId,')
replace('            var data   = JSON.parse(json)','            var data   = JSON.parse(json)\n            tahoeSurface.identifyClients(data)')
replace('    property string activeAppId:', '    property int activeClientPid:0\n    property string activeAppId:')
replace('dockRoot.activeAppId=dockRoot.resolveAppId({cls:d.class,initialClass:d.initialClass,title:d.title,initialTitle:d.initialTitle}).toLowerCase()','dockRoot.activeClientPid=Number(d.pid) || 0\n            dockRoot.activeAppId=dockRoot.resolveAppId({pid:d.pid,cls:d.class,initialClass:d.initialClass,title:d.title,initialTitle:d.initialTitle}).toLowerCase()')
replace('    function pinnedKey(entry) {','    function pinnedKey(entry) {\n        const channel=AppIdentity.discordKey(entry.cmd) || AppIdentity.discordKey(entry.name);if(channel)return channel')
replace('(appId.indexOf(cmd) !== -1 || cmd.indexOf(appId) !== -1)','AppIdentity.same(appId,cmd)')
p.chmod(p.stat().st_mode|0o200);p.write_text(s)
