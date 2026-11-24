/* Public 64-bit Foundation/Objective-C declarations used by our bridge.
 * This is a link interface, not a replacement Foundation implementation.
 */
typedef unsigned long NSUInteger;
typedef long NSInteger;
typedef signed char BOOL;
typedef struct objc_class *Class;
typedef struct { NSUInteger location, length; } NSRange;
typedef struct _NSZone NSZone;
#define nil ((id)0)
#define NSNotFound ((NSUInteger)__LONG_MAX__)
#define YES ((BOOL)1)
#define NO ((BOOL)0)
@class NSString, NSArray, NSDictionary, NSError;
__attribute__((objc_root_class))
@interface NSObject { Class isa; }
+ (id)alloc;
- (id)init;
- (id)retain;
- (oneway void)release;
- (id)copy;
- (id)autorelease;
- (void)dealloc;
@end
@interface NSString : NSObject
+ (id)stringWithUTF8String:(const char *)string;
- (const char *)UTF8String;
- (NSUInteger)length;
- (NSInteger)compare:(NSString *)other;
- (BOOL)isEqualToString:(NSString *)other;
@end
@interface NSArray : NSObject
+ (id)array;
- (NSUInteger)count;
- (id)objectAtIndex:(NSUInteger)index;
- (BOOL)containsObject:(id)object;
@end
@interface NSMutableArray : NSArray
- (void)addObject:(id)object;
@end
@interface NSDictionary : NSObject
+ (id)dictionary;
+ (id)dictionaryWithObjectsAndKeys:(id)object, ...;
- (id)objectForKey:(id)key;
- (NSArray *)allKeys;
- (NSUInteger)count;
@end
@interface NSMutableDictionary : NSDictionary
- (void)setObject:(id)object forKey:(id)key;
- (void)removeAllObjects;
@end
@interface NSNumber : NSObject
+ (id)numberWithLong:(long)value;
+ (id)numberWithDouble:(double)value;
- (double)doubleValue;
- (NSUInteger)unsignedLongValue;
@end
@interface NSData : NSObject
+ (id)dataWithBytes:(const void *)data length:(NSUInteger)length;
- (const void *)bytes;
- (NSUInteger)length;
@end
@interface NSValue : NSObject
+ (id)valueWithRange:(NSRange)range;
@end
@interface NSException : NSObject
+ (void)raise:(NSString *)name format:(NSString *)format, ...;
@end
@interface NSJSONSerialization : NSObject
+ (NSData *)dataWithJSONObject:(id)object options:(NSUInteger)options error:(NSError **)error;
+ (id)JSONObjectWithData:(NSData *)data options:(NSUInteger)options error:(NSError **)error;
@end
extern NSString *const NSInvalidArgumentException;
extern NSString *const NSInternalInconsistencyException;
extern void *malloc(unsigned long);
extern void free(void *);
extern unsigned long strlen(const char *);
extern void *memcpy(void *, const void *, unsigned long);
extern char *getenv(const char *);
