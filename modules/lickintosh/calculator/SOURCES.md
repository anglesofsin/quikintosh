# Calculator design and behavior references

User screenshots: compact circular keypad, translucent window, separate expression/result and optional left history.

Apple's macOS Tahoe guide:
- https://support.apple.com/en-ge/guide/calculator/welcome/12.0/mac/26
- https://support.apple.com/guide/calculator/choose-the-right-mode-calc22d50970/mac
- https://support.apple.com/guide/calculator/calcf964141e/mac
- https://support.apple.com/guide/calculator/calcc4fc3386/mac
- https://support.apple.com/guide/calculator/calce87b2f66/mac
- https://support.apple.com/guide/calculator/calc2bbb5464/mac

Rates: https://frankfurter.dev/v1/ — daily reference rates, cached with their published date; these are not live trading quotes.

This implementation uses native compositor glass, SF Pro, and an independent
bounded arithmetic worker. It is not Apple's proprietary Calculator or Notes.
Math Notes are local typed expressions and variables, without handwriting or iCloud.
