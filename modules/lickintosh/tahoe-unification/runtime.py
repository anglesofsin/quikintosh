"""Unify runtime appearance scheduling and rice-local Spotlight actions."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
def save(name,s):
 p=root/name;p.chmod(p.stat().st_mode|0o200);p.write_text(s)
p=root/'settingsapp/SettingsRuntime.qml';s=p.read_text();old="  if(SettingsPreferences.profile.autoAppearance){const mode=time>=420 && time<1140 ? 'light':'dark';if(ShellConfig.options.appearance.mode!==mode)Theme.setMode(mode)}";assert old in s
s=s.replace(old,"""  if(SettingsPreferences.profile.autoAppearance){
   const dawn=WeatherState.available && WeatherState.sunrise ? root.minutes(WeatherState.sunrise):420
   const dusk=WeatherState.available && WeatherState.sunset ? root.minutes(WeatherState.sunset):1140
   const mode=time>=dawn && time<dusk ? 'light':'dark'
   if(ShellConfig.options.appearance.mode!==mode)Theme.setMode(mode)
  }""");save('settingsapp/SettingsRuntime.qml',s)
p=root/'ui/topbar/statusarea/spotlight/SpotlightWindow.qml';s=p.read_text().replace('~/.config/quickshell/spotlight/actions/','~/.config/lickintosh/spotlight/actions/').replace('~/.cache/quickshell/spotlight_file_index.txt','~/.cache/lickintosh/spotlight_file_index.txt').replace('mkdir -p ~/.cache/quickshell','mkdir -p ~/.cache/lickintosh');save('ui/topbar/statusarea/spotlight/SpotlightWindow.qml',s)
