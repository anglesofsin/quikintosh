import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import qs.components
import qs.services
import qs.settingsapp
import qs.ui.settings.widgets
import qs.ui.topbar.statusarea.ai
ContentPage {
 id:root
 property bool showKey:false
 readonly property var providers:['anthropic','openai','google','ollama']
 SettingsCard{title:'Provider'
  SettingsRow{label:'AI Provider';kind:'choice';choices:['Anthropic (Claude)','OpenAI','Google (Gemini)','Ollama'];selection:Math.max(0,root.providers.indexOf(AiConfig.provider));onPicked:index=>AiConfig.set('provider',root.providers[index])}
  SettingsRow{visible:AiConfig.provider!=='ollama';label:'Model';kind:'field';value:AiConfig.cloudModel;separator:false;onEdited:value=>AiConfig.set('cloudModel',value)}
  SettingsRow{visible:AiConfig.provider==='ollama';label:'Server';kind:'field';value:AiConfig.ollamaHost;onEdited:value=>AiConfig.set('ollamaHost',value)}
  SettingsRow{visible:AiConfig.provider==='ollama';label:'Model';kind:'choice';choices:AiConfig.ollamaModels;selection:Math.max(0,AiConfig.ollamaModels.indexOf(AiConfig.ollamaModel));onPicked:index=>AiConfig.set('ollamaModel',AiConfig.ollamaModels[index])}
  SettingsRow{visible:AiConfig.provider==='ollama';label:'Available models';kind:'button';buttonText:'Refresh';separator:false;onActivated:AiConfig.refreshOllamaModels()}
 }
 SettingsCard{title:'API Key';visible:AiConfig.provider!=='ollama'
  RowLayout{Layout.fillWidth:true;Layout.topMargin:10;Layout.bottomMargin:10;spacing:10
   TahoeField{Layout.fillWidth:true;text:AiConfig.getKey(AiConfig.provider);echoMode:root.showKey ? TextInput.Normal:TextInput.Password;selectByMouse:true;onEditingFinished:AiConfig.setKey(AiConfig.provider,text)}
   TahoeButton{text:root.showKey ? 'Hide':'Show';onClicked:root.showKey=!root.showKey}
   TahoeButton{text:'Remove';onClicked:AiConfig.removeKey(AiConfig.provider)}
  }
  Text{visible:!AiConfig.keyringAvailable;Layout.fillWidth:true;Layout.bottomMargin:10;text:'System keyring unavailable. The key is stored in the local configuration.';color:Theme.textSecondary;font.pixelSize:11;wrapMode:Text.WordWrap}
 }
 SettingsCard{title:'Speech Recognition'
  SettingsRow{label:'Whisper model';kind:'field';value:AiConfig.whisperModel;onEdited:value=>AiConfig.set('whisperModel',value)}
  SettingsRow{label:'Language';kind:'choice';choices:['Automatic','English','Português','Français','Español'];selection:Math.max(0,['auto','en','pt','fr','es'].indexOf(AiConfig.whisperLang));separator:false;onPicked:index=>AiConfig.set('whisperLang',['auto','en','pt','fr','es'][index])}
 }
 SettingsCard{title:'Conversation History'
  SettingsRow{label:'Saved conversations';kind:'button';buttonText:'Clear History…';separator:false;onActivated:clearHistory.open()}
 }
 SettingsCard{title:'Custom Instructions'
  TextArea{Layout.fillWidth:true;Layout.preferredHeight:140;Layout.topMargin:10;Layout.bottomMargin:10;text:AiConfig.systemPrompt;placeholderText:'Instructions for your assistant';color:Theme.textPrimary;wrapMode:TextEdit.Wrap;padding:12;selectByMouse:true;background:Rectangle{radius:10;color:Theme.isLight ? '#e8e8ed':'#34343a'} onActiveFocusChanged:if(!activeFocus)AiConfig.set('systemPrompt',text)}
 }
 Dialog{id:clearHistory;parent:Overlay.overlay;anchors.centerIn:parent;modal:true;title:'Clear conversation history?';standardButtons:Dialog.Cancel|Dialog.Ok;onAccepted:AiChats.clearAllChats()}
}
