import ctypes as C
C.CDLL('/System/Library/Frameworks/Foundation.framework/Versions/C/Foundation',C.RTLD_GLOBAL)
C.CDLL('/System/Library/Frameworks/Combine.framework/Versions/A/Combine',C.RTLD_GLOBAL)
C.CDLL('/System/Library/Frameworks/CryptoKit.framework/Versions/A/CryptoKit',C.RTLD_GLOBAL)
C.CDLL('/System/Library/Frameworks/GameplayKit.framework/Versions/A/GameplayKit',C.RTLD_GLOBAL)
o=C.CDLL('/usr/lib/libobjc.A.dylib')
o.objc_getClass.argtypes=[C.c_char_p];o.objc_getClass.restype=C.c_void_p
o.sel_registerName.argtypes=[C.c_char_p];o.sel_registerName.restype=C.c_void_p
address=C.cast(o.objc_msgSend,C.c_void_p).value
def send(result,instance,name,*arguments):
 types=[arg[0] for arg in arguments];values=[arg[1] for arg in arguments]
 return C.CFUNCTYPE(result,C.c_void_p,C.c_void_p,*types)(address)(instance,o.sel_registerName(name),*values)
pool=send(C.c_void_p,send(C.c_void_p,o.objc_getClass('NSAutoreleasePool'),'alloc'),'init')
cls=o.objc_getClass('GKMersenneTwisterRandomSource');assert cls
obj=send(C.c_void_p,cls,'alloc');obj=send(C.c_void_p,obj,'initWithSeed:',(C.c_ulonglong,5489));assert obj
assert send(C.c_ulonglong,obj,'seed')==5489
assert send(C.c_ulonglong,obj,'qi_nextWord')==14514284786278117030
send(None,obj,'setSeed:',(C.c_ulonglong,1))
for i in range(17):send(C.c_ulonglong,obj,'qi_nextWord')
copy=send(C.c_void_p,obj,'copyWithZone:',(C.c_void_p,None));assert copy
for i in range(100):assert send(C.c_ulonglong,obj,'qi_nextWord')==send(C.c_ulonglong,copy,'qi_nextWord')
seen=set()
for i in range(1000):
 value=send(C.c_long,obj,'nextInt');assert -(1<<31)<=value<(1<<31)
 value=send(C.c_float,obj,'nextUniform');assert 0<=value<1
 assert send(C.c_byte,obj,'nextBool') in (0,1)
 value=send(C.c_ulong,obj,'nextIntWithUpperBound:',(C.c_ulong,7));assert 0<=value<7;seen.add(value)
 assert send(C.c_ulong,obj,'nextIntWithUpperBound:',(C.c_ulong,1))==0
 bound=(1<<63)+17;assert send(C.c_ulong,obj,'nextIntWithUpperBound:',(C.c_ulong,bound))<bound
assert len(seen)==7
array=send(C.c_void_p,send(C.c_void_p,o.objc_getClass('NSMutableArray'),'alloc'),'init')
for i in range(20):
 number=send(C.c_void_p,o.objc_getClass('NSNumber'),'numberWithLong:',(C.c_long,i))
 send(None,array,'addObject:',(C.c_void_p,number))
shuffled=send(C.c_void_p,obj,'arrayByShufflingObjectsInArray:',(C.c_void_p,array))
assert send(C.c_ulong,shuffled,'count')==20
values=[]
for i in range(20):
 original=send(C.c_void_p,array,'objectAtIndex:',(C.c_ulong,i));assert send(C.c_long,original,'longValue')==i
 number=send(C.c_void_p,shuffled,'objectAtIndex:',(C.c_ulong,i));values.append(send(C.c_long,number,'longValue'))
assert sorted(values)==list(range(20)) and values!=list(range(20))
base=o.objc_getClass('GKRandomSource')
assert send(C.c_void_p,base,'sharedRandom')==send(C.c_void_p,base,'sharedRandom')
send(None,array,'release');send(None,copy,'release');send(None,obj,'release');send(None,pool,'drain')
print('GAMEPLAYKIT_DARWIN_SEED_COPY_BOUNDS_FLOAT_BOOL_OK')
