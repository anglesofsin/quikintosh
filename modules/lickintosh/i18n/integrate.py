"""Build Portuguese catalogs and localize presentation without changing IDs."""
import ast
import json
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
translations = {}
for line in (Path(__file__).parent / 'pt-BR.txt').read_text().splitlines():
    if line and not line.startswith('#'):
        english, portuguese = line.split('|', 1)
        translations[english] = portuguese
english = json.loads((root / 'assets/i18n/en.json').read_text())
portuguese = {key: translations.get(value, value) for key, value in english.items()}
portuguese.update(translations)
for key, value in english.items():
    portuguese.setdefault(value, translations.get(value, value))
(root / 'assets/i18n/pt_BR.json').write_text(json.dumps(portuguese, ensure_ascii=False, indent=1) + '\n')

# Only literals bound to presentation properties; never action names, routes,
# object keys, configuration values or backend commands.
literal = r'''("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')'''
pattern = re.compile(r'(?P<prefix>\b(?:text|title|placeholderText|toolTipText|description)\s*:\s*)' + literal)
qs_tr = re.compile(r'\bqsTr\(\s*' + literal + r'\s*\)')
for path in root.rglob('*.qml'):
    if path.is_symlink() or path.name == 'I18n.qml' or 'rosa' in path.relative_to(root).parts:
        continue
    text = path.read_text()
    original = text
    text = pattern.sub(lambda m: m['prefix'] + 'I18n.tr(' + m[2] + ')', text)
    text = qs_tr.sub(lambda m: 'I18n.tr(' + m[1] + ')', text)
    if text != original:
        if not re.search(r'^import qs\.services\s*$', text, re.M):
            lines = text.splitlines(True)
            indices = [i for i, line in enumerate(lines) if line.startswith('import ')]
            if not indices:
                continue
            lines.insert(max(indices) + 1, 'import qs.services\n')
            text = ''.join(lines)
        path.write_text(text)

p = root / 'settingsapp/SettingsContent.qml'
s = p.read_text().replace('label:label,kind:', 'label:I18n.tr(label),kind:')
s = s.replace('title:title,rows:', 'title:I18n.tr(title),rows:').replace("footer:footer || ''", "footer:I18n.tr(footer || '')")
s = s.replace('choices:choices,selection:', 'choices:choices.map(value=>I18n.tr(value)),selection:')
s = s.replace('buttonText:caption,action:', 'buttonText:I18n.tr(caption),action:')
p.write_text(s)
p = root / 'components/TahoeCombo.qml'
s = p.read_text().replace('text:control.displayText;', 'text:I18n.tr(control.displayText);')
s = s.replace('text:control.textAt(index);', 'text:I18n.tr(control.textAt(index));')
s = s.replace('text:control.textAt(parent.index);', 'text:I18n.tr(control.textAt(parent.index));')
p.write_text(s)
p = root / 'services/SettingsCatalog.qml'
s = p.read_text().replace(' property var pages:[]', ''' property var rawPages:[]
 readonly property var pages:rawPages.map(page=>Object.assign({},page,{title:I18n.tr(page.title)}))''')
s = s.replace('root.pages=JSON.parse(text())', 'root.rawPages=JSON.parse(text())')
s = s.replace(' function search(query)', ''' function fold(value){const text=String(value || '').toLowerCase();return text.normalize ? text.normalize('NFD').replace(/[\\u0300-\\u036f]/g,''):text}
 function search(query)''')
s = s.replace("query.toLowerCase().trim()", "fold(query).trim()")
s = s.replace("(page.title+' '+page.keywords).toLowerCase()", "fold(page.title+' '+page.keywords)")
s = s.replace('b.title.toLowerCase().startsWith(query.toLowerCase())', 'fold(b.title).startsWith(fold(query))').replace('a.title.toLowerCase().startsWith(query.toLowerCase())', 'fold(a.title).startsWith(fold(query))')
p.write_text(s)
catalog = root / 'settingsapp/catalog.json'
pages = json.loads(catalog.read_text())
keywords = {'appearance':'aparência aparencia escala tamanho interface cores ícones icones tema vidro',
            'language':'português portugues brasil idioma língua lingua localidade região regiao',
            'sound':'som áudio audio volume microfone toque notificação notificacao',
            'menubar':'barra menus logotipo maçã maca cantos',
            'desktop':'mesa dock arquivos widgets tamanho grade',
            'accessibility':'acessibilidade contraste movimento transparência transparencia texto'}
for page in pages:
    page['keywords'] = page.get('keywords', '') + ' ' + keywords.get(page['id'], '')
catalog.write_text(json.dumps(pages, ensure_ascii=False, indent=1) + '\n')
for name, replacements in {
    'SettingsRow.qml': [('text:root.label;', 'text:I18n.tr(root.label);'), ('text:root.description;', 'text:I18n.tr(root.description);'), ('text:root.value;', 'text:I18n.tr(root.value);')],
    'SettingsRoot.qml': [('text:SettingsState.error;', 'text:I18n.tr(SettingsState.error);')],
}.items():
    p = root / 'settings.qml' if name == 'SettingsRoot.qml' else root / 'settingsapp' / name
    s = p.read_text()
    for old, new in replacements:
        s = s.replace(old, new)
    p.write_text(s)

# Dynamic Island has its own keyed catalog; follow the shell language while
# retaining upstream Russian/English handling and plural structures.
p = root / 'rosa/services/I18n.qml'
s = p.read_text().replace('import QtQuick', 'import qs.services as Native\nimport QtQuick', 1)
s = s.replace('readonly property string lang: Prefs.language', 'readonly property string lang: Native.I18n.lang === "pt_BR" ? "pt_BR" : Prefs.language')
s = s.replace('return spare !== undefined ? spare : key;', 'return spare !== undefined ? (root.lang === "pt_BR" && typeof spare === "string" ? Native.I18n.tr(spare) : spare) : key;')
p.write_text(s)
print('Portuguese catalog:', len(portuguese), 'keys;', len(translations), 'authored translations')
