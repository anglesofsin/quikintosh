from pathlib import Path
import importlib.util,os,socket,tempfile,unittest
spec=importlib.util.spec_from_file_location('benchmark',Path(__file__).resolve().parents[1]/'modules/lickintosh/live-backdrop/benchmark.py')
bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(bench)
class BenchmarkSafety(unittest.TestCase):
 def test_host_output_is_rejected(self):
  with self.assertRaises(ValueError):bench.private_environment('/run/user/'+str(os.getuid()),'wayland-1','host')
 def test_private_sockets_and_no_path_traversal(self):
  with tempfile.TemporaryDirectory(prefix='qi-bench-test-') as tmp:
   root=Path(tmp);(root/'hypr/test').mkdir(parents=True)
   with socket.socket(socket.AF_UNIX) as display,socket.socket(socket.AF_UNIX) as hypr:
    display.bind(str(root/'wayland-1'));hypr.bind(str(root/'hypr/test/.socket.sock'))
    env=bench.private_environment(tmp,'wayland-1','test')
    self.assertEqual(env['HYPRLAND_INSTANCE_SIGNATURE'],'test')
    with self.assertRaises(ValueError):bench.private_environment(tmp,'wayland-1','../test')
 def test_process_metrics(self):
  self.assertGreaterEqual(bench.cpu_seconds(os.getpid()),0)
  self.assertGreater(bench.memory(os.getpid()).get('pssMiB',0),0)
if __name__=='__main__':unittest.main()
