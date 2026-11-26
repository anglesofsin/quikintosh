from pathlib import Path
import shutil,sys
root=Path(sys.argv[1]);here=Path(__file__).parent
shutil.copyfile(here/'cursor_settings.py',root/'settingsapp/cursor_settings.py')
p=root/'settingsapp/backend.py';s=p.read_text();at=s.index('def runtime(values=None, restore=False):');s=s[:at]+s[at:].replace('        values = values or {}',"        import cursor_settings\n        cursor_settings.apply(values or {})\n        values = {k:v for k,v in (values or {}).items() if not k.startswith('qi-cursor:')}",1);p.write_text(s)
p=root/'settingsapp/SettingsContent.qml';s=p.read_text();needle="   }else if(pageId==='mouse'){";replacement=needle+'''
    const cursor=SettingsPreferences.inputOverrides
    const cv=(key,fallback)=>cursor['qi-cursor:'+key] ?? fallback
    result.push(card('Pointer',[
     row('Pointer Size','slider',{action:'input',key:'qi-cursor:size',number:cv('size',31),minimum:16,maximum:96,step:1,value:String(cv('size',31))}),
     choice('Cursor Theme',['MacTahoe','MacTahoe Dark','Bibata'],['MacTahoe-cursors','MacTahoe-dark-cursors','Bibata-Modern-Classic'].indexOf(cv('theme','MacTahoe-cursors')),'cursor-theme'),
     choice('Pointer Color',['Original','White','Blue','Pink','Green','Yellow','Red','Custom'],['original','#ffffff','#007aff','#ff2d82','#34c759','#ffcc00','#ff3b30'].indexOf(cv('color','original'))<0 ? 7:['original','#ffffff','#007aff','#ff2d82','#34c759','#ffcc00','#ff3b30'].indexOf(cv('color','original')),'cursor-color'),
     ...(cv('color','original')==='original' ? []:[row('Custom Color','field',{action:'input',key:'qi-cursor:color',value:cv('color','#007aff')})])
    ]))
    result.push(card('Locate Pointer',[
     toggle('Shake Mouse Pointer to Locate',cv('shake',true),'input',{key:'qi-cursor:shake'}),
     row('Maximum Enlargement','slider',{action:'input',key:'qi-cursor:scale',number:cv('scale',4),minimum:1.5,maximum:8,step:.1,value:Number(cv('scale',4)).toFixed(1)+'×'}),
     row('Growth Speed','slider',{action:'input',key:'qi-cursor:speed',number:cv('speed',1.7),minimum:.3,maximum:5,step:.1,value:Number(cv('speed',1.7)).toFixed(1)}),
     row('Hold Duration','slider',{action:'input',key:'qi-cursor:timeout',number:cv('timeout',900),minimum:200,maximum:3000,step:50,value:cv('timeout',900)+' ms'}),
     row('Shake Sensitivity','slider',{action:'input',key:'qi-cursor:sensitivity',number:cv('sensitivity',1),minimum:.5,maximum:2,step:.1,value:Number(cv('sensitivity',1)).toFixed(1)})
    ]))
''';assert needle in s;s=s.replace(needle,replacement,1)
s=s.replace("  if(name==='input'){", "  if(name==='cursor-theme'){SettingsPreferences.input('qi-cursor:theme',['MacTahoe-cursors','MacTahoe-dark-cursors','Bibata-Modern-Classic'][value]);return}\n  if(name==='cursor-color'){SettingsPreferences.input('qi-cursor:color',['original','#ffffff','#007aff','#ff2d82','#34c759','#ffcc00','#ff3b30','#9b59b6'][value]);return}\n  if(name==='input'){",1);p.write_text(s)

p=root/'assets/i18n/pt_BR.json'
import json
data=json.loads(p.read_text());data.update({'Pointer':'Ponteiro','Pointer Size':'Tamanho do ponteiro','Cursor Theme':'Tema do cursor','Pointer Color':'Cor do ponteiro','Locate Pointer':'Localizar ponteiro','Shake Mouse Pointer to Locate':'Aumentar o ponteiro ao balançar o mouse','Maximum Enlargement':'Ampliação máxima','Growth Speed':'Velocidade de crescimento','Hold Duration':'Tempo de permanência','Shake Sensitivity':'Sensibilidade do movimento','Custom Color':'Cor personalizada','Original':'Original'})
p.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n')
