"""Repair the June release's missing private-extern corecrypto exports.

Security.framework imports these existing implementations through libSystem's
corecrypto re-export. Their nlist entries are present but absent from dyld's
export trie. Publish the original addresses; do not replace crypto algorithms.
Both Intel slices are updated, using LIEF's Mach-O writer.
"""
import sys
import lief

binary = lief.MachO.parse(sys.argv[1])
count = 0
for architecture in binary:
    symbols = [symbol for symbol in architecture.symbols
               if int(symbol.raw_type) == 0x1e and symbol.name.startswith('_cc')]
    for symbol in symbols:
        if architecture.add_exported_function(symbol.value, symbol.name) is None:
            raise RuntimeError('Could not repair corecrypto export ' + symbol.name)
        count += 1
if not count:
    raise RuntimeError('The pinned Darling corecrypto layout changed; review the patch.')
binary.write(sys.argv[1])
print('Restored corecrypto exports:', count)
