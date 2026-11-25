import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import qs.services
import qs.components
import qs.ui.settings.widgets
ColumnLayout{
 id:root
 property var entry:({})
 signal chooseFile(string role)
 signal chooseFolder()
 function set(key,value){const changes={}
changes[key]=value;WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,changes)}
 spacing:14
 ColumnLayout{
  visible:root.entry.type==='image';Layout.fillWidth:true;spacing:12
  Text{text:'Media library';color:Theme.textSecondary;font.pixelSize:12;font.weight:Font.DemiBold}
  RowLayout{Layout.fillWidth:true;spacing:10
   TahoeButton{text:'Add files…';onClicked:root.chooseFile('media')}
   TahoeButton{text:'Choose folder…';onClicked:root.chooseFolder()}
  }
  Text{Layout.fillWidth:true;text:root.entry.mediaFolder || (root.entry.mediaFiles?.length ? root.entry.mediaFiles.length+' selected files':root.entry.image || 'No media selected');color:Theme.textSecondary;wrapMode:Text.WrapAnywhere;font.pixelSize:12}
  ListView{
   id:chosenFiles;visible:!root.entry.mediaFolder && count>0;Layout.fillWidth:true;Layout.preferredHeight:visible ? Math.min(4,count)*34:0;clip:true
   model:root.entry.mediaFiles || (root.entry.image ? [root.entry.image]:[])
   delegate:RowLayout{
    required property string modelData;required property int index
    width:chosenFiles.width;height:34;spacing:8
    Text{Layout.fillWidth:true;text:parent.modelData.split('/').pop();color:Theme.textSecondary;font.pixelSize:12;elide:Text.ElideMiddle;textFormat:Text.PlainText}
    TahoeButton{text:'×';Accessible.name:'Remove media file';onClicked:{const files=Array.from(chosenFiles.model);files.splice(parent.index,1);WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{mediaFiles:files,image:files[0] || ''})}}
   }
  }
  TahoeField{Layout.fillWidth:true;text:root.entry.mediaFolder || '';placeholderText:'Folder path';onEditingFinished:WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{mediaFolder:text.trim()})}
  ConfigSwitch{visible:!!root.entry.mediaFolder;text:'Include subfolders';checked:!!root.entry.mediaRecursive;onToggled:v=>root.set('mediaRecursive',v)}
  RowLayout{visible:!!root.entry.mediaFolder;Layout.fillWidth:true
   Text{text:'Sort files';color:Theme.textPrimary;Layout.fillWidth:true}
   TahoeCombo{model:['Name','Newest first'];currentIndex:root.entry.mediaSort==='modified' ? 1:0;onActivated:i=>root.set('mediaSort',i ? 'modified':'name')}
  }
  ConfigSwitch{text:'Shuffle';checked:!!root.entry.mediaShuffle;onToggled:v=>root.set('mediaShuffle',v)}
  RowLayout{Layout.fillWidth:true
   Text{text:'Change media every';color:Theme.textPrimary;Layout.fillWidth:true}
   TahoeCombo{model:['15 seconds','1 minute','15 minutes','Custom'];currentIndex:[15,60,900].includes(root.entry.mediaInterval ?? 60) ? [15,60,900].indexOf(root.entry.mediaInterval ?? 60):3;onActivated:i=>root.set('mediaInterval',i<3 ? [15,60,900][i]:30)}
  }
  RowLayout{Layout.fillWidth:true
   Text{text:'Interval (seconds)';color:Theme.textPrimary;Layout.fillWidth:true}
   TahoeField{Layout.preferredWidth:110;text:String(root.entry.mediaInterval ?? 60);validator:IntValidator{bottom:1;top:86400}
onEditingFinished:if(acceptableInput)root.set('mediaInterval',Number(text))}
  }
  RowLayout{Layout.fillWidth:true
   Text{text:'Transition';color:Theme.textPrimary;Layout.fillWidth:true}
   TahoeCombo{model:['Dissolve','Slide','Zoom','Cut'];currentIndex:Math.max(0,['dissolve','slide','zoom','cut'].indexOf(root.entry.mediaTransition || 'dissolve'));onActivated:i=>root.set('mediaTransition',['dissolve','slide','zoom','cut'][i])}
  }
  ConfigSlider{visible:root.entry.mediaTransition!=='cut';text:'Transition duration (ms)';from:100;to:2000;decimals:0;value:root.entry.mediaTransitionMs ?? 550;onMoved:v=>root.set('mediaTransitionMs',Math.round(v))}
  ConfigSwitch{text:'Finish video before advancing';checked:!!root.entry.mediaFinishVideo;onToggled:v=>root.set('mediaFinishVideo',v)}
  ConfigSwitch{text:'Video sound';checked:!!root.entry.mediaSound;onToggled:v=>root.set('mediaSound',v)}
  ConfigSlider{visible:!!root.entry.mediaSound;text:'Video volume (%)';from:0;to:100;decimals:0;value:(root.entry.mediaVolume ?? .35)*100;onMoved:v=>root.set('mediaVolume',v/100)}
  RowLayout{Layout.fillWidth:true
   Text{text:'Media fit';color:Theme.textPrimary;Layout.fillWidth:true}
   TahoeCombo{model:['Fill','Fit','Stretch'];currentIndex:Math.max(0,['crop','fit','stretch'].indexOf(root.entry.imageFit || 'crop'));onActivated:i=>root.set('imageFit',['crop','fit','stretch'][i])}
  }
  RowLayout{Layout.fillWidth:true
   Text{text:'Shape';color:Theme.textPrimary;Layout.fillWidth:true}
   TahoeCombo{model:['Rounded','Rectangle','Circle'];currentIndex:Math.max(0,['rounded','rectangle','circle'].indexOf(root.entry.shape || 'rounded'));onActivated:i=>root.set('shape',['rounded','rectangle','circle'][i])}
  }
  TahoeButton{text:'Clear media';onClicked:WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{image:'',mediaFolder:'',mediaFiles:[]})}
 }
 ColumnLayout{
  visible:root.entry.type==='musicsticker';Layout.fillWidth:true;spacing:12
  Text{text:'Your soundtrack';color:Theme.textSecondary;font.pixelSize:12;font.weight:Font.DemiBold}
  RowLayout{Layout.fillWidth:true
   TahoeButton{text:'Choose music…';onClicked:root.chooseFile('audio')}
   TahoeButton{text:'Choose cover…';onClicked:root.chooseFile('cover')}
  }
  Text{Layout.fillWidth:true;text:root.entry.audioFile || 'No audio selected';color:Theme.textSecondary;font.pixelSize:12;wrapMode:Text.WrapAnywhere}
  RowLayout{Layout.fillWidth:true
   Text{text:'Design';color:Theme.textPrimary;Layout.fillWidth:true}
   TahoeCombo{model:['Music card','Spinning record'];currentIndex:root.entry.variant==='disc' ? 1:0;onActivated:i=>root.set('variant',i ? 'disc':'card')}
  }
  TahoeField{Layout.fillWidth:true;placeholderText:'Song title';text:root.entry.musicTitle || '';onEditingFinished:root.set('musicTitle',text)}
  TahoeField{Layout.fillWidth:true;placeholderText:'Artist / author';text:root.entry.musicArtist || '';onEditingFinished:root.set('musicArtist',text)}
  TahoeField{Layout.fillWidth:true;placeholderText:'Description';text:root.entry.musicDescription || '';onEditingFinished:root.set('musicDescription',text)}
  ConfigSwitch{text:'Play when desktop is focused';checked:root.entry.musicAutoPlay!==false;onToggled:v=>root.set('musicAutoPlay',v)}
  ConfigSwitch{text:'Repeat music';checked:root.entry.musicLoop!==false;onToggled:v=>root.set('musicLoop',v)}
  ConfigSwitch{text:'Mute';checked:!!root.entry.musicMuted;onToggled:v=>root.set('musicMuted',v)}
  ConfigSlider{text:'Music volume (%)';from:0;to:100;decimals:0;value:(root.entry.musicVolume ?? .35)*100;onMoved:v=>root.set('musicVolume',v/100)}
  ConfigSwitch{text:'Show playback controls';checked:root.entry.musicControls!==false;onToggled:v=>root.set('musicControls',v)}
  RowLayout{Layout.fillWidth:true
   Text{text:'Text color';color:Theme.textPrimary;Layout.fillWidth:true}
   TahoeCombo{model:['Follow appearance','Wallpaper accent','Custom'];currentIndex:Math.max(0,['auto','accent','custom'].indexOf(root.entry.musicColorMode || 'auto'));onActivated:i=>root.set('musicColorMode',['auto','accent','custom'][i])}
  }
  ColorSetting{visible:root.entry.musicColorMode==='custom';label:'Music color';value:root.entry.musicColor || Theme.textPrimary;onPicked:v=>root.set('musicColor',String(v))}
  TahoeField{Layout.fillWidth:true;placeholderText:'Title font family';text:root.entry.musicFont || '';onEditingFinished:root.set('musicFont',text)}
  ConfigSlider{text:'Title size';from:12;to:56;decimals:0;value:root.entry.musicFontSize || 20;onMoved:v=>root.set('musicFontSize',Math.round(v))}
 }
 ColumnLayout{
  visible:root.entry.type==='textsticker';Layout.fillWidth:true;spacing:12
  Text{text:'Your words';color:Theme.textSecondary;font.pixelSize:12;font.weight:Font.DemiBold}
  ScrollView{Layout.fillWidth:true;Layout.preferredHeight:140;clip:true
   TextArea{id:words;wrapMode:TextEdit.Wrap;selectByMouse:true;color:Theme.textPrimary;font.pixelSize:17;text:root.entry.textContent || '';placeholderText:'Write something…';onTextChanged:if(activeFocus)saveWords.restart();Timer{id:saveWords;interval:500;onTriggered:if(words.text!==(root.entry.textContent || ''))root.set('textContent',words.text)}
background:Rectangle{radius:12;color:Theme.fillControl}}
  }
 }
 ColumnLayout{
  visible:root.entry.type==='lyricssticker';Layout.fillWidth:true;spacing:12
  Text{text:'Live lyrics';color:Theme.textSecondary;font.pixelSize:12;font.weight:Font.DemiBold}
  ConfigSwitch{text:'Enable live lyrics';checked:root.entry.lyricsEnabled!==false;onToggled:v=>root.set('lyricsEnabled',v)}
  RowLayout{Layout.fillWidth:true
   Text{text:'Layout';color:Theme.textPrimary;Layout.fillWidth:true}
   TahoeCombo{model:['Current line','Surrounding lines','Line progress'];currentIndex:Math.max(0,['line','stacked','karaoke'].indexOf(root.entry.variant || 'stacked'));onActivated:i=>root.set('variant',['line','stacked','karaoke'][i])}
  }
  ConfigSwitch{text:'Show song title';checked:root.entry.lyricsTrack!==false;onToggled:v=>root.set('lyricsTrack',v)}
  ConfigSlider{text:'Synchronization offset (seconds)';from:-15;to:15;decimals:1;value:root.entry.lyricsOffset || 0;onMoved:v=>root.set('lyricsOffset',v)}
  RowLayout{Layout.fillWidth:true
   TahoeButton{text:'Choose LRC…';onClicked:root.chooseFile('lyrics')}
   TahoeButton{visible:!!root.entry.lyricsFile;text:'Use online lyrics';onClicked:root.set('lyricsFile','')}
  }
  Text{visible:!!root.entry.lyricsFile;Layout.fillWidth:true;text:root.entry.lyricsFile || '';color:Theme.textSecondary;font.pixelSize:12;wrapMode:Text.WrapAnywhere}
 }
 TypographyEditor{visible:['textsticker','lyricssticker'].includes(root.entry.type);Layout.fillWidth:true;entry:root.entry}
}
