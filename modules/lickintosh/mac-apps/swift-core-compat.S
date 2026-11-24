/* Apache-2.0 with Runtime Library Exception; adapted from VibeDarling/
 * darling-swift 78a04e469481027bf4294022a4bffc71a41886d0, swift_compat.S.
 * Only forwarding aliases and Swift force-load markers are included.
 * UI, metadata and Foundation success-returning placeholders are omitted.
 */
.data
.globl __swift_FORCE_LOAD_$_swiftCoreAudio
__swift_FORCE_LOAD_$_swiftCoreAudio: .quad 0
.globl __swift_FORCE_LOAD_$_swiftCoreFoundation
__swift_FORCE_LOAD_$_swiftCoreFoundation: .quad 0
.globl __swift_FORCE_LOAD_$_swiftCoreImage
__swift_FORCE_LOAD_$_swiftCoreImage: .quad 0
.globl __swift_FORCE_LOAD_$_swiftCoreMIDI
__swift_FORCE_LOAD_$_swiftCoreMIDI: .quad 0
.globl __swift_FORCE_LOAD_$_swiftCoreMedia
__swift_FORCE_LOAD_$_swiftCoreMedia: .quad 0

.text
.globl _swift_getTypeByMangledNameInContext2
_swift_getTypeByMangledNameInContext2:
    jmp _swift_getTypeByMangledNameInContext

.globl _swift_getTypeByMangledNameInContextInMetadataState2
_swift_getTypeByMangledNameInContextInMetadataState2:
    mov %rsi, %rdi
    mov %rdx, %rsi
    mov %rcx, %rdx
    mov %r8, %rcx
    jmp _swift_getTypeByMangledNameInContext

.globl _$ss12_ArrayBufferV19_getElementSlowPathyyXlSiFyXl_Ts5
_$ss12_ArrayBufferV19_getElementSlowPathyyXlSiFyXl_Ts5:
    jmp _$ss12_ArrayBufferV19_getElementSlowPathyyXlSiF
