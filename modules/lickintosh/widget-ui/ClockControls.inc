     ColumnLayout{visible:root.entry.type==='personalclock';Layout.fillWidth:true;spacing:14
      RowLayout{Layout.fillWidth:true
       Text{text:'Design';color:Theme.textPrimary;Layout.fillWidth:true}
       TahoeCombo{model:['Classic','Stacked','Minimal'];currentIndex:Math.max(0,['classic','stacked','minimal'].indexOf(root.entry.variant || 'classic'));onActivated:i=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{variant:['classic','stacked','minimal'][i]})}
      }
      Text{text:'Clock Typography';color:Theme.textSecondary;font.pixelSize:12;font.weight:Font.DemiBold}
      TahoeCombo{Layout.fillWidth:true;model:LockClockStyle.styles.map(style=>style.name);currentIndex:root.entry.clockStyle ?? (root.entry.variant==='minimal' ? 3:root.entry.variant==='stacked' ? 1:0);onActivated:index=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockStyle:index,clockFont:''})}
      TahoeField{Layout.fillWidth:true;text:root.entry.clockFont || '';placeholderText:'Custom font family';onEditingFinished:WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockFont:text.trim()})}
      ConfigSwitch{text:'Scale text with widget';checked:root.entry.clockAutoSize ?? (root.entry.clockSize===undefined);onToggled:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockAutoSize:value})}
      ConfigSlider{visible:!(root.entry.clockAutoSize ?? (root.entry.clockSize===undefined));text:'Font size';from:20;to:500;decimals:0;value:root.entry.clockSize || 76;onMoved:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockSize:Math.round(value),clockAutoSize:false})}
      ConfigSlider{text:'Weight';from:0;to:1;decimals:2;value:root.entry.clockWeight ?? (root.entry.variant==='minimal' ? .25:root.entry.variant==='stacked' ? .4:.6);onMoved:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockWeight:value})}
      ConfigSlider{text:'Letter spacing';from:-4;to:20;decimals:1;value:root.entry.clockSpacing ?? LockClockStyle.styleAt(root.entry.clockStyle || 0).spacing;onMoved:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockSpacing:value})}
      ConfigSwitch{text:'Italic';checked:root.entry.clockItalic ?? LockClockStyle.styleAt(root.entry.clockStyle || 0).italic;onToggled:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockItalic:value})}
      RowLayout{Layout.fillWidth:true
       Text{text:'Text alignment';color:Theme.textPrimary;Layout.fillWidth:true}
       TahoeCombo{model:['Left','Center','Right'];currentIndex:Math.max(0,['left','center','right'].indexOf(root.entry.clockAlign || 'center'));onActivated:i=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockAlign:['left','center','right'][i]})}
      }
      RowLayout{Layout.fillWidth:true
       Text{text:'Text effect';color:Theme.textPrimary;Layout.fillWidth:true}
       TahoeCombo{model:['Solid','Liquid Glass','Gradient','Shadow'];currentIndex:Math.max(0,['solid','glass','gradient','shadow'].indexOf(root.entry.clockEffect || 'solid'));onActivated:i=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockEffect:['solid','glass','gradient','shadow'][i]})}
      }
      ConfigSwitch{text:'Animate changing digits';checked:!!root.entry.clockAnimate;onToggled:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockAnimate:value})}
      ConfigSwitch{text:'Use accent color';checked:root.entry.clockColorMode==='accent';onToggled:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockColorMode:value ? 'accent':'custom'})}
      ColorSetting{visible:root.entry.clockColorMode!=='accent';label:'Clock color';value:root.entry.clockColor || Theme.textPrimary;onPicked:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockColor:String(value)})}
      ColorSetting{visible:root.entry.clockEffect==='gradient';label:'Gradient color';value:root.entry.clockGradientColor || Theme.accent;onPicked:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockGradientColor:String(value)})}
      ConfigSlider{visible:root.entry.clockEffect==='glass';text:'Glass highlight';from:0;to:1;decimals:2;value:root.entry.clockGlassHighlight ?? .55;onMoved:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockGlassHighlight:value})}
      Text{text:'Time & Date';color:Theme.textSecondary;font.pixelSize:12;font.weight:Font.DemiBold}
      ConfigSwitch{text:'12-hour clock';checked:!!root.entry.clock12Hour;onToggled:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clock12Hour:value})}
      ConfigSwitch{text:'Show seconds';checked:!!root.entry.clockSeconds;onToggled:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockSeconds:value})}
      TahoeField{Layout.fillWidth:true;text:root.entry.clockFormat || '';placeholderText:'Custom time format';onEditingFinished:WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockFormat:text.trim()})}
      ConfigSwitch{text:'Show date';checked:root.entry.clockDate ?? (root.entry.variant!=='minimal');onToggled:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockDate:value})}
      RowLayout{visible:root.entry.clockDate ?? (root.entry.variant!=='minimal');Layout.fillWidth:true
       Text{text:'Date position';color:Theme.textPrimary;Layout.fillWidth:true}
       TahoeCombo{model:['Above time','Below time'];currentIndex:(root.entry.clockDatePosition || (root.entry.variant==='stacked' ? 'below':'above'))==='below' ? 1:0;onActivated:i=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockDatePosition:i ? 'below':'above'})}
      }
      TahoeField{visible:root.entry.clockDate ?? (root.entry.variant!=='minimal');Layout.fillWidth:true;text:root.entry.clockDateFormat || '';placeholderText:'Custom date format';onEditingFinished:WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockDateFormat:text.trim()})}
      ConfigSlider{visible:root.entry.clockDate ?? (root.entry.variant!=='minimal');text:'Date size';from:10;to:72;decimals:0;value:root.entry.clockDateSize || 14;onMoved:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockDateSize:Math.round(value)})}
      ConfigSlider{visible:root.entry.clockDate ?? (root.entry.variant!=='minimal');text:'Date spacing';from:0;to:40;decimals:0;value:root.entry.clockDateGap ?? 6;onMoved:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockDateGap:Math.round(value)})}
     }
