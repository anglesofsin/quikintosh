# coding: utf-8
import ctypes as C
import os
import sys
import threading
C.CDLL('/System/Library/Frameworks/Foundation.framework/Versions/C/Foundation',C.RTLD_GLOBAL)
C.CDLL('/System/Library/Frameworks/QuickLookThumbnailing.framework/Versions/A/QuickLookThumbnailing',C.RTLD_GLOBAL)
cg=C.CDLL('/System/Library/Frameworks/CoreGraphics.framework/Versions/A/CoreGraphics')
cf=C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation')
for name in ['CGImageGetWidth','CGImageGetHeight']:
 getattr(cg,name).argtypes=[C.c_void_p];getattr(cg,name).restype=C.c_ulong
cg.CGImageGetDataProvider.argtypes=[C.c_void_p];cg.CGImageGetDataProvider.restype=C.c_void_p
cg.CGDataProviderCopyData.argtypes=[C.c_void_p];cg.CGDataProviderCopyData.restype=C.c_void_p
cf.CFDataGetBytePtr.argtypes=[C.c_void_p];cf.CFDataGetBytePtr.restype=C.POINTER(C.c_ubyte)
cf.CFRelease.argtypes=[C.c_void_p]
o=C.CDLL('/usr/lib/libobjc.A.dylib');system=C.CDLL('/usr/lib/libSystem.B.dylib')
o.objc_getClass.argtypes=[C.c_char_p];o.objc_getClass.restype=C.c_void_p
o.sel_registerName.argtypes=[C.c_char_p];o.sel_registerName.restype=C.c_void_p
address=C.cast(o.objc_msgSend,C.c_void_p).value
class Size(C.Structure):_fields_=[('width',C.c_double),('height',C.c_double)]
def send(result,instance,name,*args):
 return C.CFUNCTYPE(result,C.c_void_p,C.c_void_p,*[a[0] for a in args])(address)(instance,o.sel_registerName(name),*[a[1] for a in args])
def string(value):return send(C.c_void_p,o.objc_getClass('NSString'),'stringWithUTF8String:',(C.c_char_p,value.encode('utf-8')))
class Descriptor(C.Structure):_fields_=[('reserved',C.c_ulong),('size',C.c_ulong)]
class Block(C.Structure):_fields_=[('isa',C.c_void_p),('flags',C.c_int),('reserved',C.c_int),('invoke',C.c_void_p),('descriptor',C.POINTER(Descriptor))]
pool=send(C.c_void_p,send(C.c_void_p,o.objc_getClass('NSAutoreleasePool'),'alloc'),'init')
generator=send(C.c_void_p,o.objc_getClass('QLThumbnailGenerator'),'sharedGenerator');assert generator
for path,valid,scale,limit in [(sys.argv[1],True,1,64),(sys.argv[1],True,2,64),('/tmp/quickintosh-file-that-does-not-exist.png',False,1,64),(sys.argv[1],False,1,0),(sys.argv[1],False,float('inf'),64)]:
 url=send(C.c_void_p,o.objc_getClass('NSURL'),'fileURLWithPath:',(C.c_void_p,string(path)))
 request=send(C.c_void_p,send(C.c_void_p,o.objc_getClass('QLThumbnailGenerationRequest'),'alloc'),'initWithFileAtURL:size:scale:representationTypes:',(C.c_void_p,url),(Size,Size(limit,limit)),(C.c_double,scale),(C.c_ulong,4))
 assert send(C.c_ulong,request,'representationTypes')==4
 assert send(C.c_double,request,'scale')==scale
 finished=threading.Event();result=[]
 @C.CFUNCTYPE(None,C.c_void_p,C.c_void_p,C.c_void_p)
 def callback(block,representation,error):
  if representation:
   image=send(C.c_void_p,representation,'NSImage');size=send(Size,image,'size')
   native=send(C.c_void_p,representation,'CGImage')
   width,height=cg.CGImageGetWidth(native),cg.CGImageGetHeight(native)
   data=cg.CGDataProviderCopyData(cg.CGImageGetDataProvider(native))
   pixel=tuple(cf.CFDataGetBytePtr(data)[i] for i in range(4));cf.CFRelease(data)
   result.append((bool(image),bool(error),size.width,size.height,width,height,pixel))
  else:result.append((False,bool(error),0,0))
  finished.set()
 descriptor=Descriptor(0,C.sizeof(Block));block=Block(C.addressof(C.c_void_p.in_dll(system,'_NSConcreteGlobalBlock')),1<<28,0,C.cast(callback,C.c_void_p),C.pointer(descriptor))
 send(None,generator,'generateBestRepresentationForRequest:completionHandler:',(C.c_void_p,request),(C.c_void_p,C.addressof(block)))
 assert finished.wait(10),'thumbnail callback was never delivered'
 assert result[0][0]==valid and result[0][1]!=valid,result
 if valid:assert 0<result[0][2]<=64 and 0<result[0][3]<=64 and result[0][4]==64*scale and result[0][5]==32*scale and all(abs(a-b)<=2 for a,b in zip(result[0][6],(51,102,153,255))),result
 send(None,request,'release')
send(None,pool,'drain')
print('THUMBNAIL_DARWIN_IMAGE_SIZE_ASYNC_ERROR_CALLBACK_OK')
