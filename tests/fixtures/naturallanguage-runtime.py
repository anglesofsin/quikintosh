# coding: utf-8
import ctypes as C
C.CDLL('/System/Library/Frameworks/Foundation.framework/Versions/C/Foundation',C.RTLD_GLOBAL)
C.CDLL('/System/Library/Frameworks/NaturalLanguage.framework/Versions/A/NaturalLanguage',C.RTLD_GLOBAL)
o=C.CDLL('/usr/lib/libobjc.A.dylib')
o.objc_getClass.argtypes=[C.c_char_p];o.objc_getClass.restype=C.c_void_p
o.sel_registerName.argtypes=[C.c_char_p];o.sel_registerName.restype=C.c_void_p
address=C.cast(o.objc_msgSend,C.c_void_p).value
class Range(C.Structure):_fields_=[('location',C.c_ulong),('length',C.c_ulong)]
def send(result,instance,name,*args):
 return C.CFUNCTYPE(result,C.c_void_p,C.c_void_p,*[a[0] for a in args])(address)(instance,o.sel_registerName(name),*[a[1] for a in args])
def string(value):return send(C.c_void_p,o.objc_getClass('NSString'),'stringWithUTF8String:',(C.c_char_p,value.encode('utf-8')))
def text(value):return send(C.c_char_p,value,'UTF8String').decode('utf-8') if value else None
def array(values):
 pointers=(C.c_void_p*len(values))(*values)
 return send(C.c_void_p,o.objc_getClass('NSArray'),'arrayWithObjects:count:',(C.POINTER(C.c_void_p),pointers),(C.c_ulong,len(values)))
pool=send(C.c_void_p,send(C.c_void_p,o.objc_getClass('NSAutoreleasePool'),'alloc'),'init')
cls=o.objc_getClass('NLLanguageRecognizer');assert cls
recognizer=send(C.c_void_p,send(C.c_void_p,cls,'alloc'),'init')
assert not send(C.c_void_p,recognizer,'dominantLanguage')
portuguese=string(u'Este texto está escrito em português e descreve a vida das pessoas no Brasil. A ciência e a tecnologia ajudam a sociedade a encontrar soluções para seus desafios, enquanto os professores compartilham conhecimentos com os estudantes.')
english=string(u'This paragraph is written in English and describes the everyday life of people around the world. Science and technology help society find solutions while teachers share knowledge with their students.')
send(None,recognizer,'processString:',(C.c_void_p,portuguese))
assert text(send(C.c_void_p,recognizer,'dominantLanguage'))=='pt'
hypotheses=send(C.c_void_p,recognizer,'languageHypothesesWithMaximum:',(C.c_ulong,1))
assert send(C.c_ulong,hypotheses,'count')==1
assert text(send(C.c_void_p,cls,'dominantLanguageForString:',(C.c_void_p,english)))=='en'
constraints=array([string(u'en')]);send(None,recognizer,'setLanguageConstraints:',(C.c_void_p,constraints))
assert not send(C.c_void_p,recognizer,'dominantLanguage')
send(None,recognizer,'reset')
assert send(C.c_ulong,send(C.c_void_p,recognizer,'languageConstraints'),'count')==1
assert not send(C.c_void_p,recognizer,'dominantLanguage')
send(None,recognizer,'setLanguageConstraints:',(C.c_void_p,None))
send(None,recognizer,'processString:',(C.c_void_p,english));assert text(send(C.c_void_p,recognizer,'dominantLanguage'))=='en'
send(None,recognizer,'reset');assert not send(C.c_void_p,recognizer,'dominantLanguage')
print('NL_DETECT_PT_EN_RESET_CONSTRAINTS_OK')
cls=o.objc_getClass('NLTokenizer');assert cls
tokenizer=send(C.c_void_p,send(C.c_void_p,cls,'alloc'),'initWithUnit:',(C.c_long,0))
assert send(C.c_long,tokenizer,'unit')==0
source=string(u'Olá 😀 mundo 123!')
send(None,tokenizer,'setString:',(C.c_void_p,source));send(None,tokenizer,'setLanguage:',(C.c_void_p,string(u'pt')))
for index,expected in [(1,(0,3)),(4,(4,2)),(7,(7,5)),(3,((1<<63)-1,0)),(17,((1<<63)-1,0))]:
 result=send(Range,tokenizer,'tokenRangeAtIndex:',(C.c_ulong,index));assert (result.location,result.length)==expected,(index,result.location,result.length)
result=send(Range,tokenizer,'tokenRangeForRange:',(Range,Range(1,10)));assert (result.location,result.length)==(0,12)
tokens=send(C.c_void_p,tokenizer,'tokensForRange:',(Range,Range(0,17)));assert send(C.c_ulong,tokens,'count')==4
result=send(Range,send(C.c_void_p,tokens,'objectAtIndex:',(C.c_ulong,1)),'rangeValue');assert (result.location,result.length)==(4,2)
result=send(Range,tokenizer,'tokenRangeForRange:',(Range,Range(1,(1<<64)-1)));assert (result.location,result.length)==(0,16)
tokens=send(C.c_void_p,tokenizer,'tokensForRange:',(Range,Range(1,(1<<64)-1)));assert send(C.c_ulong,tokens,'count')==0
system=C.CDLL('/usr/lib/libSystem.B.dylib')
class Descriptor(C.Structure):_fields_=[('reserved',C.c_ulong),('size',C.c_ulong)]
class Block(C.Structure):_fields_=[('isa',C.c_void_p),('flags',C.c_int),('reserved',C.c_int),('invoke',C.c_void_p),('descriptor',C.POINTER(Descriptor))]
visited=[]
@C.CFUNCTYPE(None,C.c_void_p,Range,C.c_ulong,C.POINTER(C.c_byte))
def callback(block,token,flags,stop):
 visited.append((token.location,token.length,flags));stop[0]=1
metadata=Descriptor(0,C.sizeof(Block));block=Block(C.addressof(C.c_void_p.in_dll(system,'_NSConcreteGlobalBlock')),1<<28,0,C.cast(callback,C.c_void_p),C.pointer(metadata))
send(None,tokenizer,'enumerateTokensInRange:usingBlock:',(Range,Range(0,17)),(C.c_void_p,C.addressof(block)));assert visited==[(0,3,0)],visited
send(None,tokenizer,'setString:',(C.c_void_p,string(u'foo bar')))
assert send(C.c_ulong,send(C.c_void_p,tokenizer,'tokensForRange:',(Range,Range(0,7))),'count')==2
send(None,tokenizer,'setString:',(C.c_void_p,None));result=send(Range,tokenizer,'tokenRangeAtIndex:',(C.c_ulong,0));assert result.location==(1<<63)-1
send(None,tokenizer,'release');send(None,recognizer,'release');send(None,pool,'drain')
print('NATURALLANGUAGE_DARWIN_UTF16_RANGES_EMPTY_OVERFLOW_OK')
