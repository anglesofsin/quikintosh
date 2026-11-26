# Dock drag anchoring

The old drag translated the artwork by pointer travel from the press position.
Grid reordering and magnification also move the tile underneath, so those two
movements accumulated and displaced the artwork away from the pointer.

During a drag, retain the pointer in window scene coordinates and map that point
back into the tile each frame. Translate the artwork center to that local point.
The dragged artwork uses its normal size and suspends its launch bounce while
dragging. Reordering still uses total pointer travel from the original press,
independent of the visual correction. Release keeps the existing return motion.
The frame callback runs only during a drag and stops on release or cancellation.

Validation: the actual DockTile component loaded in a nested compositor. With a
stationary scene-space pointer, change the parent's position, magnification,
orientation, ancestor scale and bounce. Artwork center errors measured 0, 0,
0.000008 and 0.000026 logical pixels. This verifies coordinate anchoring; it does
not measure physical pointer-to-display latency.
