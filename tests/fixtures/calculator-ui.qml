import QtQuick
import Quickshell
import Quickshell.Io
import qs.components
ShellRoot {
 CalculatorApp{id:calc}
 IpcHandler{target:'calculatorTest'
  function status():string{return JSON.stringify({ready:calc.ready,value:calc.state.rawValue,error:calc.state.error,visible:calc.testWindow.visible,width:calc.testWindow.width,height:calc.testWindow.height,history:calc.history.length})}
  function begin():void{calc.open()}
  function closeCalc():void{calc.opened=false}
  function keys(text:string):void{for(let c of text)calc.key(c)}
  function page(n:int):void{calc.historyShown=false;calc.converting=false;calc.key('AC');calc.changeMode(n===2 ? 'scientific':n===3 ? 'programmer':n===4 ? 'notes':'basic');if(n===1)calc.historyShown=true;if(n===5)calc.converting=true}
 }
}
