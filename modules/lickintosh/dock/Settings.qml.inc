    ContentSection {
        title: "Tahoe Dock"
        RowLayout {
            Layout.fillWidth:true
            Text {text:"Position on screen";color:Theme.textPrimary;Layout.fillWidth:true}
            ComboBox {model:['Bottom','Left','Right'];currentIndex:['bottom','left','right'].indexOf(ShellConfig.options.dockAppearance.position);onActivated:i=>ShellConfig.options.dockAppearance.position=['bottom','left','right'][i]}
        }
        ConfigSwitch {text:"Show Trash";checked:ShellConfig.options.dockAppearance.showTrash;onToggled:v=>ShellConfig.options.dockAppearance.showTrash=v}
        ConfigSwitch {text:"Ask before emptying Trash";checked:ShellConfig.options.dockAppearance.confirmEmptyTrash;onToggled:v=>ShellConfig.options.dockAppearance.confirmEmptyTrash=v}
        ConfigSwitch {text:"Show Downloads stack";checked:ShellConfig.options.dockAppearance.showDownloads;onToggled:v=>ShellConfig.options.dockAppearance.showDownloads=v}
        RowLayout {
            Layout.fillWidth:true
            Text {text:"Display folders as";color:Theme.textPrimary;Layout.fillWidth:true}
            ComboBox {model:['Stack of files','Folder'];currentIndex:ShellConfig.options.dockAppearance.stackDisplay==='folder' ? 1 : 0;onActivated:i=>ShellConfig.options.dockAppearance.stackDisplay=i===1 ? 'folder' : 'stack'}
        }
        ConfigSwitch {text:"Show Recent Files stack";checked:ShellConfig.options.dockAppearance.showRecentFiles;onToggled:v=>ShellConfig.options.dockAppearance.showRecentFiles=v}
        ConfigSwitch {text:"Show recent applications";checked:ShellConfig.options.dockAppearance.showRecentApps;onToggled:v=>ShellConfig.options.dockAppearance.showRecentApps=v}
        ConfigSlider {text:"Recent application count";from:1;to:6;decimals:0;value:ShellConfig.options.dockAppearance.recentAppCount;onMoved:v=>ShellConfig.options.dockAppearance.recentAppCount=Math.round(v)}
        Text {Layout.fillWidth:true;text:"Apps excluded from Recents";color:Theme.textPrimary;font.pixelSize:13;font.bold:true}
        Text {Layout.fillWidth:true;visible:ShellConfig.options.dockAppearance.recentAppBlacklist.length===0;text:"No blocked apps. Right-click a recent app and choose Never Show in Recents.";color:Theme.textSecondary;wrapMode:Text.WordWrap;font.pixelSize:12}
        Repeater {
            model:ShellConfig.options.dockAppearance.recentAppBlacklist
            RowLayout {
                required property var modelData
                Layout.fillWidth:true
                Text {Layout.fillWidth:true;text:parent.modelData.name || parent.modelData.key || String(parent.modelData);color:Theme.textPrimary;elide:Text.ElideRight}
                Button {text:"Allow again";onClicked:{const key=parent.modelData.key || parent.modelData;ShellConfig.options.dockAppearance.recentAppBlacklist=ShellConfig.options.dockAppearance.recentAppBlacklist.filter(app=>(app.key || app)!==key)}}
            }
        }

        RowLayout {
            Layout.fillWidth:true
            Text {text:"View stack contents as";color:Theme.textPrimary;Layout.fillWidth:true}
            ComboBox {model:['Automatic','Fan','Grid','List'];currentIndex:['automatic','fan','grid','list'].indexOf(ShellConfig.options.dockAppearance.stackView);onActivated:i=>ShellConfig.options.dockAppearance.stackView=['automatic','fan','grid','list'][i]}
        }
        RowLayout {
            Layout.fillWidth:true
            Text {text:"Sort folders by";color:Theme.textPrimary;Layout.fillWidth:true}
            ComboBox {model:['Date modified','Date added','Date created','Name','Kind','Size'];currentIndex:['modified','added','created','name','kind','size'].indexOf(ShellConfig.options.dockAppearance.stackSort);onActivated:i=>ShellConfig.options.dockAppearance.stackSort=['modified','added','created','name','kind','size'][i]}
        }
        ConfigSwitch {text:"Minimize windows into application icon";checked:ShellConfig.options.dockAppearance.minimizeToAppIcon;onToggled:v=>ShellConfig.options.dockAppearance.minimizeToAppIcon=v}
        ConfigSwitch {text:"Animate opening applications";checked:ShellConfig.options.dockAppearance.animateOpening;onToggled:v=>ShellConfig.options.dockAppearance.animateOpening=v}
        ConfigSwitch {text:"Show indicators for open applications";checked:ShellConfig.options.dockAppearance.showIndicators;onToggled:v=>ShellConfig.options.dockAppearance.showIndicators=v}
        ConfigSlider {text:"Auto-hide delay";from:0;to:1500;decimals:0;valueSuffix:" ms";value:ShellConfig.options.dockAppearance.hideDelay;onMoved:v=>ShellConfig.options.dockAppearance.hideDelay=Math.round(v)}
        Text {Layout.fillWidth:true;wrapMode:Text.WordWrap;color:Theme.textSecondary;font.pixelSize:12;text:"Drag pinned apps to reorder them, or drag away from the Dock to remove their shortcuts. Drop local files on Trash to move them to the system trash. Window hiding and restoring use Hyprland; Apple's Genie animation and Handoff are not available."}
    }
