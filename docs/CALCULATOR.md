# Calculator

Open **Calculator** / **calculadora** in Spotlight, click the Calculator tile in
Control Center, or run `quickintosh-calculator`. The same app is included in the
Arch runtime. A second launch reuses the running window instead of creating a
second calculator. Closing the window retains the application for warm reopening.
The calculator runs separately from the shell.

The compact view follows the supplied macOS references: SF Pro, circular keys,
orange arithmetic operators, a separate expression/result display and optional
history at the left. The compositor provides native live glass; there is no
wallpaper screenshot or client blur shader. Normal system glass/accessibility
settings still apply. Mode changes request size changes for this app only,
without racing changing Qt minimum and maximum window constraints.

## Modes and controls

- **Basic:** order of operations, parentheses, decimal arithmetic, context-aware
  percentages, sign changes, backspace and repeated equals.
- **Scientific:** memory, powers and roots, factorial, exponential/logarithmic,
  trigonometric, inverse and hyperbolic functions, constants, random numbers,
  exponential entry, degrees/radians and a second-function bank.
- **Programmer:** binary/octal/decimal/hex, 8/16/32/64-bit words, AND/OR/XOR/NOT,
  shifts, Unicode display and clickable individual bits. Integer operations do
  not pass through JavaScript's 53-bit numeric precision limit.
- **RPN:** bounded stack, enter, swap, roll up/down and drop.
- **Conversions:** length, mass, area, volume, speed, time, temperature, energy,
  power, pressure, angle, data, fuel economy and currency. Exchange rates are
  daily reference rates from Frankfurter; their date is displayed. Cached rates
  can be used offline, with an offline label. Network fetching is outside the
  arithmetic worker and UI event loop, and only starts for Currency.
- **Math Notes:** local typed expressions and variable assignments, one per line,
  with results alongside. These are not Apple Notes, handwriting recognition,
  graphing or iCloud synchronization.
- **History:** newest first, grouped by date; click to reuse, right-click to copy
  or delete an entry. Clearing all history requires confirmation.

Use the calculator-mode button at the lower left or the menu bar. Ctrl+1/2/3
select Basic/Scientific/Programmer; Ctrl+R toggles RPN; Ctrl+H toggles history;
Ctrl+Alt+C toggles conversions; Ctrl+Alt+M opens notes. Ctrl+C/V copies/pastes,
Ctrl+Z/Shift+Ctrl+Z undoes/redoes input, Enter evaluates, Escape clears and
Backspace deletes. The red window button or Ctrl+W closes the window.

## Persistence and implementation

History (up to 200 results) and notes live in
`${XDG_STATE_HOME:-~/.local/state}/quickintosh/calculator.json`, written atomically
with private file permissions. Arithmetic uses a bounded Python AST visitor,
not `eval`, with 34-digit decimal context for ordinary arithmetic. Scientific
transcendental functions use the standard math library. Limits bound expression,
exponent, factorial and RPN stack work. The worker is persistent and idle when
unused; keypresses do not spawn processes or fetch network data.

`python3 tests/test_calculator.py` covers arithmetic, percentages, scientific
functions, exact large integers, bit operations, RPN, conversions, undo/redo,
notes, history, malformed saved state and rejected/costly expressions. The
isolated UI regression is `tests/test_calculator_ui.py`; it refuses the host
Wayland runtime. It requires the same private-compositor environment variables
as the panel tests. Measurements from a nested software compositor are not a
promise of zero latency on every machine or workload.

References: [Apple's Tahoe guide](https://support.apple.com/en-ge/guide/calculator/welcome/12.0/mac/26),
[mode overview](https://support.apple.com/guide/calculator/choose-the-right-mode-calc22d50970/mac),
[Frankfurter API](https://frankfurter.dev/v1/).
