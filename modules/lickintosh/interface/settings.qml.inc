    ContentSection {
        title: "Menu bar colors"
        RowLayout {
            CFText { text:"Text and icons";color:Theme.textPrimary;Layout.fillWidth:true }
            ComboBox {
                model:["Automatic contrast","Light foreground","Dark foreground","Custom color"]
                currentIndex:["auto","light","dark","custom"].indexOf(ShellConfig.options.topbar.foregroundMode)
                onActivated:i=>ShellConfig.options.topbar.foregroundMode=["auto","light","dark","custom"][i]
            }
        }
        TextField {
            Layout.fillWidth:true;visible:ShellConfig.options.topbar.foregroundMode==="custom"
            text:ShellConfig.options.topbar.foregroundColor;placeholderText:"Foreground color (#RRGGBB)"
            validator:RegularExpressionValidator {regularExpression:/#[0-9a-fA-F]{6}/}
            onEditingFinished:if(acceptableInput)ShellConfig.options.topbar.foregroundColor=text
        }
        CFText {Layout.fillWidth:true;text:"Automatic mode chooses a light or dark foreground from the wallpaper behind each side of the bar.";color:Theme.textSecondary;wrapMode:Text.WordWrap}
    }
    ContentSection {
        title:"Menu bar logo"
        ConfigSwitch {text:"Show logo";checked:ShellConfig.options.topbar.logoVisible;onToggled:v=>ShellConfig.options.topbar.logoVisible=v}
        RowLayout {
            CFText {text:"Logo";color:Theme.textPrimary;Layout.fillWidth:true}
            ComboBox {model:["Linux","Text or symbol","Custom image"];currentIndex:["linux","text","image"].indexOf(ShellConfig.options.topbar.logoType);onActivated:i=>ShellConfig.options.topbar.logoType=["linux","text","image"][i]}
        }
        TextField {Layout.fillWidth:true;visible:ShellConfig.options.topbar.logoType==="text";text:ShellConfig.options.topbar.logoText;placeholderText:"Text, symbol or emoji";onEditingFinished:ShellConfig.options.topbar.logoText=text}
        TextField {Layout.fillWidth:true;visible:ShellConfig.options.topbar.logoType==="image";text:ShellConfig.options.topbar.logoSource;placeholderText:"Image path (PNG, SVG, WebP…)";onEditingFinished:ShellConfig.options.topbar.logoSource=text}
        RowLayout {
            CFText {text:"Logo color";color:Theme.textPrimary;Layout.fillWidth:true}
            ComboBox {model:["Follow text and icons","Custom color","Original image colors"];currentIndex:["follow","custom","original"].indexOf(ShellConfig.options.topbar.logoColorMode);onActivated:i=>ShellConfig.options.topbar.logoColorMode=["follow","custom","original"][i]}
        }
        TextField {Layout.fillWidth:true;visible:ShellConfig.options.topbar.logoColorMode==="custom";text:ShellConfig.options.topbar.logoColor;placeholderText:"Logo color (#RRGGBB)";validator:RegularExpressionValidator {regularExpression:/#[0-9a-fA-F]{6}/}
            onEditingFinished:if(acceptableInput)ShellConfig.options.topbar.logoColor=text}
        ConfigSlider {text:"Logo size";from:12;to:28;value:ShellConfig.options.topbar.logoSize;onMoved:v=>ShellConfig.options.topbar.logoSize=Math.round(v)}
    }
