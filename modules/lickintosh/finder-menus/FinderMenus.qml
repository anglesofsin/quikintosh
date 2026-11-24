pragma Singleton
import QtQuick
import QtQuick.Dialogs
import Quickshell
import Quickshell.Hyprland
import qs.services
import qs.ui.topbar.menubar.globalmenu
Singleton {
 id:root
 readonly property bool desktop:GlobalMenuService.desktopMode
 readonly property bool selected:!desktop || DesktopFiles.selection.length>0
 function command(label,args){return {label:I18n.tr(label),command:args}}
 function item(label,mods,key,action,disabled){return {label:I18n.tr(label),mods:mods,key:key,desktopAction:action || '',disabled:!!disabled}}
 function path(label,value){return command(label,['rice-file-manager',value])}
 readonly property var applicationMenu:[
  command('About Quickintosh',['xdg-open','https://github.com/anglesofsin/quikintosh']),
  command('Settings…',['gapplication','action','org.gnome.Nautilus','preferences']),
  {separator:true},{label:I18n.tr('Desktop & Dock Settings…'),finderAction:'settings'}
 ]
 readonly property var menus:[
  {label:I18n.tr('File'),items:[
   command('New Finder Window',['rice-file-manager']),
   item('New Folder','CTRL SHIFT','N','new-folder'),
   item('New Tab','CTRL','T','',desktop),{separator:true},
   item('Open','CTRL','O','open',!selected),
   item('Close Window','CTRL','W','',desktop),{separator:true},
   item('Get Info','ALT','Return','info',!selected),
   item('Rename','','F2','rename',!selected),
   Object.assign(item('Duplicate','CTRL','D','duplicate',!selected),{chord:[{mods:'CTRL',key:'C'},{mods:'CTRL',key:'V'}]}),
   item('Quick Look','','space','quicklook',!selected),{separator:true},
   item('Move to Trash','','Delete','trash',!selected)
  ]},
  {label:I18n.tr('Edit'),items:[
   item('Undo','CTRL','Z','',desktop),item('Redo','CTRL SHIFT','Z','',desktop),{separator:true},
   item('Cut','CTRL','X','cut',!selected),item('Copy','CTRL','C','copy',!selected),
   item('Paste','CTRL','V','paste'),{separator:true},
   item('Select All','CTRL','A','select-all')
  ]},
  {label:I18n.tr('View'),items:[
   item('As Icons','CTRL','1','',desktop),item('As List','CTRL','2','',desktop),{separator:true},
   item('Zoom In','CTRL','plus','zoom-in'),item('Zoom Out','CTRL','minus','zoom-out'),
   item('Actual Size','CTRL','0','zoom-reset'),{separator:true},
   item('Show Hidden Files','CTRL','H','hidden'),item('Reload','','F5','reload'),
   item('Clean Up','','','cleanup',!desktop),
   {label:I18n.tr('Show View Options…'),finderAction:'settings'}
  ]},
  {label:I18n.tr('Go'),items:[
   item('Back','ALT','Left','',desktop),item('Forward','ALT','Right','',desktop),
   item('Enclosing Folder','ALT','Up','',desktop),{separator:true},
   path('Home',Quickshell.env('HOME')),path('Desktop',DesktopFiles.dir),
   path('Documents',Quickshell.env('HOME')+'/Documents'),path('Downloads',Quickshell.env('HOME')+'/Downloads'),
   path('Pictures',Quickshell.env('HOME')+'/Pictures'),path('Music',Quickshell.env('HOME')+'/Music'),
   path('Videos',Quickshell.env('HOME')+'/Videos'),path('Recent Files','recent:///'),
   path('Trash','trash:///'),path('Computer','/'),path('Network','network:///'),{separator:true},
   item('Go to Folder…','CTRL','L','go-folder')
  ]},
  {label:I18n.tr('Window'),items:[
   item('Zoom','','F11','',desktop),
   command('Bring Finder to Front',['rice-file-manager']),
   item('Next Tab','CTRL','Page_Down','',desktop),item('Previous Tab','CTRL','Page_Up','',desktop)
  ]},
  {label:I18n.tr('Help'),items:[
   command('Quickintosh Help',['xdg-open','https://github.com/anglesofsin/quikintosh#readme']),
   command('Files Help',['xdg-open','help:gnome-help/files'])
  ]}
 ]
 FolderDialog{id:goFolder;title:I18n.tr('Go to Folder');currentFolder:'file://'+Quickshell.env('HOME');onAccepted:Quickshell.execDetached(['rice-file-manager',String(selectedFolder)])}
 function execute(action){
  const selection=DesktopFiles.selection.slice(),target={path:selection[0] || '',kind:'file'}
  if(action==='quicklook'){if(selection.length)QuickLookState.show(selection,0,'desktop')}
  else if(action==='select-all'){const files=[];for(let i=0;i<DesktopFiles.model.count;i++)files.push(DesktopFiles.model.get(i,'filePath'));DesktopFiles.selectMany(files)}
  else if(action==='zoom-in')WidgetState.resizeDesktopIcons(WidgetState.iconSize+8)
  else if(action==='zoom-out')WidgetState.resizeDesktopIcons(WidgetState.iconSize-8)
  else if(action==='zoom-reset')WidgetState.resizeDesktopIcons(56)
  else if(action==='paste')QuickLookState.fileAction('paste',[],'',DesktopFiles.dir)
  else if(action==='copy' || action==='cut'){
   const content=action+'\n'+selection.map(p=>'file://'+p.split('/').map(encodeURIComponent).join('/')).join('\n')+'\n'
   Quickshell.execDetached(['sh','-c','printf "%s" "$1" | wl-copy --type x-special/gnome-copied-files','sh',content])
  }
  else if(action==='go-folder')goFolder.open()
  else if(action==='settings')SettingsLauncher.open('DockPage')
  else if(action==='reload')DesktopFiles.scanLaunchers()
  else DesktopFiles.handle(action,target)
 }
}
