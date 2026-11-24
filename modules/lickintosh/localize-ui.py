"""Route existing French UI literals through the shell's selected catalog."""
import ast
import json
from pathlib import Path
import re
import sys
root=Path(sys.argv[1]); additions=json.loads(Path(sys.argv[2]).read_text())
files={lang:root/'assets/i18n'/f'{lang}.json' for lang in ['fr','en','es']}
catalogs={lang:json.loads(path.read_text()) for lang,path in files.items()}
for key,value in additions.items():
    catalogs['en'][key]=value
    for lang in ['fr','es']: catalogs[lang].setdefault(key,key)
translate={k:v for k,v in catalogs['en'].items() if k!=v and k!='Français'}
tokens=re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\x27(?:\\.|[^\x27\\])*\x27')
count=0
for path in root.rglob('*.qml'):
    if path.is_symlink() or path.name=='I18n.qml' or 'rosa' in path.relative_to(root).parts: continue
    source=path.read_text(); changed=[0]
    def replace(match):
        token=match.group()
        if token.startswith(('/', '/*')): return token
        try: text=json.loads(token) if token.startswith('"') else ast.literal_eval(token)
        except (ValueError,SyntaxError): return token
        if text not in translate: return token
        before=source[:match.start()].rstrip()
        if re.search(r'I18n\.tr\s*\(\s*$',source[max(0,match.start()-64):match.start()]): return token
        if before.endswith(('{',',')) and source[match.end():].lstrip().startswith(':'): return token
        changed[0]+=1
        return 'I18n.tr('+token+')'
    result=tokens.sub(replace,source)
    if changed[0]:
        if not re.search(r'^import qs\.services\s*$',result,re.M):
            lines=result.splitlines(True);indices=[i for i,line in enumerate(lines) if line.startswith('import ')]
            lines.insert(max(indices)+1,'import qs.services\n');result=''.join(lines)
        path.write_text(result);count+=changed[0]
for lang,path in files.items(): path.write_text(json.dumps(catalogs[lang],ensure_ascii=False,indent=1)+'\n')
print(f'Localized {count} existing UI literals; added {len(additions)} English translations.')
