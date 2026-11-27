import importlib.util,tempfile,unittest,time
from pathlib import Path
spec=importlib.util.spec_from_file_location('calculator',Path(__file__).resolve().parents[1]/'modules/lickintosh/calculator/engine.py');calc=importlib.util.module_from_spec(spec);spec.loader.exec_module(calc)
class Calculator(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.e=calc.Engine(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def keys(self,keys):
  for key in keys:r=self.e.dispatch({'key':key});self.assertFalse(r['error'],r)
  return r['rawValue']
 def test_decimal_precedence_and_percent(self):
  self.assertEqual(calc.number(calc.Evaluator().run('0.1+0.2')),'0.3')
  for expression,value in [('239.5*0.4','95.8'),('(2*4)+10','18'),('200+10%','220'),('200-10%','180'),('200*10%','20'),('2+3*4','14'),('sqrt(81)','9')]:self.assertEqual(calc.number(calc.Evaluator().run(expression)),value)
 def test_repeat_clear_backspace_sign_memory(self):
  self.assertEqual(self.keys('2+3=='),'8');self.keys(['AC']);self.assertEqual(self.keys(['2','+','3','±','=']),'-1')
  self.keys(['AC','4','m+','AC','mr']);self.assertEqual(self.e.value,'4')
  self.keys(['AC','1','2','⌫','=']);self.assertEqual(self.e.value,'1')
 def test_undo_bits_and_delete(self):
  self.keys('12');self.e.dispatch({'action':'undo'});self.assertEqual(self.e.value,'1')
  self.e.dispatch({'action':'redo'});self.assertEqual(self.e.value,'12')
  self.keys(['AC']);self.e.dispatch({'action':'toggleBit','bit':63});self.assertEqual(self.e.value,'9223372036854775808')
  self.keys(['AC','5','=']);stamp=self.e.history[0]['time'];self.e.dispatch({'action':'deleteHistory','time':stamp});self.assertEqual(self.e.history,[])
 def test_scientific(self):
  self.assertAlmostEqual(float(calc.Evaluator().run('sin(30)')),.5)
  self.assertAlmostEqual(float(calc.Evaluator(False).run('cos(pi)')),-1)
  self.assertEqual(calc.Evaluator().run('factorial(10)'),3628800)
  self.assertEqual(calc.Evaluator().run('cbrt(-8)'),-2)
  self.assertEqual(calc.Evaluator().run('log2(1024)'),10)
 def test_programmer_precision_and_word(self):
  self.e.dispatch({'action':'mode','mode':'programmer'});self.e.dispatch({'action':'base','base':16})
  self.keys(['F','F']);self.assertEqual(self.e.value,'255')
  self.keys(['&','A','=']);self.assertEqual(self.e.value,'10')
  self.keys(['AC','C']);self.assertEqual(self.e.value,'12')
  self.assertEqual(calc.Evaluator(bits=8).run('~0'),255)
  self.assertEqual(calc.Evaluator().run('0xffffffffffffffff'),18446744073709551615)
  self.assertEqual(calc.Evaluator().run('7⊕3'),4)
 def test_rpn(self):
  self.e.dispatch({'action':'rpn'});self.keys(['2','=','3','+']);self.assertEqual(self.e.value,'5');self.assertEqual(self.e.stack,['5'])
  self.keys(['4','=']);self.e.dispatch({'action':'stack','key':'swap'});self.assertEqual(self.e.stack,['4','5'])
 def test_conversions(self):
  self.assertEqual(calc.convert(1,'Length','mi','m'),calc.D('1609.344'))
  self.assertEqual(calc.convert(32,'Temperature','°F','°C'),0)
  self.assertEqual(calc.convert(0,'Temperature','°C','K'),calc.D('273.15'))
  self.assertEqual(calc.convert(1,'Data','GiB','MiB'),1024)
  self.assertEqual(calc.convert(5,'Fuel economy','L/100km','km/L'),20)
 def test_notes_history_restore(self):
  self.keys('2+3=');other=calc.Engine(self.tmp.name);self.assertEqual(other.history[0]['result'],'5')
  r=self.e.dispatch({'action':'notes','text':'x = 7\nx + 20\nhello\n(2+3)*4'});self.assertEqual(r['noteResults'],['7','27','','20'])
  self.e.dispatch({'action':'clearHistory'});self.assertEqual(calc.Engine(self.tmp.name).history,[])
 def test_reject_unsafe_and_costly_expressions(self):
  for expression in ["__import__('os')",'(1).__class__','[1]*999','2**999999','factorial(999999)','a.b','1/0','sqrt(-1)']:
   with self.assertRaises((ValueError,ArithmeticError)):calc.Evaluator().run(expression)
 def test_invalid_saved_state(self):
  self.e.path.parent.mkdir(parents=True,exist_ok=True)
  for value in ['[]','{"history":4,"notes":null}','{"history":[{}]}']:
   self.e.path.write_text(value);self.assertEqual(calc.Engine(self.tmp.name).history,[])
 def test_worker_latency(self):
  start=time.perf_counter()
  for _ in range(1000):calc.Evaluator().run('(239.5*0.4)+sqrt(81)')
  elapsed=time.perf_counter()-start;print('CALCULATOR_1000_EXPRESSIONS_SECONDS',round(elapsed,4));self.assertLess(elapsed,2)
if __name__=='__main__':unittest.main()
