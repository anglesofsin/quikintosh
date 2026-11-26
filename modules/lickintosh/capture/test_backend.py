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
 def test_window_targets_use_named_special_workspace_addresses(self):
  import json
  with tempfile.TemporaryDirectory() as private:
   worker=Worker(private)
   special={'address':'special:public','name':'special:public','type':'special'}
   monitor=dict(name='test',width=800,height=600,x=0,y=0,focused=True,activeWorkspace={'id':1},specialWorkspace=special)
   clients=[
    dict(at=[20,20],size=[100,100],workspace={'id':1}),
    dict(at=[50,50],size=[200,200],workspace=special),
    dict(at=[60,60],size=[300,300],workspace={'address':'special:right','type':'special'}),
   ]
   replies={'monitors':[monitor],'cursorpos':{'x':100,'y':100},'clients':clients}
   def read(command):return json.dumps(replies[command[1]])
   def capture(command,**kwargs):Image.new('RGB',(800,600),'blue').save(command[-1])
   with patch.dict('os.environ',{'QT_SCALE_FACTOR':'1'}),patch('backend.output',side_effect=read),patch('backend.run',side_effect=capture),patch('backend.emit'):
    worker.capture(dict(mode='region',config={}))
   self.assertEqual(worker.meta['windows'],[dict(x=50,y=50,w=200,h=200),dict(x=20,y=20,w=100,h=100)])
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
 def test_raw_export_crops_exact_pixels_and_preserves_png(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);worker=Worker(root);worker.session='fast';worker.frame=Image.new('RGB',(120,80),'blue');worker.frame.putpixel((20,10),(255,0,0));source=root/'frame.png';worker.frame.save(source);worker.meta={'factor':2,'path':str(source)}
   with patch('backend.copy_png'),patch('backend.emit') as emit:
    worker.command(dict(action='finishRaw',kind='save',box=[10,5,30,20],width=30,height=20,config={'directory':str(root/'saved')}))
   with Image.open(emit.call_args.kwargs['saved']) as result:
    self.assertEqual(result.size,(60,40));self.assertEqual(result.getpixel((0,0)),(255,0,0))
 def test_full_frame_export_reuses_source_and_validates_bounds(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);worker=Worker(root);worker.session='fast';worker.frame=Image.new('RGB',(120,80),'blue');source=root/'frame.png';worker.frame.save(source);worker.meta={'factor':1,'path':str(source)}
   with patch('backend.copy_png') as copy,patch('backend.emit'):
    worker.command(dict(action='finishRaw',kind='copy',box=[0,0,120,80],config={}))
    self.assertEqual(Path(copy.call_args.args[0]),source)
   for box in [[0,0,-1,2],[0,0,float('nan'),2],[130,0,20,20]]:
    with self.assertRaises(ValueError):worker.command(dict(action='finishRaw',box=box))
 def test_fullscreen_reuses_grim_png_without_enumerating_windows(self):
  import json
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);worker=Worker(root)
   def read(command):
    if command[1]=='monitors':return json.dumps([dict(name='test',width=800,height=600,scale=1,x=0,y=0,focused=True)])
    if command[1]=='cursorpos':return json.dumps(dict(x=20,y=20))
    raise AssertionError('Full-display capture should not enumerate clients')
   def capture(command,**kwargs):Image.new('RGB',(800,600),'blue').save(command[-1])
   with patch('backend.output',side_effect=read),patch('backend.run',side_effect=capture),patch('backend.copy_png') as copy,patch('backend.emit') as emit:
    worker.capture(dict(mode='fullscreen',config={'directory':str(root/'saved'),'autoSave':True}))
   self.assertIsNone(worker.frame)
   self.assertEqual(emit.call_args.kwargs['action'],'fullscreen')
   self.assertEqual(Path(emit.call_args.kwargs['saved']).read_bytes(),Path(copy.call_args.args[0]).read_bytes())
 def test_annotated_bmp_is_encoded_as_lossless_png_in_worker(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);worker=Worker(root);worker.session='annotated'
   bitmap=root/'export.bmp';image=Image.new('RGB',(60,40),'blue');image.putpixel((20,10),(255,0,0));image.save(bitmap)
   with patch('backend.copy_png') as copy,patch('backend.emit') as emit:
    worker.command(dict(action='finish',kind='save',path=str(bitmap),config={'directory':str(root/'saved')}))
   self.assertFalse(bitmap.exists())
   self.assertEqual(Path(copy.call_args.args[0]).suffix,'.png')
   with Image.open(emit.call_args.kwargs['saved']) as result:
    self.assertEqual(result.format,'PNG');self.assertEqual(result.size,(60,40));self.assertEqual(result.getpixel((20,10)),(255,0,0))
if __name__=='__main__':unittest.main()
