import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('picker',Path(__file__).resolve().parents[1]/'modules/lickintosh/share-picker/picker.py')
picker=importlib.util.module_from_spec(spec);spec.loader.exec_module(picker)
class PickerProtocol(unittest.TestCase):
 def groups(self):return picker.sources({'XDPH_OUTPUT_SHARING_LIST':'6:HDMI-1:-1920:0:1920:1080;','XDPH_WINDOW_SHARING_LIST':'42[HC>]discord[HT>]Call[HE>]0xabc[HA>]','XDPH_WORKSPACE_SHARING_LIST_V3':'9[HN>]2:é[HM>]1:6:HDMI-1[HE>]'})
 def test_length_prefix_uses_bytes(self):self.assertEqual(self.groups()[2][0]['title'],'é')
 def test_window_handle_is_portal_handle(self):self.assertEqual(picker.selection({'kind':'window','key':'42'},self.groups()),'[SELECTION]/window:42')
 def test_unknown_source_is_rejected(self):self.assertEqual(picker.selection({'kind':'window','key':'43'},self.groups()),'')
 def test_region_relative_to_negative_monitor(self):self.assertEqual(picker.selection({'kind':'region','key':'-1800,20,100,80','remember':True},self.groups()),'[SELECTION]r/region:HDMI-1@120,20,100,80')
 def test_cancel_emits_nothing(self):self.assertEqual(picker.selection({},self.groups()),'')
if __name__=='__main__':unittest.main()
