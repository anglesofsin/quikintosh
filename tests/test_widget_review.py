"""Playback arbitration, font provenance and configurable world clocks."""
from pathlib import Path
import hashlib,importlib.util,json,tempfile,unittest
import test_qml_interface as qml
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'modules/lickintosh/widget-review'
class ReviewAssets(unittest.TestCase):
 def test_fonts_are_pinned_and_licensed(self):
  manifest=json.loads((SOURCE/'fonts/SOURCES.json').read_text());self.assertEqual(len(manifest['fonts']),10)
  for entry in manifest['fonts']:
   folder=SOURCE/'fonts'/entry['family'];self.assertEqual(hashlib.sha256((folder/entry['file']).read_bytes()).hexdigest(),entry['sha256']);self.assertIn('SIL OPEN FONT LICENSE',(folder/'OFL.txt').read_text());self.assertIn(manifest['commit'],entry['source'])
 def test_zones_validate_unknown_and_malicious_inputs(self):
  spec=importlib.util.spec_from_file_location('zones',SOURCE/'zones.py');zones=importlib.util.module_from_spec(spec);spec.loader.exec_module(zones)
  data=zones.clocks([{'tz':'Etc/UTC'},{'tz':'America/Sao_Paulo'},{'tz':'invalid/zone'},{'tz':'$(touch /tmp/nope)'}]);self.assertTrue(data['Etc/UTC']['valid']);self.assertRegex(data['Etc/UTC']['time'],r'^\d{2}:\d{2}$');self.assertFalse(data['invalid/zone']['valid']);self.assertFalse(data['$(touch /tmp/nope)']['valid'])
@unittest.skipUnless(qml.QS,'Set QUICKINTOSH_TEST_QS for offscreen checks')
class AudioPolicy(unittest.TestCase):
 def test_foreign_playback_blocks_widgets_without_feedback(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);services=root/'services';services.mkdir()
   for name in ['AudioActivity.qml','audio-policy.js']:(services/name).write_text((SOURCE/name).read_text())
   (services/'MprisState.qml').write_text('pragma Singleton\nimport Quickshell\nSingleton{property var players:[]}')
   (services/'qmldir').write_text('module qs.services\nsingleton AudioActivity AudioActivity.qml\nsingleton MprisState MprisState.qml\n')
   output=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
import qs.services
Scope{
 function node(pid,state,role,muted){return {info:{state:state,props:{'media.class':'Stream/Output/Audio','application.process.id':pid,'application.name':'Fixture','media.role':role},params:{Props:[{mute:muted}]}}}}
 function check(ok,label){if(!ok){console.error(label);Qt.exit(71)}}
 Timer{interval:50;running:true;onTriggered:{
  check(!AudioActivity.mayPlay,'wait for inventory')
  AudioActivity.observe([node(Quickshell.processId,'running','Music',false),node(123,'idle','Music',false),node(124,'running','Notification',false),node(125,'running','Music',true)])
  check(AudioActivity.mayPlay,'own, idle, notification and muted streams ignored')
  MprisState.players=[{isPlaying:true}];check(!AudioActivity.mayPlay,'MPRIS playback wins')
  MprisState.players=[];AudioActivity.observe([node(123,'running','Video',false)])
  check(!AudioActivity.mayPlay && AudioActivity.apps.length===1,'active external video wins')
  AudioActivity.observe([]);check(!AudioActivity.mayPlay,'hold before resuming')
 }}
 Timer{interval:1450;running:true;onTriggered:{check(AudioActivity.mayPlay,'resume after quiet interval');console.log('AUDIO_POLICY_OK');Qt.quit()}}
}''');self.assertIn('AUDIO_POLICY_OK',output)
if __name__=='__main__':unittest.main()
