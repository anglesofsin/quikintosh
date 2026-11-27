"""Local bounded teleprompter script import. No macros or embedded code execute."""
import json,sys,zipfile
from pathlib import Path
from xml.etree import ElementTree

def read_script(value):
 path=Path(value).expanduser()
 if not path.is_file() or path.stat().st_size>20*1024*1024:raise ValueError('Choose a document smaller than 20 MiB')
 suffix=path.suffix.lower()
 if suffix=='.pdf':
  import fitz
  with fitz.open(path) as document:
   if document.needs_pass:raise ValueError('Unlock the PDF before importing it')
   text='\n'.join(document.load_page(i).get_text() for i in range(min(len(document),200)))
 elif suffix=='.docx':
  with zipfile.ZipFile(path) as archive:
   info=archive.getinfo('word/document.xml')
   if info.file_size>4*1024*1024:raise ValueError('Document text is too large')
   data=archive.read(info)
   if b'<!DOCTYPE' in data or b'<!ENTITY' in data:raise ValueError('Unsupported document XML')
   root=ElementTree.fromstring(data);ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
   text='\n'.join(''.join(p.itertext()) for p in root.findall('.//w:p',ns))
 elif suffix in ('.txt','.md'):text=path.read_text(encoding='utf-8-sig')
 else:raise ValueError('Choose TXT, Markdown, PDF or DOCX')
 text=text.strip()
 if not text:raise ValueError('No readable text found; scanned PDFs need OCR first')
 if len(text)>100000:raise ValueError('Script is limited to 100,000 characters')
 return text

if __name__=='__main__':
 try:print(json.dumps({'text':read_script(sys.argv[1])}))
 except Exception as error:print(json.dumps({'error':str(error)}));sys.exit(1)
