import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import qs.services
import qs.components
import qs.ui.settings.widgets
ContentPage {
 pageTitle:'Screenshots'
 ContentSection {
  title:'Capture and annotation'
  CFText {Layout.fillWidth:true;text:'Super+Shift+S selects a region or window. Print copies the display under the pointer. Super+Shift+P opens the full-display editor. Super+Shift+O selects text for OCR. Super+O opens Quickshot. The ⋯ menu contains OCR, colors, QR, palette, Lens, measuring, recording and webcam mirror.';color:Theme.textSecondary;wrapMode:Text.WordWrap}
  ConfigSwitch {text:'Save a PNG automatically when copying';checked:ShellConfig.options.capture.autoSave;onToggled:v=>ShellConfig.options.capture.autoSave=v}
  TextField {Layout.fillWidth:true;text:ShellConfig.options.capture.directory;placeholderText:'Save directory';onEditingFinished:ShellConfig.options.capture.directory=text}
  TextField {Layout.fillWidth:true;text:ShellConfig.options.capture.filenameTemplate;placeholderText:'Screenshot_{datetime}_{w}x{h}.png';onEditingFinished:ShellConfig.options.capture.filenameTemplate=text}
  CFText {Layout.fillWidth:true;text:'Filename fields: {date}, {time}, {datetime}, {w}, {h}, {mode}. PNG files are saved without overwriting previous captures.';color:Theme.textSecondary;wrapMode:Text.WordWrap}
  RowLayout {CFText {text:'Fullscreen feedback';color:Theme.textPrimary;Layout.fillWidth:true} ComboBox {model:['Flash and notification','Flash only','Off'];currentIndex:['notification','flash','off'].indexOf(ShellConfig.options.capture.feedback);onActivated:i=>ShellConfig.options.capture.feedback=['notification','flash','off'][i]}}
  ConfigSwitch {text:'Record system audio';checked:ShellConfig.options.capture.recordSystemAudio;onToggled:v=>ShellConfig.options.capture.recordSystemAudio=v}
  ConfigSwitch {text:'Record microphone';checked:ShellConfig.options.capture.recordMic;onToggled:v=>ShellConfig.options.capture.recordMic=v}
  ConfigSwitch {text:'Show cursor in recordings';checked:ShellConfig.options.capture.recordCursor;onToggled:v=>ShellConfig.options.capture.recordCursor=v}
  ConfigSwitch {text:'Show pixel magnifier';checked:ShellConfig.options.capture.magnifier;onToggled:v=>ShellConfig.options.capture.magnifier=v}
  TextField {Layout.fillWidth:true;text:ShellConfig.options.capture.ocrLanguages;placeholderText:'OCR languages (eng+por)';onEditingFinished:ShellConfig.options.capture.ocrLanguages=text}
 }
 ContentSection {
  title:'Recording and translation'
  TextField {Layout.fillWidth:true;text:ShellConfig.options.capture.videoDirectory;placeholderText:'Recording directory';onEditingFinished:ShellConfig.options.capture.videoDirectory=text}
  ConfigSlider {text:'Maximum recording duration (seconds)';from:3;to:3600;value:ShellConfig.options.capture.recordMaxSeconds;onMoved:v=>ShellConfig.options.capture.recordMaxSeconds=Math.round(v)}
  TextField {Layout.fillWidth:true;text:ShellConfig.options.capture.translateLanguage;placeholderText:'Translation target (pt, en, …)';onEditingFinished:ShellConfig.options.capture.translateLanguage=text}
 }
 ContentSection {
  title:'Editor shortcuts'
  CFText {Layout.fillWidth:true;text:'M Move · A Arrow · R Rectangle · E Ellipse · P Pen · T Text · B Mosaic\n1–4 Color · [ / ] Size · Ctrl+Z / Ctrl+Shift+Z Undo / redo\nEnter or double-click copies · Ctrl+S Save as · Esc Cancel\nC copies the pixel HEX while selecting. H shows toolbar hints.\nText: Enter commits, Shift+Enter adds a line, Esc discards the edit.\nPinned images: drag to move, scroll to resize, hover and click × to close.';color:Theme.textSecondary;wrapMode:Text.WordWrap}
 }
}
