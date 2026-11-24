# Optional GUI smoke test: use a dedicated virtual DISPLAY, not the desktop.
import ctypes as C,time,sys
C.CDLL("/System/Library/Frameworks/AppKit.framework/Versions/C/AppKit",C.RTLD_GLOBAL)
o=C.CDLL("/usr/lib/libobjc.A.dylib")
o.objc_getClass.argtypes=[C.c_char_p];o.objc_getClass.restype=C.c_void_p
o.sel_registerName.argtypes=[C.c_char_p];o.sel_registerName.restype=C.c_void_p
address=C.cast(o.objc_msgSend,C.c_void_p).value
class Point(C.Structure):_fields_=[("x",C.c_double),("y",C.c_double)]
class Size(C.Structure):_fields_=[("width",C.c_double),("height",C.c_double)]
class Rect(C.Structure):_fields_=[("origin",Point),("size",Size)]
def send(result,instance,name,*args):
 return C.CFUNCTYPE(result,C.c_void_p,C.c_void_p,*[a[0] for a in args])(address)(instance,o.sel_registerName(name),*[a[1] for a in args])
pool=send(C.c_void_p,send(C.c_void_p,o.objc_getClass("NSAutoreleasePool"),"alloc"),"init")
app=send(C.c_void_p,o.objc_getClass("NSApplication"),"sharedApplication")
window=send(C.c_void_p,send(C.c_void_p,o.objc_getClass("NSWindow"),"alloc"),"initWithContentRect:styleMask:backing:defer:",(Rect,Rect(Point(100,100),Size(360,200))),(C.c_ulong,15),(C.c_ulong,2),(C.c_byte,0))
title=send(C.c_void_p,o.objc_getClass("NSString"),"stringWithUTF8String:",(C.c_char_p,"Quickintosh compatibility validation"))
send(None,window,"setTitle:",(C.c_void_p,title));send(None,window,"makeKeyAndOrderFront:",(C.c_void_p,None))
send(None,window,"display");send(None,window,"flushWindow")
assert send(C.c_byte,window,"isVisible")
print("APPKIT_VIRTUAL_WINDOW_VISIBLE");sys.stdout.flush();time.sleep(10)
send(None,window,"close");send(None,pool,"drain")
