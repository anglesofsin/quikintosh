"""Hot-path regressions: unchanged app state must not rewrite the history."""
import io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,MagicMock
import backend
class HistoryPerformance(unittest.TestCase):
 def test_repeated_remember_and_focus_preserve_history(self):
  with tempfile.TemporaryDirectory() as directory:
   state=Path(directory);app={'key':'example','desktopId':'example.desktop','name':'Example','icon':'example'};history=state/'recent-apps.json';history.write_text(json.dumps([app]));before=history.stat().st_mtime_ns
   requests=[{'action':'remember','apps':[app]},{'action':'focus','key':'example'}]*40
   catalog=MagicMock();catalog.sanitize.side_effect=lambda rows:rows
   with patch.object(backend,'STATE',state),patch.object(backend,'Watcher'),patch.object(backend,'AppCatalog',return_value=catalog),patch.object(backend,'trashcount',return_value=0),patch.object(backend,'capture_directory',return_value=state),patch.object(backend.sys,'stdin',io.StringIO(''.join(json.dumps(r)+'\n' for r in requests))),patch.object(backend,'emit') as emit,patch.object(backend.signal,'signal'):
    backend.main()
   self.assertEqual(history.stat().st_mtime_ns,before)
   self.assertEqual([call.args[0] for call in emit.call_args_list],['ready'])
 def test_thumbnail_queue_is_bounded_and_failed_files_are_not_retried(self):
  with tempfile.TemporaryDirectory() as directory:
   home=Path(directory);paths=[]
   for n in range(3):
    path=home/(str(n)+'.png');path.write_bytes(b'not an image');paths.append(path)
   with patch.object(backend,'HOME',home),patch.object(backend,'_pending',set()),patch.object(backend,'_failed',{}),patch.object(backend,'MAX_PENDING',2),patch.object(backend,'_pool') as pool,patch.object(backend,'emit'):
    for path in paths:backend.fileitem(path)
    self.assertEqual(pool.submit.call_count,2);self.assertEqual(len(backend._pending),2)
    backend.make_thumbnail(paths[0]);self.assertIn(str(paths[0]),backend._failed)
    before=pool.submit.call_count;backend.fileitem(paths[0]);self.assertEqual(pool.submit.call_count,before)
 def test_large_trash_only_generates_thumbnails_for_returned_items(self):
  with tempfile.TemporaryDirectory() as directory:
   home=Path(directory);files=home/'Trash/files';files.mkdir(parents=True);(home/'Trash/info').mkdir()
   for n in range(30):(files/(str(n)+'.png')).write_bytes(b'not an image')
   with patch.object(backend,'HOME',home),patch.dict(backend.os.environ,{'XDG_DATA_HOME':str(home)}),patch.object(backend,'_pending',set()),patch.object(backend,'_pool') as pool:
    result=backend.trashfiles(limit=3);self.assertEqual(len(result),3);self.assertEqual(pool.submit.call_count,3)

if __name__=='__main__':unittest.main()
