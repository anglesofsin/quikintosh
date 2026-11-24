import tempfile,unittest
from unittest.mock import patch
from pathlib import Path
from PIL import Image
from backend import save_png,filename,Worker
class CaptureTests(unittest.TestCase):
 def test_shell_scale_keeps_pixels_window_rectangles_and_cursor_aligned(self):
  import json
  with tempfile.TemporaryDirectory() as private:
   worker=Worker(private)
   def read(command):
    if command[1]=='monitors':return json.dumps([dict(name='test',width=1920,height=1080,scale=1,x=100,y=50,focused=True,activeWorkspace={'id':1},specialWorkspace={'id':0})])
    if command[1]=='cursorpos':return json.dumps(dict(x=400,y=350))
    return json.dumps([dict(at=[250,200],size=[600,450],workspace={'id':1},mapped=True,hidden=False)])
   def capture(command,**kwargs):Image.new('RGB',(1920,1080),'blue').save(command[-1])
   with patch.dict('os.environ',{'QT_SCALE_FACTOR':'1.5'}),patch('backend.output',side_effect=read),patch('backend.run',side_effect=capture),patch('backend.emit'):
    worker.capture(dict(mode='region',config={}))
   self.assertEqual(worker.frame.size,(1920,1080))
   self.assertEqual((worker.meta['width'],worker.meta['height']),(1280,720))
   self.assertEqual(worker.meta['factor'],1.5)
   self.assertEqual((worker.meta['cursorX'],worker.meta['cursorY']),(200,200))
   self.assertEqual(worker.meta['windows'],[dict(x=100,y=100,w=400,h=300)])
 def test_save_does_not_overwrite_and_templates_are_safe(self):
  with tempfile.TemporaryDirectory() as directory:
   src=Path(directory)/'source.png';Image.new('RGB',(31,19),'red').save(src)
   config=dict(directory=directory,filenameTemplate='../test_{w}_{h}.png')
   a=save_png(src,config,'region');b=save_png(src,config,'region')
   self.assertNotEqual(a,b);self.assertEqual(Path(a).parent,Path(directory));
   with Image.open(a) as image:self.assertEqual(image.size,(31,19))
   with Image.open(b) as image:self.assertEqual(image.getpixel((0,0)),(255,0,0))
 def test_markup_prepares_private_copy_and_preserves_original(self):
  import json,hashlib
  with tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as private:
   source=Path(directory)/'Original.png';Image.new('RGB',(640,420),'#4089c0').save(source);before=source.read_bytes();worker=Worker(private)
   monitors=json.dumps([dict(name='test',width=1920,height=1080,scale=1,focused=True)])
   with patch('backend.output',return_value=monitors),patch('backend.emit') as emit:worker.command(dict(action='editImage',path=source.as_uri()))
   self.assertEqual(source.read_bytes(),before);self.assertEqual(worker.frame.size,(1920,1080));self.assertEqual(worker.meta['editSelection']['w'],640)
   self.assertTrue(Path(worker.meta['path']).is_relative_to(private));self.assertEqual(worker.meta['filename'],'Original annotated.png');self.assertEqual(emit.call_args.args[0],'prepared')
 def test_worker_rejects_files_outside_its_private_directory(self):
  with tempfile.TemporaryDirectory() as directory:
   w=Worker(directory)
   with self.assertRaises(ValueError):w.owned('/etc/passwd')
 def test_prune_preserves_pinned_images(self):
  with tempfile.TemporaryDirectory() as directory:
   w=Worker(directory);pin=Path(directory)/'pin.png';temp=Path(directory)/'temp.png';pin.write_bytes(b'pinned');temp.write_bytes(b'temporary');w.pins.add(str(pin));w.prune();self.assertTrue(pin.exists());self.assertFalse(temp.exists())
 def test_ocr_copies_and_completes_without_a_result_window(self):
  with tempfile.TemporaryDirectory() as directory:
   source=Path(directory)/'text.png';Image.new('RGB',(80,40),'white').save(source)
   worker=Worker(directory)
   with patch('backend.output',return_value='Recognized example text'),patch('backend.copy_data') as copy,patch('backend.emit') as emit:
    worker.command(dict(action='finish',kind='ocr',path=str(source),config={}))
    copy.assert_called_once_with(text='Recognized example text')
    emit.assert_called_once_with('complete',action='ocr',saved='')
 def test_screenshot_has_one_completion_and_no_duplicate_notification(self):
  with tempfile.TemporaryDirectory() as directory:
   source=Path(directory)/'source.png';Image.new('RGB',(80,40),'blue').save(source)
   worker=Worker(directory)
   with patch('backend.copy_png'),patch('backend.notify') as notify,patch('backend.emit') as emit:
    worker.command(dict(action='finish',kind='copy',path=str(source),config={'autoSave':True,'directory':str(Path(directory)/'Desktop')}))
    notify.assert_not_called();self.assertEqual(emit.call_count,1)
    self.assertEqual(emit.call_args.args,('complete',));self.assertTrue(Path(emit.call_args.kwargs['saved']).is_file())
if __name__=='__main__':unittest.main()
