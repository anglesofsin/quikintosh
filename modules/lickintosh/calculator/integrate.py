from pathlib import Path
import sys,shutil,json
root=Path(sys.argv[1]);source=Path(__file__).parent
out=root/'calculator';out.mkdir(exist_ok=True)
for name in ['engine.py','rates.py','mode.svg','SOURCES.md']:shutil.copyfile(source/name,out/name)
p=root/'components/CalculatorApp.qml';p.write_text((source/'CalculatorApp.qml').read_text().replace('@PYTHON@',sys.argv[2]))
p=root/'components/qmldir';p.write_text(p.read_text()+'\nCalculatorApp CalculatorApp.qml\n')
(root/'calculator.qml').write_text('''//@ pragma AppId org.quickintosh.Calculator
import QtQuick
import Quickshell
import qs.components
ShellRoot {
 CalculatorApp {
  id:calculator
  Component.onCompleted:{calculator.open();const action=Quickshell.env('QUICKINTOSH_CALCULATOR_ACTION');if(action)calculator.execute(action)}
 }
}
''')
p=root/'ui/topbar/statusarea/controlcenter/ControlCenter.qml';s=p.read_text();a=s.index('    function openCalculator() {');b=s.index('    Process { id: _shOn;',a)
s=s[:a]+'''    function openCalculator() {
        root.closeRequested()
        Quickshell.execDetached(['quickintosh-calculator'])
    }
'''+s[b:];p.write_text(s)
p=root/'assets/i18n/pt_BR.json';data=json.loads(p.read_text());data.update({'Basic':'Básica','Scientific':'Científica','Programmer':'Programador','Convert':'Converter','RPN Mode':'Modo RPN','Show History':'Mostrar histórico','Math Notes':'Notas Matemáticas','Copy Result':'Copiar resultado','No calculations yet':'Nenhum cálculo ainda','Today':'Hoje','Previous 7 Days':'Últimos 7 dias','Previous 30 Days':'Últimos 30 dias','Copy Expression':'Copiar expressão','History':'Histórico','Clear history':'Limpar histórico','Clear history?':'Limpar o histórico?','Write expressions or define variables, one per line.':'Escreva expressões ou defina variáveis, uma por linha.','Error':'Erro','Calculator unavailable':'Calculadora indisponível','Rates unavailable':'Cotações indisponíveis'});p.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n')
# Expose the app's real commands through the shared menu bar and dock identity.
p=root/'ui/dock/Dock.qml';s=p.read_text();needle='    function resolveAppId(c) {';assert needle in s;s=s.replace(needle,needle+'\n        if((c.title || c.initialTitle)==="Quickintosh Calculator")return "org.quickintosh.Calculator"',1);p.write_text(s)
base=root/'ui/topbar/menubar/globalmenu'
p=base/'data/CalculatorMenus.qml';p.write_text('''pragma Singleton
import QtQuick
import qs.services
QtObject {
 function item(label,action){return {label:I18n.tr(label),command:['quickintosh-calculator',action]}}
 readonly property var menus:[
  {label:I18n.tr('Edit'),items:[item('Copy Result','copy'),item('Paste','paste'),{separator:true},item('Clear','clear')]},
  {label:I18n.tr('View'),items:[item('Basic','basic'),item('Scientific','scientific'),item('Programmer','programmer'),{separator:true},item('Convert','convert'),item('RPN Mode','rpn'),item('Show History','history'),item('Math Notes','notes')]},
  {label:I18n.tr('Window'),items:[item('Minimize','minimize'),item('Close Window','close')]},
  {label:I18n.tr('Help'),items:[{label:I18n.tr('Calculator User Guide'),command:['xdg-open','https://support.apple.com/en-ge/guide/calculator/welcome/12.0/mac/26']}]}
 ]
}
''')
p=base/'data/qmldir';p.write_text(p.read_text()+'\nsingleton CalculatorMenus CalculatorMenus.qml\n')
p=base/'GlobalMenuService.qml';s=p.read_text().replace('readonly property string category: root.desktopMode ? "filemanager":root.classify(root.appId)', 'readonly property string category:root.desktopMode ? "filemanager":root.currentWayland?.title==="Quickintosh Calculator" ? "calculator":root.classify(root.appId)',1).replace('case "browser": return Browser.menus','case "calculator": return CalculatorMenus.menus\n        case "browser": return Browser.menus',1);p.write_text(s)
p=root/'ui/topbar/menubar/activewindows/ActiveWindow.qml';s=p.read_text().replace('property string appName:GlobalMenuService.desktopMode ? "Finder":formatName(currentAppId, currentTitle)', 'property string appName:GlobalMenuService.desktopMode ? "Finder":currentTitle==="Quickintosh Calculator" ? I18n.tr("Calculator"):formatName(currentAppId, currentTitle)',1);p.write_text(s)
