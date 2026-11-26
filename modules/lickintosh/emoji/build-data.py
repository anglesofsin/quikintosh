"""Build the searchable Unicode/CLDR catalog; no network is used at runtime."""
import json,re,sys,unicodedata,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(sys.argv[1]);annotations={}
for file in [root/'pt.xml',root/'pt-derived.xml']:
 for node in ET.parse(file).iter('annotation'):
  key=node.attrib.get('cp','');entry=annotations.setdefault(key,{'pt':'','words':[]})
  if node.attrib.get('type')=='tts':entry['pt']=node.text or ''
  else:entry['words'].append(node.text or '')
def norm(s):return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if not unicodedata.combining(c))
def bare(s):return ''.join(c for c in s if ord(c) not in range(0x1f3fb,0x1f400) and c!='\ufe0f')
items={};variations=[];group='';order=[]
for line in (root/'emoji-test.txt').read_text().splitlines():
 if line.startswith('# group: '):
  group=line.split(': ',1)[1]
  if group!='Component':order.append(group)
 m=re.match(r'^([0-9A-F ]+)\s*; fully-qualified\s*#\s*(\S+)\s+E[\d.]+\s+(.+)$',line)
 if not m or group=='Component':continue
 emoji=m[2];name=m[3];base=bare(emoji)
 if any(0x1f3fb<=ord(c)<=0x1f3ff for c in emoji):variations.append((base,emoji));continue
 pt=annotations.get(emoji,annotations.get(base,{}));label=pt.get('pt') or name
 items[base]={'emoji':emoji,'name':name,'pt':label,'group':order.index(group), 'search':norm(' '.join([name,label,*pt.get('words',[])])),'tones':{}}
for base,emoji in variations:
 tones={ord(c)-0x1f3fa for c in emoji if 0x1f3fb<=ord(c)<=0x1f3ff}
 if base in items and len(tones)==1:items[base]['tones'][str(tones.pop())]=emoji
out=Path(sys.argv[2]);out.write_text(json.dumps({'groups':order,'items':list(items.values())},ensure_ascii=False,separators=(',',':'))+'\n')
print(len(items),'base emojis;',len(variations),'skin variants')
