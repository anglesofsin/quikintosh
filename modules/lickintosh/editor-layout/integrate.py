"""Keep widget controls intact, but separate appearance, typography and content."""
from pathlib import Path
import sys,re
r=Path(sys.argv[1]);here=Path(__file__).parent
def untranslated(s):return re.sub(r"I18n\.tr\((('[^']*'|\"[^\"]*\"))\)",lambda m:m[1],s)

def write(name,s):
 p=r/name;p.chmod(p.stat().st_mode|0o200) if p.exists() else None;p.write_text(s)
def block(s,start):
 a=s.index('{',start);depth=0;quote=None;escape=False
 for i in range(a,len(s)):
  c=s[i]
  if quote:
   if escape:escape=False
   elif c=='\\':escape=True
   elif c==quote:quote=None
  elif c in ('"',"'"):quote=c
  elif c=='{':depth+=1
  elif c=='}':
   depth-=1
   if depth==0:return s[start:i+1],i+1
 raise ValueError('Unclosed editor object')
def group(title,content,visible='true'):
 return "EditorGroup{title:'"+title+"';visible:"+visible+'\n'+content+'\n}\n'
write('ui/widgets/EditorGroup.qml',(here/'EditorGroup.qml').read_text())
write('ui/widgets/qmldir',(r/'ui/widgets/qmldir').read_text()+'\nEditorGroup EditorGroup.qml\n')
p='ui/widgets/WidgetSettings.qml';s=untranslated((r/p).read_text())
s=s.replace("property bool closing:false","property string editorPage:'appearance'\n   readonly property var editorTabs:{const tabs=[{key:'appearance',label:'Appearance'}];if(['image','musicsticker','textsticker','lyricssticker','clock'].includes(root.entry.type))tabs.push({key:'content',label:'Content'});if(['personalclock','textsticker','lyricssticker'].includes(root.entry.type))tabs.push({key:'typography',label:'Typography'});if(root.entry.type==='personalclock')tabs.push({key:'date',label:'Time & Date'});return tabs}\n   property bool closing:false")
s=s.replace('width:Math.min(580,win.width-40)','width:Math.min(720,win.width-48)').replace('height:Math.min(win.height-80,column.implicitHeight+96)','height:Math.min(780,win.height-64)').replace("radius:22;color:Theme.isLight ? '#b8f3f3f6':'#b8252529'","radius:24;color:Theme.isLight ? '#edeeeeF2':'#ed202024'")
a=s.index('    ScrollView{');b=s.index('     RowLayout{anchors{left:parent.left;',a)
old=s[a:b]
objects={}
for name,anchor in [('size',"     RowLayout{Layout.fillWidth:true\n      Text{text:'Size'"),('appearance',"     RowLayout{Layout.fillWidth:true\n      Text{text:'Appearance'"),('surface',"     RowLayout{Layout.fillWidth:true\n      Text{text:'Surface'"),('creative','     CreativeWidgetEditor{'),('clock',"     RowLayout{visible:root.entry.type==='clock'"),('personal',"     ColumnLayout{visible:root.entry.type==='personalclock'")]:
 assert old.count(anchor)==1,(name,old.count(anchor));objects[name]=block(old,old.index(anchor))[0].strip()
personal=objects['personal'];a=personal.index("      RowLayout{");parts=[]
while a<len(personal):
 match=re.search(r'(?m)^      (?:RowLayout|Text|TahoeCombo|TahoeField|ConfigSwitch|ConfigSlider|ColorSetting)\{',personal[a:])
 if not match:break
 start=a+match.start();part,end=block(personal,start);parts.append(part.strip());a=end
assert len(parts)>20,len(parts)
i=next(i for i,p in enumerate(parts) if "text:'Text effect'" in p)
j=next(i for i,p in enumerate(parts) if "text:'Time & Date'" in p)
assert "text:'Clock Typography'" in parts[1]
body=group('Widget appearance','\n'.join(objects[k] for k in ['size','appearance','surface']),"win.editorPage==='appearance'")
body+=group('Clock layout',parts[0],"root.entry.type==='personalclock' && win.editorPage==='appearance'")
body+=group('Colors & effects','\n'.join(parts[i:j]),"root.entry.type==='personalclock' && win.editorPage==='appearance'")
typography='\n'.join(parts[2:i]).replace("text:'Weight';from:0;to:1;decimals:2;value:","text:'Weight';from:0;to:100;decimals:0;valueSuffix:'%';value:100*(")
# Keep the stored normalized weight unchanged while presenting a percentage.
if 'value:100*(' in typography:
 typography=typography.replace(".4:.6);onMoved:value=>",".4:.6));onMoved:value=>").replace("{clockWeight:value}","{clockWeight:value/100}")
body+=group('Clock typography',typography,"root.entry.type==='personalclock' && win.editorPage==='typography'")
body+=group('Time & date','\n'.join(parts[j+1:]),"root.entry.type==='personalclock' && win.editorPage==='date'")
body+=group('Clock',objects['clock'],"root.entry.type==='clock' && win.editorPage==='content'")
body+=objects['creative'].replace('Layout.fillWidth:true;entry:root.entry','Layout.fillWidth:true;entry:root.entry;editorPage:win.editorPage')
header='''    ColumnLayout{
     id:editorHeader;anchors{left:parent.left;right:parent.right;top:parent.top;margins:24};spacing:18
     Item{Layout.fillWidth:true;implicitHeight:52
      Text{anchors{left:parent.left;top:parent.top};text:WidgetRegistry.info(root.entry.type)?.title || 'Widget';font.family:'SF Pro Display';font.pixelSize:24;color:Theme.textPrimary;font.weight:Font.Bold}
      Text{anchors{left:parent.left;bottom:parent.bottom};text:'Customize Widget';font.pixelSize:12;color:Theme.textSecondary}
      TahoeButton{anchors{right:parent.right;top:parent.top};implicitWidth:30;text:'×';Accessible.name:'Close';onClicked:win.finish(false)}
     }
     Rectangle{Layout.fillWidth:true;height:38;radius:11;color:Theme.isLight ? '#10000000':'#24000000'
      RowLayout{anchors.fill:parent;anchors.margins:3;spacing:3
       Repeater{model:win.editorTabs
        delegate:Rectangle{required property var modelData;Layout.fillWidth:true;Layout.fillHeight:true;radius:8;color:win.editorPage===modelData.key ? (Theme.isLight ? '#ffffff':'#55555c'):'transparent'
         Text{anchors.centerIn:parent;text:I18n.tr(parent.modelData.label);color:Theme.textPrimary;font.pixelSize:12;font.weight:win.editorPage===parent.modelData.key ? Font.DemiBold:Font.Normal}
         MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:{win.editorPage=parent.modelData.key;editorScroll.contentItem.contentY=0}}
        }
       }
      }
     }
    }
    ScrollView{
     id:editorScroll;anchors{left:parent.left;right:parent.right;top:editorHeader.bottom;bottom:parent.bottom;leftMargin:24;rightMargin:24;topMargin:22;bottomMargin:88};clip:true
     contentWidth:availableWidth;ScrollBar.horizontal.policy:ScrollBar.AlwaysOff
     ColumnLayout{id:column;width:editorScroll.availableWidth;spacing:18
'''
# a/b still refer to old body positions? Recompute after parsing personal.
a=s.index('    ScrollView{');b=s.index('     RowLayout{anchors{left:parent.left;',a)
s=s[:a]+header+body+'\n     }\n    }\n'+s[b:]
s=s.replace('      Item{Layout.fillWidth:true}\n      TahoeButton{text:\'Remove Widget\';onClicked:win.finish(true)}',"      TahoeButton{text:'Remove Widget';onClicked:win.finish(true)}\n      Item{Layout.fillWidth:true}")
s=s.replace('     RowLayout{anchors{left:parent.left;',"     Rectangle{anchors{left:parent.left;right:parent.right;bottom:parent.bottom;bottomMargin:70;leftMargin:24;rightMargin:24};height:1;color:Theme.isLight ? '#14000000':'#16ffffff'}\n     RowLayout{anchors{left:parent.left;")
# Give standard option rows a consistent minimum hit target inside this editor.
s=s.replace('    MouseArea{anchors.fill:parent}',"    Rectangle{anchors.fill:parent;radius:24;color:Theme.isLight ? '#d9f4f4f7':'#d9202024';border.width:1;border.color:Theme.isLight ? '#30000000':'#30ffffff'}\n    MouseArea{anchors.fill:parent}")
s=s.replace('RowLayout{Layout.fillWidth:true','RowLayout{Layout.fillWidth:true;Layout.minimumHeight:40')
write(p,s.replace('};','}\n'))
# Creative content gets its own page; typography is no longer buried below it.
p='ui/widgets/CreativeWidgetEditor.qml';s=untranslated((r/p).read_text()).replace(' property var entry:({})'," property var entry:({})\n property string editorPage:'content'")
s=s.replace("visible:root.entry.type===", "visible:root.editorPage==='content' && root.entry.type===")
s=s.replace("TypographyEditor{visible:","TypographyEditor{visible:root.editorPage==='typography' && ")
s=s.replace("import qs.components\n","import qs.components\nimport qs.ui.widgets\n")
# Split the long media/music forms into digestible groups without changing handlers.
for first,markers in [
 ("  Text{text:'Media library'",[("  Text{text:'Media library'",'Library'),("  ConfigSwitch{text:'Shuffle'",'Slideshow'),("  ConfigSwitch{text:'Finish video",'Video playback'),("  RowLayout{Layout.fillWidth:true\n   Text{text:'Media fit'",'Framing')]),
 ("  Text{text:'Your soundtrack'",[("  Text{text:'Your soundtrack'",'Music'),("  ConfigSwitch{text:'Play when desktop",'Playback'),("  RowLayout{Layout.fillWidth:true\n   Text{text:'Text color'",'Typography & color')])]:
 start=s.index(first);end=s.index('\n }\n ColumnLayout{',start)
 section=s[start:end];positions=[(section.index(marker),title) for marker,title in markers]
 groups=''
 for n,(pos,title) in enumerate(positions):
  content=section[pos:positions[n+1][0] if n+1<len(positions) else len(section)]
  if n==0:content=re.sub(r'^  Text\{[^\n]+\}\n','',content,count=1)
  groups+=group(title,content)
 s=s[:start]+groups+s[end:]
write(p,s.replace('};','}\n'))

# Text styling is grouped too, rather than another uninterrupted list.
p='ui/widgets/TypographyEditor.qml';s=untranslated((r/p).read_text())
s=s.replace('import qs.components\n','import qs.components\nimport qs.ui.widgets\n')
a=s.index(" Text{text:'Typography'");first=s.index(' RowLayout{',a)
color=s.index(" RowLayout{Layout.fillWidth:true\n  Text{text:'Text effect'",first)
motion=s.index(" ConfigSlider{text:'Rotation'",color)
end=s.rfind('}')
s=s[:a]+group('Font & layout',s[first:color])+group('Colors & effects',s[color:motion])+group('Motion',s[motion:end])+s[end:]
write(p,s.replace('};','}\n'))
