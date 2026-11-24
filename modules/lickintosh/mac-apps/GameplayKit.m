/* Public API contracts: Apple's GKRandom and GKMersenneTwisterRandomSource
 * documentation. This is an Intel-only subset, not the complete GameplayKit.
 * NSObject declarations below use the public 64-bit Objective-C ABI; no SDK
 * from a macOS installation is needed to build it.
 */
#include "mt19937-64.h"
typedef unsigned long NSUInteger;
typedef long NSInteger;
typedef signed char BOOL;
typedef struct objc_class *Class;
typedef struct _NSZone NSZone;
@class NSString, NSArray, NSMutableArray;
extern void arc4random_buf(void *, unsigned long);
extern void *malloc(unsigned long);
extern void free(void *);
extern void *memcpy(void *, const void *, unsigned long);

__attribute__((objc_root_class))
@interface NSObject { Class isa; }
+ (id)alloc;
+ (id)allocWithZone:(NSZone *)zone;
- (id)init;
- (Class)class;
- (void)dealloc;
- (id)autorelease;
@end
@interface NSException : NSObject
+ (void)raise:(NSString *)name format:(NSString *)format, ...;
@end
extern NSString * const NSInvalidArgumentException;
extern NSString * const NSMallocException;
@interface NSArray : NSObject
- (NSUInteger)count;
- (id)mutableCopy;
@end
@interface NSMutableArray : NSArray
- (void)exchangeObjectAtIndex:(NSUInteger)a withObjectAtIndex:(NSUInteger)b;
@end

@protocol GKRandom
- (NSInteger)nextInt;
- (NSUInteger)nextIntWithUpperBound:(NSUInteger)bound;
- (float)nextUniform;
- (BOOL)nextBool;
@end

@interface GKRandomSource : NSObject <GKRandom>
+ (instancetype)sharedRandom;
- (QIMTWord)qi_nextWord;
- (NSArray *)arrayByShufflingObjectsInArray:(NSArray *)array;
@end

@interface GKMersenneTwisterRandomSource : GKRandomSource {
    QIMTState *_state;
    QIMTWord _seed;
}
@property QIMTWord seed;
- (instancetype)initWithSeed:(QIMTWord)seed;
- (id)copyWithZone:(NSZone *)zone;
@end

@implementation GKRandomSource
+ (instancetype)sharedRandom {
    static GKRandomSource *source;
    @synchronized(self) { if (!source) source = [[GKRandomSource alloc] init]; }
    return source;
}
- (QIMTWord)qi_nextWord {
    QIMTWord result;
    arc4random_buf(&result, sizeof(result));
    return result;
}
- (NSInteger)nextInt { return (int)[self qi_nextWord]; }
- (NSUInteger)nextIntWithUpperBound:(NSUInteger)bound {
    if (!bound) [NSException raise:NSInvalidArgumentException format:@"upperBound must be positive"];
    QIMTWord limit = (0ULL - bound) % bound;
    QIMTWord value;
    do { value = [self qi_nextWord]; } while (value < limit);
    return value % bound;
}
- (float)nextUniform { return ([self qi_nextWord] >> 40) * (1.0f / 16777216.0f); }
- (BOOL)nextBool { return ([self qi_nextWord] & 1) != 0; }
- (NSArray *)arrayByShufflingObjectsInArray:(NSArray *)array {
    NSMutableArray *result = [array mutableCopy];
    for (NSUInteger count = [result count]; count > 1; --count)
        [result exchangeObjectAtIndex:count-1 withObjectAtIndex:[self nextIntWithUpperBound:count]];
    return [result autorelease];
}
@end

@implementation GKMersenneTwisterRandomSource
- (instancetype)init {
    QIMTWord seed;
    arc4random_buf(&seed, sizeof(seed));
    return [self initWithSeed:seed];
}
- (instancetype)initWithSeed:(QIMTWord)seed {
    self = [super init];
    if (self) {
        _state = malloc(sizeof(*_state));
        if (!_state) [NSException raise:NSMallocException format:@"Cannot allocate random-source state"];
        [self setSeed:seed];
    }
    return self;
}
- (QIMTWord)seed { @synchronized(self) { return _seed; } }
- (void)setSeed:(QIMTWord)seed {
    @synchronized(self) { _seed = seed; qi_mt_seed(_state, seed); }
}
- (QIMTWord)qi_nextWord { @synchronized(self) { return qi_mt_next(_state); } }
- (id)copyWithZone:(NSZone *)zone {
    @synchronized(self) {
        GKMersenneTwisterRandomSource *copy = [[[self class] allocWithZone:zone] initWithSeed:_seed];
        memcpy(copy->_state, _state, sizeof(*_state));
        return copy;
    }
}
- (void)dealloc { free(_state); [super dealloc]; }
@end
