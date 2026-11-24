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
if __name__=='__main__':unittest.main()
