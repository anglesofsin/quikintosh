#!/usr/bin/env bash
# Stream-visible scratchpad ("special:public"): NOT hidden from capture.
# Slides from the TOP edge and back to the TOP edge.
exec "$(dirname -- "$0")/special-toggle.sh" public
