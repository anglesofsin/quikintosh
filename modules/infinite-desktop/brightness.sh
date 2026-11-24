#!/usr/bin/env bash
set -euo pipefail

STEP=10
MIN=0
MAX=100

get_brightness() {
    ddcutil getvcp 10 | grep -oP 'current value =\s+\K[0-9]+'
}

current=$(get_brightness)
[ -z "$current" ] && current=$MAX

case "${1:-}" in
    increase)
        new=$((current + STEP))
        [ "$new" -gt "$MAX" ] && new=$MAX
        ddcutil setvcp 10 "$new"
        ;;
    decrease)
        new=$((current - STEP))
        [ "$new" -lt "$MIN" ] && new=$MIN
        ddcutil setvcp 10 "$new"
        ;;
    *)
        echo "Usage: $0 {increase|decrease}"
        exit 1
        ;;
esac
