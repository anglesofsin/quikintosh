"""Public visual snapshots exclude content; restore preserves private settings."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('visual_profile',Path(__file__).parents[1]/'scripts/visual-profile.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class ProfileTests(unittest.TestCase):
 def test_export_omits_private_content_and_paths(self):
  with tempfile.TemporaryDirectory() as tmp:
   home=Path(tmp);base=home/'.config/lickintosh';(base/'core').mkdir(parents=True)
   (base/'shell-config.json').write_text(json.dumps({'appearance':{'mode':'dark','apiKey':'PRIVATE_SENTINEL'},'wallpaper':{'path':'/home/user/PRIVATE_SENTINEL.mp4','videoFps':60},'topbar':{'logoText':'PRIVATE_SENTINEL'},'dock':{'pinnedFiles':['PRIVATE_SENTINEL']}}))
   (base/'core/settings-preferences.json').write_text(json.dumps({'profile':{'displayName':'PRIVATE_SENTINEL','autoAppearance':True},'servers':['PRIVATE_SENTINEL'],'inputOverrides':{'plugin:secretToken':'PRIVATE_SENTINEL'},'notifications':{'sounds':True,'rules':['PRIVATE_SENTINEL']}}))
   (base/'core/widgets.json').write_text(json.dumps({'desktop':[{'text':'PRIVATE_SENTINEL'}],'iconPositions':{'PRIVATE_SENTINEL':[0,0]},'iconSize':64}))
   data=p.export(home);self.assertNotIn('PRIVATE_SENTINEL',json.dumps(data));self.assertEqual(data['files'][p.ROOT+'shell-config.json']['json']['wallpaper']['videoFps'],60)
 def test_preview_does_not_mutate_and_restore_merges_with_backup(self):
  with tempfile.TemporaryDirectory() as tmp:
   home=Path(tmp);target=home/p.ROOT/'core/settings-preferences.json';target.parent.mkdir(parents=True)
   old={'servers':['keep private'],'accessibility':{'reduceMotion':False,'increaseContrast':True}};target.write_text(json.dumps(old))
   profile={'schema':1,'files':{p.ROOT+'core/settings-preferences.json':{'json':{'accessibility':{'reduceMotion':True}}}}}
   _,backup=p.restore(profile,home);self.assertIsNone(backup);self.assertEqual(json.loads(target.read_text()),old)
   _,backup=p.restore(profile,home,True);new=json.loads(target.read_text());self.assertTrue(new['accessibility']['reduceMotion']);self.assertTrue(new['accessibility']['increaseContrast']);self.assertEqual(new['servers'],old['servers'])
   self.assertEqual(json.loads((Path(backup)/p.ROOT/'core/settings-preferences.json').read_text()),old);self.assertEqual(target.stat().st_mode&0o777,0o600)
 def test_rejects_traversal_and_symlink_parent(self):
  with tempfile.TemporaryDirectory() as tmp,tempfile.TemporaryDirectory() as outside:
   home=Path(tmp)
   with self.assertRaises(ValueError):p.restore({'schema':1,'files':{'../file':{'text':'x'}}},home,True)
   (home/'.config').symlink_to(outside,target_is_directory=True)
   with self.assertRaises(ValueError):p.restore({'schema':1,'files':{p.ROOT+'shell-config.json':{'json':{}}}},home,True)
if __name__=='__main__':unittest.main()
