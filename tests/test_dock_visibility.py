"""Headless checks of real Dock occlusion bindings and compositor coordinates."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import test_qml_interface as qml

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(qml.QS,'Quickshell is required for the offscreen Dock checks')
class DockVisibility(unittest.TestCase):
    def test_visible_workspaces_geometry_scaling_and_live_changes(self):
        monitor={'id':0,'name':'test','x':100,'y':50,'activeWorkspace':{'id':1},'specialWorkspace':{'id':0}}
        client={'monitor':0,'workspace':{'id':1},'at':[650,990],'size':[400,200],'mapped':True}
        def window(**changes):return dict(client,**changes)
        cases=[
            ('empty desktop',[],False),
            ('floating away from dock',[window(at=[650,200])],False),
            ('floating over dock',[client],True),
            ('touching the edge',[window(at=[650,800],size=[400,200])],False),
            ('unmapped',[window(mapped=False)],False),
            ('hidden',[window(hidden=True)],False),
            ('other workspace',[window(workspace={'id':2})],False),
            ('pinned on another regular workspace',[window(pinned=True,workspace={'id':2})],True),
            ('hidden special workspace',[window(workspace={'id':-99})],False),
            ('hidden pinned special workspace',[window(pinned=True,workspace={'id':-99})],False),
            ('fullscreen stale geometry',[window(fullscreen=2,at=[650,200])],True),
            ('fullscreen elsewhere',[window(fullscreen=2,workspace={'id':2})],False),
            ('invalid size',[window(size=[0,200])],False),
            ('missing geometry',[{'monitor':0,'workspace':{'id':1}}],False),
        ]
        values=[{'name':name,'clients':clients,'blocked':blocked,'monitors':[monitor],'rect':[500,950,600,90],'scale':1} for name,clients,blocked in cases]
        special=dict(monitor,specialWorkspace={'id':-99})
        values.append(dict(values[0],name='visible special workspace',clients=[window(workspace={'id':-99})],monitors=[special],blocked=True))
        modern=dict(monitor,activeWorkspace={'address':'1','type':'normal','name':'1'},specialWorkspace={'address':'special:public','type':'special','name':'special:public'})
        values.append(dict(values[0],name='modern visible special',monitors=[modern],clients=[window(workspace={'address':'special:public','type':'special','name':'special:public'})],blocked=True))
        values.append(dict(values[0],name='modern hidden special',monitors=[modern],clients=[window(workspace={'address':'special:hidden','type':'special','name':'special:hidden'})],blocked=False))
        values.append(dict(values[0],name='modern regular workspace',monitors=[modern],clients=[window(workspace={'address':'1','type':'normal','name':'1'})],blocked=True))
        values.append(dict(values[0],name='modern empty special',monitors=[dict(modern,specialWorkspace={'address':'','type':'','name':''})],clients=[window(workspace={'address':'special:public','type':'special','name':'special:public'})],blocked=False))
        other={'id':1,'name':'other','x':2020,'y':50,'activeWorkspace':{'id':2},'specialWorkspace':{'id':0}}
        values.append(dict(values[0],name='other monitor',clients=[window(monitor=1,workspace={'id':2},at=[2200,990])],monitors=[monitor,other]))
        values.append(dict(values[0],name='window crossing monitor edge',clients=[window(monitor=1,workspace={'id':2},at=[1000,990],size=[1300,200])],monitors=[monitor,other],blocked=True))
        values.append(dict(values[0],name='shell scaling',clients=[client],rect=[200,600,400,60],scale=1.5,blocked=True))
        negative=dict(monitor,x=-1920,y=-1000)
        values.append(dict(values[0],name='negative monitor origin',clients=[window(at=[-1400,0],size=[100,100])],monitors=[negative],blocked=True))
        values.append(dict(values[0],name='left dock',clients=[window(at=[110,400])],rect=[8,200,80,500],blocked=True))
        values.append(dict(values[0],name='right dock',clients=[window(at=[1930,400])],rect=[1832,200,80,500],blocked=True))
        with tempfile.TemporaryDirectory() as directory:
            for name in ['DockOcclusion.qml','DockOcclusion.js']:
                shutil.copyfile(ROOT/'modules/lickintosh/dock'/name,Path(directory)/name)
            output=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
Scope {
 Loader{id:watcher;sourceComponent:DockOcclusion{monitorName:'test'}}
 readonly property var probe:watcher.item
 property var cases:'''+json.dumps(values)+'''
 Timer{interval:1;running:true;onTriggered:{
  for(const value of cases){
   probe.monitors=value.monitors;probe.clients=value.clients;probe.shellScale=value.scale
   probe.dockRect=Qt.rect(...value.rect)
   if(probe.blocked!==value.blocked){console.error('Dock collision:',value.name,probe.blocked);Qt.exit(41);return}
  }
  probe.monitors=cases[0].monitors;probe.shellScale=1;probe.dockRect=Qt.rect(500,950,600,90)
  probe.clients=cases[2].clients;if(!probe.blocked){Qt.exit(42);return}
  probe.monitors=[Object.assign({},cases[0].monitors[0],{activeWorkspace:{id:2}})]
  if(probe.blocked){Qt.exit(43);return}
  console.log('DOCK_OCCLUSION_GEOMETRY_WORKSPACE_SCALE_OK',cases.length);Qt.quit()
 }}
}''')
            self.assertIn('DOCK_OCCLUSION_GEOMETRY_WORKSPACE_SCALE_OK',output)

if __name__=='__main__':unittest.main()
