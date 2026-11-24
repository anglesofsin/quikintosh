/* Clean-room public thumbnail API backed by Darling AppKit image decoding.
 * Unsupported formats report an error rather than producing a fake thumbnail.
 */
#include "Foundation-NL.h"
typedef struct { double width,height; } QSize;
typedef struct { double x,y; } QPoint;
typedef struct { QPoint origin; QSize size; } QRect;
@interface NSError : NSObject
+ (id)errorWithDomain:(NSString *)domain code:(NSInteger)code userInfo:(NSDictionary *)info;
@end
@interface NSImage : NSObject
- (id)initWithContentsOfURL:(id)url;
- (QSize)size;
- (void)setSize:(QSize)size;
- (NSArray *)representations;

@end
@interface NSObject (QIImageQueries)
- (BOOL)respondsToSelector:(void *)selector;
- (void *)CGImage;
@end
extern void *CGColorSpaceCreateDeviceRGB(void);
extern void CGColorSpaceRelease(void *);
extern void *CGBitmapContextCreate(void *,NSUInteger,NSUInteger,NSUInteger,NSUInteger,void *,unsigned int);
extern void CGContextDrawImage(void *,QRect,void *);
extern void *CGBitmapContextCreateImage(void *);
extern void CGContextRelease(void *);
extern void CGImageRelease(void *);
extern void dispatch_async(void *, void (^)(void));
extern void *dispatch_get_global_queue(long,unsigned long);
extern void dispatch_once(long *,void (^)(void));
NSString *const QLThumbnailErrorDomain = @"QLThumbnailErrorDomain";
@interface QLThumbnailGenerationRequest : NSObject {
    id _fileURL,_contentType;
    QSize _size;
    double _scale,_minimumDimension;
    NSUInteger _representationTypes;
    BOOL _iconMode;
}
@property(readonly) id fileURL;
@property(readonly) QSize size;
@property(readonly) double scale;
@property(readonly) NSUInteger representationTypes;
@property double minimumDimension;
@property BOOL iconMode;
@property(copy) id contentType;
- (id)initWithFileAtURL:(id)url size:(QSize)size scale:(double)scale representationTypes:(NSUInteger)types;
@end
@implementation QLThumbnailGenerationRequest
@synthesize fileURL=_fileURL,size=_size,scale=_scale,representationTypes=_representationTypes;
@synthesize minimumDimension=_minimumDimension,iconMode=_iconMode,contentType=_contentType;
- (id)initWithFileAtURL:(id)url size:(QSize)size scale:(double)scale representationTypes:(NSUInteger)types {
    if ((self=[super init])) { _fileURL=[url copy];_size=size;_scale=scale;_representationTypes=types; }
    return self;
}
- (void)dealloc { [_fileURL release];[_contentType release];[super dealloc]; }
@end
@interface QLThumbnailRepresentation : NSObject { NSImage *_image; void *_cgImage; double _scale; }
- (id)initWithImage:(NSImage *)image scale:(double)scale;
- (NSImage *)NSImage;
- (void *)CGImage;
- (NSInteger)type;
- (QRect)contentRect;
@end
@implementation QLThumbnailRepresentation
- (id)initWithImage:(NSImage *)image scale:(double)scale { if((self=[super init])) { _image=[image retain];_scale=scale; } return self; }
- (NSImage *)NSImage {return _image;}
- (void *)CGImage {
    if(_cgImage)return _cgImage;
    NSArray *representations=[_image representations];
    void *source=0;
    for(NSUInteger i=0;i<[representations count] && !source;i++) {
        id representation=[representations objectAtIndex:i];
        if([representation respondsToSelector:@selector(CGImage)])source=[representation CGImage];
    }
    if(!source)return 0;
    QSize size=[_image size];
    double pixelWidth=size.width*_scale,pixelHeight=size.height*_scale;
    if(!__builtin_isfinite(pixelWidth) || !__builtin_isfinite(pixelHeight) || pixelWidth>16384 || pixelHeight>16384)return 0;
    NSUInteger width=(NSUInteger)(pixelWidth+.5),height=(NSUInteger)(pixelHeight+.5);
    if(!width || !height || width>16384 || height>16384 || width*height>16777216)return 0;
    void *space=CGColorSpaceCreateDeviceRGB();
    void *context=CGBitmapContextCreate(0,width,height,8,width*4,space,1 | (4<<12));
    CGColorSpaceRelease(space);
    if(!context)return 0;
    CGContextDrawImage(context,(QRect){{0,0},{width,height}},source);
    _cgImage=CGBitmapContextCreateImage(context);CGContextRelease(context);
    return _cgImage;
}
- (NSInteger)type {return 2;}
- (QRect)contentRect {return (QRect){{0,0},[_image size]};}
- (void)dealloc {if(_cgImage)CGImageRelease(_cgImage);[_image release];[super dealloc];}
@end
@interface QLThumbnailGenerator : NSObject
+ (id)sharedGenerator;
@end
@implementation QLThumbnailGenerator
+ (id)sharedGenerator {static id shared;static long once;dispatch_once(&once,^{shared=[[self alloc]init];});return shared;}
- (void)generateBestRepresentationForRequest:(QLThumbnailGenerationRequest *)request completionHandler:(void (^)(id,NSError *))handler {
    if(!handler)return;
    dispatch_async(dispatch_get_global_queue(0,0),^{
        NSImage *image=[[[NSImage alloc]initWithContentsOfURL:[request fileURL]]autorelease];
        QSize size=[image size],limit=[request size];
        if(([request representationTypes]&4) && image && [[image representations] count]>0 && size.width>0 && size.height>0 && limit.width>0 && limit.height>0 && [request scale]>0 && __builtin_isfinite(size.width) && __builtin_isfinite(size.height) && __builtin_isfinite(limit.width) && __builtin_isfinite(limit.height) && __builtin_isfinite([request scale])) {
            double ratio=limit.width/size.width;if(limit.height/size.height<ratio)ratio=limit.height/size.height;
            if(ratio<1)[image setSize:(QSize){size.width*ratio,size.height*ratio}];
            QLThumbnailRepresentation *thumbnail=[[[QLThumbnailRepresentation alloc]initWithImage:image scale:[request scale]]autorelease];
            if([thumbnail CGImage])handler(thumbnail,nil);
            else handler(nil,[NSError errorWithDomain:QLThumbnailErrorDomain code:0 userInfo:nil]);
        } else handler(nil,[NSError errorWithDomain:QLThumbnailErrorDomain code:0 userInfo:nil]);
    });
}
- (void)generateRepresentationsForRequest:(QLThumbnailGenerationRequest *)request updateHandler:(void (^)(id,NSInteger,NSError *))handler {
    if(handler)[self generateBestRepresentationForRequest:request completionHandler:^(id image,NSError *error){handler(image,2,error);}];
}
- (void)cancelRequest:(QLThumbnailGenerationRequest *)request { /* Completed bounded decoding has no long-lived request. */ }
- (void)saveBestRepresentationForRequest:(id)request toFileAtURL:(id)url withContentType:(id)type completionHandler:(void (^)(NSError *))handler {
    if(handler)dispatch_async(dispatch_get_global_queue(0,0),^{handler([NSError errorWithDomain:QLThumbnailErrorDomain code:1 userInfo:nil]);});
}
- (void)saveBestRepresentationForRequest:(id)request toFileAtURL:(id)url asContentType:(id)type completionHandler:(void (^)(NSError *))handler {
    [self saveBestRepresentationForRequest:request toFileAtURL:url withContentType:type completionHandler:handler];
}
@end
