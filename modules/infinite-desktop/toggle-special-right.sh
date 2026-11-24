#!/usr/bin/env bash
# Right-slide special workspace ("special:right"): enters from the RIGHT edge and
# leaves toward the RIGHT edge.
exec "$(dirname -- "$0")/special-toggle.sh" right
