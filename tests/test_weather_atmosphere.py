"""Offscreen weather lifecycle checks, without user services or desktop changes."""
from pathlib import Path
import tempfile,unittest
import test_qml_interface as qml
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(qml.QS,'Quickshell is required')
class WeatherAtmosphere(unittest.TestCase):
 def test_saved_weather_settings_do_not_restart_removed_effects(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   (root/'WeatherAtmosphere.qml').write_text((ROOT/'modules/lickintosh/personalization/WeatherAtmosphere.qml').read_text())
   result=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
Scope {
 Item { WeatherAtmosphere { id:weather;width:320;height:160;kind:'storm';active:true;intensity:2;speed:2;lightning:true } }
 Timer { interval:100;running:true;onTriggered: {
  if(weather.children.length!==0){Qt.exit(10);return}
  weather.kind='rain';weather.active=false;weather.active=true
  if(weather.children.length!==0){Qt.exit(11);return}
  console.log('WEATHER_ASSET_ONLY_OK');Qt.quit()
 }}
}''')
   self.assertIn('WEATHER_ASSET_ONLY_OK',result)
if __name__=='__main__':unittest.main()
