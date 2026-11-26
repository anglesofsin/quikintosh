# Settings organization and Quickshot validation (2026-11-25)

Settings navigation and compact card proportions follow the organization reviewed
in vladbiber/macshell at 48f73c94f7e54c2dce3206d3186875f52f139272. Existing
Quickintosh backends and pages remain in place. The account tile stays above the
scrolling category list; Widgets has its own real preferences/gallery page.
All 48 routes were opened in an isolated compositor without a Loader error.
Reference: https://github.com/vladbiber/macshell

The emoji popover now has one continuous filled outline for its body and arrow.
The former overlapping translucent rectangle and rotated square caused a dark
diamond/seam at the junction. Shape.CurveRenderer draws one shape instead.

Quickshot:
- Removed the centered “Rendering screenshot…” label.
- Unannotated selections crop the already captured pixels in the worker, avoiding
  the QML export surface, GPU readback and Qt PNG encoder.
- Full-display capture reuses grim's PNG without decoding RGB or querying clients.
- Annotated selections still render the annotations; Qt writes a fast uncompressed
  intermediate and the separate worker encodes the final lossless PNG.
- PNG compression level 1 trades some file size for faster lossless encoding.
- Atomic saves remain private (0600), collision-safe, and use a bounded copy buffer.

Six encoding+save samples per size on a synthetic screenshot-like RGB fixture:

| Source size | Previous PNG encode+save median | Worker crop+encode+save median |
| --- | ---: | ---: |
| 1920×1080 | 156.60 ms | 81.60 ms |
| 3840×2160 | 499.47 ms | 272.38 ms |

All output pixels compared identical. These are CPU encoding/copy measurements,
not promises about complete capture latency on every GPU/filesystem. A separate
nested compositor exercise saved both plain and annotated selections as valid
400×200 PNGs and checked a red annotation pixel. Backend tests also cover region
scaling, full-frame reuse, original-file preservation, filename collisions, PNG
conversion, private-directory checks and screenshot completion events.
