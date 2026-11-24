/* Clean-room public API implementation.
 * Contracts: developer.apple.com/documentation/naturallanguage/{nltokenizer,nllanguagerecognizer}.
 * Enum/attribute ABI: Darling 6ac4c0d73747e041e971ac920933f3db6bb73659 public headers.
 * Private IPC ABI: Linux x86_64 socket(2), unix(7), syscall(2).
 * Language classification uses local CLD2; token boundaries use local ICU.
 */
#include "Foundation-NL.h"
/* Private host IPC uses Linux calls directly. The deployed Darling socket path
 * translation cannot connect to the visible host AF_UNIX socket; no Darwin socket API is replaced.
 * This framework runs only on the x86_64 Linux compatibility runtime. */
static long NLHostCall(long number, long a, long b, long c, long d, long e, long f) {
    register long r10 __asm__("r10") = d;
    register long r8 __asm__("r8") = e;
    register long r9 __asm__("r9") = f;
    long result;
    __asm__ volatile("syscall" : "=a"(result)
        : "a"(number), "D"(a), "S"(b), "d"(c), "r"(r10), "r"(r8), "r"(r9)
        : "rcx", "r11", "memory", "cc");
    return result;
}

NSString *const NLLanguageEnglish = @"en";
NSString *const NLLanguageUndetermined = @"und";
NSString *const NLLanguagePortuguese = @"pt";
NSString *const NLLanguageFrench = @"fr";
NSString *const NLLanguageSpanish = @"es";
NSString *const NLLanguageGerman = @"de";
NSString *const NLLanguageJapanese = @"ja";
NSString *const NLLanguageSimplifiedChinese = @"zh-Hans";
NSString *const NLLanguageTraditionalChinese = @"zh-Hant";

static void NLFailure(NSString *stage) {
    [NSException raise:NSInternalInconsistencyException
                 format:@"The local Quickintosh language provider is unavailable (%@)",stage];
}
static BOOL NLTransfer(int fd, void *bytes, NSUInteger count, BOOL writing) {
    unsigned char *cursor = bytes;
    while (count) {
        long size = NLHostCall(writing ? 44 : 45, fd, (long)cursor, count, writing ? 0x4000 : 0, 0, 0);
        if (size == -4) continue;
        if (size <= 0) return NO;
        cursor += size; count -= size;
    }
    return YES;
}

static NSDictionary *NLRequest(NSString *operation, NSString *text, NSInteger unit, NSString *language) {
    const char *path = getenv("QUICKINTOSH_NL_SOCKET");
    struct { unsigned short family; char path[108]; } address = {0};
    if (!path || strlen(path) >= sizeof(address.path)) { NLFailure(@"socket configuration"); return nil; }
    memcpy(address.path, path, strlen(path)+1);
    address.family = 1;
    int fd = (int)NLHostCall(41, 1, 1 | 0x80000, 0, 0, 0, 0);
    if (fd < 0) { NLFailure(@"socket creation"); return nil; }
    @try {
        // Linux x86_64 timeval and SOL_SOCKET timeout options.
        struct { long seconds, micros; } timeout = {10, 0};
        if (NLHostCall(54, fd, 1, 21, (long)&timeout, sizeof(timeout), 0) ||
            NLHostCall(54, fd, 1, 20, (long)&timeout, sizeof(timeout), 0) ||
            NLHostCall(42, fd, (long)&address, 2 + strlen(path) + 1, 0, 0, 0)) { NLFailure(@"connection"); return nil; }
        NSDictionary *request = [NSDictionary dictionaryWithObjectsAndKeys:
            operation, @"operation", text ? text : @"", @"text",
            [NSNumber numberWithLong:unit], @"unit", language ? language : @"und", @"language", nil];
        NSData *data = [NSJSONSerialization dataWithJSONObject:request options:0 error:0];
        NSUInteger length = [data length];
        if (!data || length > 4*1024*1024) { NLFailure(@"request serialization"); return nil; }
        unsigned char header[4] = {length>>24, length>>16, length>>8, length};
        if (!NLTransfer(fd, header, 4, YES) || !NLTransfer(fd, (void *)[data bytes], length, YES) ||
            !NLTransfer(fd, header, 4, NO)) { NLFailure(@"request/response transfer"); return nil; }
        length = ((NSUInteger)header[0]<<24) | ((NSUInteger)header[1]<<16) |
                 ((NSUInteger)header[2]<<8) | header[3];
        if (!length || length > 4*1024*1024) { NLFailure(@"response size"); return nil; }
        void *buffer = malloc(length);
        if (!buffer) { NLFailure(@"response allocation"); return nil; }
        BOOL read = NLTransfer(fd, buffer, length, NO);
        NSData *response = read ? [NSData dataWithBytes:buffer length:length] : nil;
        free(buffer);
        NSDictionary *decoded = response ? [NSJSONSerialization JSONObjectWithData:response options:0 error:0] : nil;
        NSDictionary *result = [decoded objectForKey:@"result"];
        if (!result || [decoded objectForKey:@"error"]) { NLFailure(@"response decoding"); return nil; }
        return result;
    } @finally { NLHostCall(3, fd, 0, 0, 0, 0, 0); }
}

@interface NLLanguageRecognizer : NSObject {
    NSMutableDictionary *_weights;
    NSDictionary *_languageHints;
    NSArray *_languageConstraints;
}
@property(copy) NSDictionary *languageHints;
@property(copy) NSArray *languageConstraints;
+ (NSString *)dominantLanguageForString:(NSString *)text;
- (void)processString:(NSString *)text;
- (NSString *)dominantLanguage;
- (NSDictionary *)languageHypothesesWithMaximum:(NSUInteger)maximum;
- (void)reset;
@end

@implementation NLLanguageRecognizer
@synthesize languageHints = _languageHints;
@synthesize languageConstraints = _languageConstraints;
- (instancetype)init {
    self = [super init];
    if (self) {
        _weights = [[NSMutableDictionary alloc] init];
        _languageHints = [[NSDictionary alloc] init];
        _languageConstraints = [[NSArray alloc] init];
    }
    return self;
}
+ (NSString *)dominantLanguageForString:(NSString *)text {
    NLLanguageRecognizer *recognizer = [[[self alloc] init] autorelease];
    [recognizer processString:text];
    return [recognizer dominantLanguage];
}
- (void)processString:(NSString *)text {
    if (![text length]) return;
    NSDictionary *result = NLRequest(@"detect", text, 0, nil);
    double weight = [[result objectForKey:@"weight"] doubleValue];
    NSArray *languages = [result objectForKey:@"languages"];
    for (NSUInteger i=0; i<[languages count]; ++i) {
        NSArray *pair = [languages objectAtIndex:i];
        NSString *key = [pair objectAtIndex:0];
        double score = [[_weights objectForKey:key] doubleValue] + weight * [[pair objectAtIndex:1] doubleValue];
        [_weights setObject:[NSNumber numberWithDouble:score] forKey:key];
    }
}
- (NSDictionary *)languageHypothesesWithMaximum:(NSUInteger)maximum {
    NSMutableDictionary *scores = [NSMutableDictionary dictionary];
    NSArray *keys = [_weights allKeys];
    double total = 0;
    for (NSUInteger i=0; i<[keys count]; ++i) {
        NSString *key = [keys objectAtIndex:i];
        if ([_languageConstraints count] && ![_languageConstraints containsObject:key]) continue;
        double hint = [[_languageHints objectForKey:key] doubleValue];
        if (!(hint>=0 && hint<=1)) hint = 0;
        double score = [[_weights objectForKey:key] doubleValue] * (1 + 3*hint);
        [scores setObject:[NSNumber numberWithDouble:score] forKey:key]; total += score;
    }
    NSMutableDictionary *result = [NSMutableDictionary dictionary];
    NSMutableArray *used = [NSMutableArray array];
    keys = [scores allKeys];
    for (NSUInteger index=0; total>0 && index<maximum && index<[keys count]; ++index) {
        NSString *best = nil; double bestScore = -1;
        for (NSUInteger i=0; i<[keys count]; ++i) {
            NSString *key = [keys objectAtIndex:i];
            if ([used containsObject:key]) continue;
            double score = [[scores objectForKey:key] doubleValue];
            if (score>bestScore || (score==bestScore && best && [key compare:best]<0)) { best=key; bestScore=score; }
        }
        if (!best) break;
        [used addObject:best]; [result setObject:[NSNumber numberWithDouble:bestScore/total] forKey:best];
    }
    return result;
}
- (NSString *)dominantLanguage {
    NSArray *keys = [[self languageHypothesesWithMaximum:1] allKeys];
    return [keys count] ? [[[keys objectAtIndex:0] copy] autorelease] : nil;
}
- (void)reset { [_weights removeAllObjects]; }
- (void)dealloc { [_weights release]; [_languageHints release]; [_languageConstraints release]; [super dealloc]; }
@end

@interface NLTokenizer : NSObject {
    NSString *_string;
    NSString *_language;
    NSInteger _unit;
    NSArray *_tokens;
}
@property(copy) NSString *string;
@property(readonly) NSInteger unit;
- (instancetype)initWithUnit:(NSInteger)unit;
- (void)setLanguage:(NSString *)language;
- (NSArray *)qi_tokens;
- (NSRange)tokenRangeAtIndex:(NSUInteger)index;
- (NSRange)tokenRangeForRange:(NSRange)range;
- (NSArray *)tokensForRange:(NSRange)range;
- (void)enumerateTokensInRange:(NSRange)range usingBlock:(void (^)(NSRange,NSUInteger,BOOL *))block;
@end

@implementation NLTokenizer
@synthesize unit = _unit;
- (instancetype)initWithUnit:(NSInteger)unit {
    self = [super init];
    if (unit<0 || unit>3) [NSException raise:NSInvalidArgumentException format:@"Invalid token unit"];
    if (self) _unit=unit;
    return self;
}
- (NSString *)string { return _string; }
- (void)setString:(NSString *)string {
    NSString *copy=[string copy]; [_string release]; _string=copy; [_tokens release]; _tokens=nil;
}
- (void)setLanguage:(NSString *)language {
    NSString *copy=[language copy]; [_language release]; _language=copy; [_tokens release]; _tokens=nil;
}
- (NSArray *)qi_tokens {
    if (!_tokens) {
        _tokens = [_string length] ? [[NLRequest(@"tokens",_string,_unit,_language) objectForKey:@"tokens"] copy]
                                  : [[NSArray alloc] init];
    }
    return _tokens;
}
static NSRange NLRange(NSArray *token) {
    NSRange value={[[token objectAtIndex:0] unsignedLongValue],[[token objectAtIndex:1] unsignedLongValue]};
    return value;
}
static BOOL NLIntersects(NSRange token,NSRange range) {
    return range.length ? token.location<range.location+range.length && token.location+token.length>range.location
                        : range.location>=token.location && range.location<token.location+token.length;
}
- (NSRange)tokenRangeAtIndex:(NSUInteger)index { NSRange range={index,0}; return [self tokenRangeForRange:range]; }
- (NSRange)tokenRangeForRange:(NSRange)range {
    NSRange result={NSNotFound,0}; NSUInteger length=[_string length];
    if (!length || range.location>=length) return result;
    if (range.length>length-range.location) range.length=length-range.location;
    NSArray *tokens=[self qi_tokens];
    for (NSUInteger i=0; i<[tokens count]; ++i) {
        NSRange token=NLRange([tokens objectAtIndex:i]);
        if (!NLIntersects(token,range)) continue;
        if (result.location==NSNotFound) result=token;
        else result.length=token.location+token.length-result.location;
    }
    return result;
}
- (void)enumerateTokensInRange:(NSRange)range usingBlock:(void (^)(NSRange,NSUInteger,BOOL *))block {
    NSUInteger length=[_string length];
    if (!block || !length || range.location>length || range.length>length-range.location) return;
    if (!range.length && range.location==0 && _unit!=3) return;
    NSArray *tokens=[[[self qi_tokens] retain] autorelease]; BOOL stop=NO;
    for (NSUInteger i=0; i<[tokens count] && !stop; ++i) {
        NSArray *token=[tokens objectAtIndex:i]; NSRange location=NLRange(token);
        if (NLIntersects(location,range)) block(location,[[token objectAtIndex:2] unsignedLongValue],&stop);
    }
}
- (NSArray *)tokensForRange:(NSRange)range {
    NSMutableArray *tokens=[NSMutableArray array];
    [self enumerateTokensInRange:range usingBlock:^(NSRange token,NSUInteger flags,BOOL *stop) {
        [tokens addObject:[NSValue valueWithRange:token]];
    }];
    return tokens;
}
- (void)dealloc { [_string release]; [_language release]; [_tokens release]; [super dealloc]; }
@end
