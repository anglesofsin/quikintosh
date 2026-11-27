"""Calculator worker: bounded AST arithmetic; no eval, GUI I/O or shell execution."""
import ast,decimal,json,math,operator,os,re,sys,tempfile,time,secrets
from pathlib import Path
D=decimal.Decimal
decimal.getcontext().prec=34
class MathError(ValueError):pass
class Evaluator:
 def __init__(self,degrees=True,bits=64,variables=None):self.degrees=degrees;self.bits=bits;self.variables=variables or {};self.nodes=0
 def run(self,text):
  if len(text)>4096:raise MathError('Expression too long')
  text=text.replace('×','*').replace('÷','/').replace('−','-').replace('π','pi').replace('^','**').replace('⊕','@')
  text=re.sub(r'(?<![A-Za-z0-9_])(\d+(?:\.\d+)?)\s*(?=\()',r'\1*',text)
  text=re.sub(r'\)\s*(?=\()',')*',text)
  text=re.sub(r'(\d+(?:\.\d+)?|\([^()]*\))%',r'percent(\1)',text)
  text=re.sub(r'(\d+(?:\.\d+)?|\([^()]*\))!',r'factorial(\1)',text)
  self.text=text
  try:return self.visit(ast.parse(text,mode='eval').body)
  except (ArithmeticError,OverflowError,TypeError,SyntaxError) as e:raise MathError('Invalid calculation') from e
 def visit(self,n):
  self.nodes+=1
  if self.nodes>256:raise MathError('Expression too complex')
  if isinstance(n,ast.Constant) and type(n.value) in (int,float):return D(ast.get_source_segment(self.text,n).replace('_','')) if not isinstance(n.value,int) or not ast.get_source_segment(self.text,n).lower().startswith(('0x','0o','0b')) else D(n.value)
  if isinstance(n,ast.Name):
   if n.id in self.variables:return D(str(self.variables[n.id]))
   if n.id in ('pi','e','tau'):return D(str(getattr(math,n.id)))
   raise MathError('Unknown variable: '+n.id)
  if isinstance(n,ast.UnaryOp):
   x=self.visit(n.operand)
   if isinstance(n.op,ast.USub):return -x
   if isinstance(n.op,ast.UAdd):return x
   if isinstance(n.op,ast.Invert):return D((~int(x))&((1<<self.bits)-1))
  if isinstance(n,ast.BinOp):
   a,b=self.visit(n.left),self.visit(n.right)
   if isinstance(n.op,(ast.Add,ast.Sub)) and isinstance(n.right,ast.Call) and isinstance(n.right.func,ast.Name) and n.right.func.id=='percent':b=a*b
   if isinstance(n.op,ast.Pow):
    if abs(b)>10000 or abs(a.adjusted())*abs(b)>10000:raise MathError('Exponent too large')
    return a**b
   operations={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Mod:operator.mod,ast.FloorDiv:operator.floordiv}
   if type(n.op) in operations:return operations[type(n.op)](a,b)
   if isinstance(n.op,(ast.LShift,ast.RShift)):
    if not 0<=b<=self.bits:raise MathError('Shift exceeds word size')
    return D((int(a)<<int(b) if isinstance(n.op,ast.LShift) else int(a)>>int(b))&((1<<self.bits)-1))
   bitops={ast.BitAnd:operator.and_,ast.BitOr:operator.or_,ast.BitXor:operator.xor,ast.MatMult:operator.xor}
   if type(n.op) in bitops:return D(bitops[type(n.op)](int(a),int(b))&((1<<self.bits)-1))
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and not n.keywords:
   name=n.func.id;args=[self.visit(a) for a in n.args]
   if len(args)!=1:raise MathError('One argument required')
   x=args[0]
   if name=='percent':return x/100
   if name=='sqrt':return x.sqrt()
   if name=='abs':return abs(x)
   if name=='factorial':
    if x!=int(x) or not 0<=x<=1000:raise MathError('Factorial requires integer 0–1000')
    return D(math.factorial(int(x)))
   if name in ('sin','cos','tan','sinh','cosh','tanh','asin','acos','atan','asinh','acosh','atanh','log','log10','log2','exp','cbrt'):
    y=float(x)
    if name in ('sin','cos','tan') and self.degrees:y=math.radians(y)
    y=getattr(math,name)(y)
    if name in ('asin','acos','atan') and self.degrees:y=math.degrees(y)
    if not math.isfinite(y):raise MathError('Result not finite')
    if abs(y)<1e-15:y=0
    return D(str(y))
  raise MathError('Unsupported expression')
def number(x):
 if not x.is_finite():raise MathError('Result not finite')
 if not x:return '0'
 if x.adjusted()>18 or x.adjusted()<-9:return format(x,'.14E').replace('E+','e+').replace('E-','e-')
 return format(x,'f').rstrip('0').rstrip('.') if '.' in format(x,'f') else format(x,'f')
# Values are base-unit factors. Temperature and fuel economy are affine/reciprocal.
UNITS={
 'Length':{'m':1,'km':1000,'cm':.01,'mm':.001,'µm':1e-6,'in':.0254,'ft':.3048,'yd':.9144,'mi':1609.344,'nmi':1852},
 'Mass':{'kg':1,'g':.001,'mg':1e-6,'t':1000,'lb':.45359237,'oz':.028349523125},
 'Area':{'m²':1,'km²':1e6,'cm²':.0001,'ha':10000,'acre':4046.8564224,'ft²':.09290304,'mi²':2589988.110336},
 'Volume':{'L':1,'mL':.001,'m³':1000,'US gal':3.785411784,'US fl oz':.0295735295625,'US cup':.2365882365,'UK gal':4.54609},
 'Speed':{'m/s':1,'km/h':1/3.6,'mph':.44704,'knot':.5144444444},
 'Time':{'s':1,'ms':.001,'min':60,'h':3600,'day':86400,'week':604800},
 'Temperature':{'°C':1,'°F':1,'K':1},
 'Energy':{'J':1,'kJ':1000,'cal':4.184,'kcal':4184,'Wh':3600,'kWh':3600000,'eV':1.602176634e-19},
 'Power':{'W':1,'kW':1000,'MW':1e6,'hp':745.6998715823},
 'Pressure':{'Pa':1,'kPa':1000,'bar':100000,'atm':101325,'psi':6894.757293168},
 'Angle':{'rad':1,'deg':math.pi/180,'grad':math.pi/200,'turn':math.tau},
 'Data':{'B':1,'bit':.125,'kB':1000,'MB':1e6,'GB':1e9,'TB':1e12,'KiB':1024,'MiB':1048576,'GiB':1073741824},
 'Fuel economy':{'L/100km':1,'km/L':1,'US mpg':1,'UK mpg':1}}
def convert(value,category,source,target):
 x=D(str(value));units=UNITS[category]
 if source not in units or target not in units:raise MathError('Unknown unit')
 if category=='Temperature':
  c=(x-32)*5/9 if source=='°F' else x-D('273.15') if source=='K' else x
  return c*9/5+32 if target=='°F' else c+D('273.15') if target=='K' else c
 if category=='Fuel economy':
  def factor(u):return D('100') if u=='km/L' else D('235.214583') if u=='US mpg' else D('282.480936')
  base=x if source=='L/100km' else factor(source)/x
  return base if target=='L/100km' else factor(target)/base
 return x*D(str(units[source]))/D(str(units[target]))
class Engine:
 def __init__(self,path=None):
  self.path=Path(path or os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'quickintosh/calculator.json'
  self.expression='';self.value='0';self.error='';self.history=[];self.notes='';self.mode='basic';self.degrees=True;self.base=10;self.bits=64;self.rpn=False;self.stack=[];self.memory=D(0);self.done=False;self.repeat=None;self.undo=[];self.redo=[]
  try:
   d=json.loads(self.path.read_text());d=d if isinstance(d,dict) else {};rows=d.get('history',[]);self.history=[v for v in rows[:200] if isinstance(v,dict) and isinstance(v.get('expression'),str) and isinstance(v.get('result'),str) and isinstance(v.get('time'),(int,float))] if isinstance(rows,list) else [];self.notes=str(d.get('notes',''))[:16000]
  except (OSError,ValueError):pass
 def save(self):
  self.path.parent.mkdir(parents=True,exist_ok=True)
  fd,tmp=tempfile.mkstemp(dir=self.path.parent,prefix='.calculator-')
  try:
   with os.fdopen(fd,'w') as f:json.dump({'history':self.history[:200],'notes':self.notes},f,ensure_ascii=False)
   os.replace(tmp,self.path)
  finally:
   if os.path.exists(tmp):os.unlink(tmp)
 def evaluate(self,text):return Evaluator(self.degrees,self.bits).run(text)
 def state(self):
  try:
   n=int(self.evaluate(self.value));unsigned=n&((1<<self.bits)-1)
   bases={str(b):format(unsigned,{2:'b',8:'o',10:'d',16:'X'}[b]) for b in (2,8,10,16)}
   character=chr(n) if 32<=n<=0x10ffff and not 0xd800<=n<=0xdfff else ''
  except (ValueError,ArithmeticError):bases={};character=''
  shown=bases.get(str(self.base),self.value) if self.mode=='programmer' else self.value
  return dict(expression=self.expression,value=shown,rawValue=self.value,error=self.error,history=self.history,notes=self.notes,mode=self.mode,degrees=self.degrees,base=self.base,bits=self.bits,rpn=self.rpn,stack=self.stack,memory=number(self.memory),bases=bases,character=character,binary=bases.get('2','0').zfill(self.bits),units={k:list(v) for k,v in UNITS.items()})
 def record(self,expression,result):
  self.history.insert(0,{'expression':expression,'result':result,'time':time.time()});self.history=self.history[:200];self.save()
 def dispatch(self,r):
  self.error='';action=r.get('action','key');key=str(r.get('key',''))
  try:
   if action=='undo' or action=='redo':
    source,target=(self.undo,self.redo) if action=='undo' else (self.redo,self.undo)
    if source:target.append((self.expression,self.value,self.done,self.repeat));self.expression,self.value,self.done,self.repeat=source.pop()
   elif action=='toggleBit':
    bit=int(r.get('bit',-1))
    if not 0<=bit<self.bits:raise MathError('Invalid bit')
    self.value=str((int(self.evaluate(self.value))^(1<<bit))&((1<<self.bits)-1));self.expression=self.value;self.done=True
   elif action=='clearHistory':self.history=[];self.save()
   elif action=='deleteHistory':self.history=[item for item in self.history if item.get('time')!=r.get('time')];self.save()
   elif action=='restore':self.expression=str(r['expression']);self.value=number(self.evaluate(self.expression));self.done=False
   elif action=='convert':return {'conversion':number(convert(self.value,r['category'],r['source'],r['target']))}
   elif action=='notes':
    self.notes=str(r.get('text',''))[:16000];variables={};lines=[]
    for line in self.notes.splitlines():
     text=line.strip().rstrip('= ').strip()
     if not text:lines.append('');continue
     try:
      match=re.fullmatch(r'([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.+)',text)
      result=Evaluator(self.degrees,self.bits,variables).run(match[2] if match else text)
      if match:variables[match[1]]=result
      lines.append(number(result))
     except (MathError,ValueError,ArithmeticError):lines.append('')
    self.save();return {'noteResults':lines}
   elif action=='mode':self.mode=r['mode'] if r['mode'] in ('basic','scientific','programmer','notes') else 'basic';self.base=10;self.rpn=False
   elif action=='base':self.base=int(r['base']) if int(r['base']) in (2,8,10,16) else 10;self.expression='';self.done=True
   elif action=='bits':self.bits=int(r['bits']) if int(r['bits']) in (8,16,32,64) else 64
   elif action=='degrees':self.degrees=not self.degrees
   elif action=='rpn':self.rpn=not self.rpn;self.stack=[];self.expression='';self.done=False
   elif action=='stack':
    if key=='drop' and self.stack:self.stack.pop()
    elif key=='swap' and len(self.stack)>1:self.stack[-2:]=reversed(self.stack[-2:])
    elif key=='up' and self.stack:self.stack=self.stack[1:]+self.stack[:1]
    elif key=='down' and self.stack:self.stack=self.stack[-1:]+self.stack[:-1]
    self.value=self.stack[-1] if self.stack else '0';self.expression='';self.done=True
   elif action=='paste':
    value=str(r.get('text','')).strip();self.value=number(self.evaluate(value));self.expression=value;self.done=False
   elif action=='key':
    self.undo=(self.undo+[(self.expression,self.value,self.done,self.repeat)])[-100:];self.redo=[];self.key(key)
  except (ValueError,KeyError,ArithmeticError) as e:self.error=str(e) or 'Invalid calculation'
  return self.state()
 def key(self,k):
  if k=='AC':self.expression='';self.value='0';self.done=False;self.repeat=None;self.stack=[];return
  if k=='C' and self.mode!='programmer':self.expression=re.sub(r'(?:0[xob])?[\dA-Fa-f.]+$','',self.expression);self.value='0';self.done=False;return
  if k=='⌫':self.expression=self.expression[:-1];self.done=False
  elif k in ('mc','m+','m−','mr'):
   if k=='mc':self.memory=D(0)
   elif k=='m+':self.memory+=self.evaluate(self.value)
   elif k=='m−':self.memory-=self.evaluate(self.value)
   else:self.expression=number(self.memory);self.value=self.expression;self.done=True
   return
  elif k=='±':
   match=re.search(r'(?:\d+(?:\.\d*)?|\.\d+)$',self.expression) if not self.done else None
   if match:self.expression=self.expression[:match.start()]+'(-'+match[0]+')';self.value=number(self.evaluate(self.expression));self.done=False
   else:self.value=number(-self.evaluate(self.value));self.expression=self.value;self.done=True
   return
  elif k in ('=','Enter'):
   if self.rpn:
    self.stack=(self.stack+[number(self.evaluate(self.expression or self.value))])[-128:];self.expression='';self.done=True;return
   expr=self.expression or self.value
   expr+=')'*max(0,expr.count('(')-expr.count(')'))
   if self.done and self.repeat:expr=self.value+self.repeat
   value=number(self.evaluate(expr));self.record(expr,value)
   match=re.search(r'([+*/−-](?:[^+*/−]*))$',expr)
   if not self.done:self.repeat=match[1] if match else None
   self.value=value;self.expression=expr;self.done=True;return
  elif k=='Rand':self.value=str(secrets.randbelow(10**15)/10**15);self.expression=self.value;self.done=True;return
  elif k=='EE':self.expression=(self.value if self.done else self.expression)+'e';self.done=False;return
  elif k=='root':self.expression=(self.value if self.done else self.expression)+'^(1/';self.done=False;return
  elif k in ('sqrt','square','cube','reciprocal','factorial','sin','cos','tan','asin','acos','atan','sinh','cosh','tanh','asinh','acosh','atanh','log','log10','log2','exp','pow10','pow2','cbrt','abs','NOT'):
   x=self.expression if self.expression and not self.done else self.value
   expr={'square':f'({x})^2','cube':f'({x})^3','reciprocal':f'1/({x})','pow10':f'10^({x})','pow2':f'2^({x})','cbrt':f'cbrt({x})','NOT':f'~({x})'}.get(k,f'{k}({x})')
   self.value=number(self.evaluate(expr));self.expression=self.value;self.done=True;return
  elif k in ('+','−','×','÷','^','&','|','<<','>>','⊕','%'):
   op={'−':'-','×':'*','÷':'/'}.get(k,k)
   if self.rpn and op!='%':
    if self.expression:self.stack.append(number(self.evaluate(self.expression)))
    if len(self.stack)<2:raise MathError('Two stack values required')
    b,a=self.stack[-1],self.stack[-2];value=number(self.evaluate(f'({a}){op}({b})'));self.stack=self.stack[:-2]+[value];self.value=value;self.expression='';self.done=True;return
   if self.done or self.mode=='programmer':self.expression=self.value
   if op!='%' and self.expression.endswith(('+','-','*','/','^','&','|')):self.expression=self.expression[:-1]
   self.expression+=op;self.done=False
  else:
   if self.done:self.expression='';self.done=False
   if k=='π':k='pi'
   if self.mode=='programmer' and self.base!=10:
    prefix={2:'0b',8:'0o',16:'0x'}[self.base]
    match=re.search(r'(?:0[xob])?([0-9A-Fa-f]*)$',self.expression)
    old=match[1] if match else ''
    digits=old+str(k).upper()
    if not re.fullmatch('[0-9A-F]+',digits):raise MathError('Invalid digit')
    value=int(digits,self.base)
    if value>=(1<<self.bits):raise MathError('Value exceeds word size')
    self.expression=self.expression[:match.start()]+prefix+digits
    self.value=number(self.evaluate(self.expression));return
   if len(self.expression)<4096:self.expression+=k
  try:self.value=number(self.evaluate(self.expression)) if self.expression else '0'
  except (ValueError,ArithmeticError):pass
if __name__=='__main__':
 engine=Engine()
 print(json.dumps(engine.state(),ensure_ascii=False),flush=True)
 for line in sys.stdin:
  try:reply=engine.dispatch(json.loads(line))
  except Exception:engine.error='Invalid request';reply=engine.state()
  print(json.dumps(reply,ensure_ascii=False),flush=True)
