#!/bin/bash
mkdir -p ~/Pictures/Screenshots
FILE=~/Pictures/Screenshots/$(date '+%Y-%m-%d_%H-%M-%S').png
grim -g "$(slurp)" "$FILE" && wl-copy < "$FILE"
