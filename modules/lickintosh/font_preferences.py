"""Set font-only JSONC preferences without rewriting unrelated editor settings."""
import json,re
from pathlib import Path

def set_jsonc(text,key,value):
 pattern=re.compile(r'("'+re.escape(key)+r'"\s*:\s*)"(?:\\.|[^"\\])*"')
 encoded=json.dumps(value)
 if pattern.search(text):return pattern.sub(lambda m:m[1]+encoded,text,count=1)
 # Locate the root object while skipping comments and quoted strings.
 token=re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\{')
 for match in token.finditer(text):
  if match[0]=='{':
   rest=text[match.end():];clean=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/','',rest).lstrip()
   return text[:match.end()]+'\n  '+json.dumps(key)+': '+encoded+(',' if not clean.startswith('}') else '')+'\n'+rest
 raise ValueError('Editor settings do not contain a JSON object')

def apply(home,write):
 config=Path(home)/'.config'
 for app in ['Code','Code - Insiders','VSCodium','Cursor','Antigravity']:
  path=config/app/'User/settings.json'
  if path.is_file():
   text=path.read_text()
   for key,value in [('editor.fontFamily','SF Mono'),('terminal.integrated.fontFamily','SF Mono')]:text=set_jsonc(text,key,value)
   write(path,text.encode())
 path=config/'zed/settings.json'
 if path.is_file():
  text=path.read_text()
  for key,value in [('ui_font_family','SF Pro Text'),('buffer_font_family','SF Mono')]:text=set_jsonc(text,key,value)
  write(path,text.encode())
