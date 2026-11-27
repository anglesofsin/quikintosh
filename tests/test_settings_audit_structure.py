"""Settings transforms preserve routes and actions while fixing layout ownership."""
import importlib.util,os,re,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('audit',Path(__file__).parents[1]/'modules/lickintosh/island-shelf/settings_audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
BASE=Path(os.environ.get("QI_SETTINGS_BASE_SOURCE","/nix/store/3f39p07cv6iny38szjbkcy2h9j1vsrl9-lickintosh-source-reference-shelf"))
@unittest.skipUnless(BASE.exists(),"Set QI_SETTINGS_BASE_SOURCE to the pre-audit assembled source")
class AuditStructure(unittest.TestCase):
 def test_island_keeps_existing_actions_and_groups(self):
  before=(BASE/'ui/settings/pages/RosaPage.qml').read_text()
  after=audit.island_page(before)
  for expression in re.findall(r'(?:Rosa\.IslandConfig\.setStyle\([^\n]+|SettingsPreferences\.[\w.]+)',before):self.assertIn(expression,after)
  for section in ['Shape & Material','Navigation & Favorites','Contextual Icons','Calls & Privacy','Advanced']:self.assertIn(section,after)
  self.assertIn('root.advancedOptions ? Rosa.IslandConfig.groups:[]',after)
  self.assertIn('["auto","focus","minimized"]',after)
 def test_paths_keep_action_and_dialog(self):
  source=(BASE/'settingsapp/SettingsPathRow.qml').read_text();after=audit.path_row(source)
  self.assertEqual(source.count('root.edited('),after.count('root.edited('));self.assertIn('FolderDialog',after);self.assertNotIn('Layout.maximumWidth:root.width*.47',after)
if __name__=='__main__':unittest.main()
