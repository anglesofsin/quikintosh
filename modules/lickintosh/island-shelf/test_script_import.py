import tempfile,unittest,zipfile
from pathlib import Path
from script_import import read_script
class ScriptImportTests(unittest.TestCase):
 def test_text_and_docx(self):
  with tempfile.TemporaryDirectory() as directory:
   text=Path(directory)/'script.txt';text.write_text('Olá, mundo',encoding='utf-8');self.assertEqual(read_script(text),'Olá, mundo')
   doc=Path(directory)/'script.docx'
   with zipfile.ZipFile(doc,'w') as archive:archive.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:t>Hello</w:t></w:r></w:p><w:p><w:r><w:t>world</w:t></w:r></w:p></w:document>')
   self.assertEqual(read_script(doc),'Hello\nworld')
 def test_empty_unsupported_and_large(self):
  with tempfile.TemporaryDirectory() as directory:
   for name,value in [('empty.txt',''),('code.py','print(1)'),('large.txt','a'*100001)]:
    path=Path(directory)/name;path.write_text(value)
    with self.assertRaises(ValueError):read_script(path)
 def test_entity_document_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'script.docx'
   with zipfile.ZipFile(path,'w') as archive:archive.writestr('word/document.xml','<!DOCTYPE document [<!ENTITY x "no">]><document/>')
   with self.assertRaises(ValueError):read_script(path)
if __name__=='__main__':unittest.main()
