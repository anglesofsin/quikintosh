"""Offscreen weather lifecycle checks, without user services or desktop changes."""
from pathlib import Path
import tempfile,unittest
import test_qml_interface as qml
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(qml.QS,'Quickshell is required')
class WeatherAtmosphere(unittest.TestCase):
 def test_conditions_and_motion_policy(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);services=root/'services';services.mkdir()
   (services/'qmldir').write_text('module qs.services\nsingleton RenderingState RenderingState.qml\nsingleton SettingsPreferences SettingsPreferences.qml\n')
   for name,body in [('RenderingState','property bool ambientAnimations:true'),('SettingsPreferences','property bool locked:false')]:
    (services/(name+'.qml')).write_text('pragma Singleton\nimport QtQuick\nQtObject{'+body+'}')
   (root/'WeatherAtmosphere.qml').write_text((ROOT/'modules/lickintosh/personalization/WeatherAtmosphere.qml').read_text())
   result=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
import qs.services
Scope{
 Item{WeatherAtmosphere{id:weather;width:320;height:160;kind:'rain'}}
 property int step:0
 Timer{interval:60;running:true;repeat:true;onTriggered:{
  if(step===0){if(!weather.rain || !weather.running){Qt.exit(10);return};weather.kind='thunderstorm'}
  if(step===1){if(!weather.storm){Qt.exit(11);return};RenderingState.ambientAnimations=false}
  if(step===2){if(weather.running){Qt.exit(12);return};RenderingState.ambientAnimations=true;SettingsPreferences.locked=true}
  if(step===3){if(weather.running){Qt.exit(13);return};SettingsPreferences.locked=false;weather.active=false}
  if(step===4){if(weather.running){Qt.exit(14);return};weather.active=true;weather.kind='clear'}
  if(step===5){if(weather.running || weather.rain || weather.snow){Qt.exit(15);return};console.log('WEATHER_POLICY_OK');Qt.quit()}
  step++
 }}
}''')
   self.assertIn('WEATHER_POLICY_OK',result)
if __name__=='__main__':unittest.main()
