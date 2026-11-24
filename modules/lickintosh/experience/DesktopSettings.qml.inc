    ContentSection {
        title:"Desktop"
        ConfigSlider{text:"Icon size";from:32;to:128;decimals:0;value:WidgetState.iconSize;onMoved:v=>WidgetState.iconSize=Math.round(v)}
        ConfigSlider{text:"Grid spacing";from:16;to:96;decimals:0;value:WidgetState.iconSpacing;onMoved:v=>WidgetState.iconSpacing=Math.round(v)}
    }
    ContentSection {
        title:"Widgets"
        ConfigSwitch{text:"Show widgets on the Desktop";checked:WidgetState.showDesktopWidgets;onToggled:v=>WidgetState.showDesktopWidgets=v}
        RowLayout{
            Layout.fillWidth:true
            Text{text:"Widget style";color:Theme.textPrimary;Layout.fillWidth:true}
            ComboBox{model:['Automatic','Full Color','Clear','Tinted'];currentIndex:Math.max(0,['auto','color','clear','tinted'].indexOf(WidgetState.widgetStyle));onActivated:i=>WidgetState.widgetStyle=['auto','color','clear','tinted'][i]}
        }
        RowLayout{
            Layout.fillWidth:true
            Text{text:"Dim widgets on the Desktop";color:Theme.textPrimary;Layout.fillWidth:true}
            ComboBox{model:['Automatically','Always','Never'];currentIndex:Math.max(0,['auto','always','never'].indexOf(WidgetState.dimWidgets));onActivated:i=>WidgetState.dimWidgets=['auto','always','never'][i]}
        }
        RowLayout{
            visible:WidgetState.widgetStyle==='tinted';Layout.fillWidth:true
            Text{text:"Tint color";color:Theme.textPrimary;Layout.fillWidth:true}
            TextField{text:WidgetState.widgetTint;maximumLength:7;onEditingFinished:if(/^#[0-9a-fA-F]{6}$/.test(text))WidgetState.widgetTint=text}
        }
        Button{text:"Edit Widgets…";onClicked:Quickshell.execDetached(['lickintosh','ipc','call','rice','widgets'])}
    }
