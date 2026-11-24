#!/usr/bin/env bash
set -e

ENGINE="${SAY_ENGINE:-espeak}"
LANG="${SAY_LANG:-pt-br}"
VOICE="${SAY_VOICE:-}"
SPEED="${SAY_SPEED:-175}"
SINK_NAME=say_sink
SOURCE_NAME=say_mic
FIFO_PATH=/tmp/say-kokoro.fifo

while [ $# -gt 0 ]; do
    case "$1" in
        --engine) ENGINE="$2"; shift 2 ;;
        --lang) LANG="$2"; shift 2 ;;
        --voice) VOICE="$2"; shift 2 ;;
        --speed) SPEED="$2"; shift 2 ;;
        --) shift; break ;;
        *) break ;;
    esac
done

if ! pw-cli list-objects 2>/dev/null | grep -q "$SINK_NAME"; then
    pw-loopback \
        --capture-props "media.class=Audio/Sink node.name=$SINK_NAME" \
        --playback-props "media.class=Audio/Source node.name=$SOURCE_NAME" \
        --latency 20 &
    disown
    sleep 0.5
fi

REAL_SOURCE=$(pactl get-default-source 2>/dev/null || echo "")
if [ -n "$REAL_SOURCE" ]; then
    if ! pw-cli list-objects 2>/dev/null | grep -q "say_mic_loop"; then
        pw-loopback \
            --capture "$REAL_SOURCE" \
            --playback "$SINK_NAME" \
            --name "say_mic_loop" \
            --latency 20 &
        disown
        pactl set-default-source "$SOURCE_NAME" 2>/dev/null || true
    fi
fi

if [ "$ENGINE" = "kokoro" ]; then
    if [ ! -p "$FIFO_PATH" ]; then
        notify-send -a "Text to Speech" "Kokoro daemon not running. Start it in plugin settings." -u critical
        exit 1
    fi

    KOKORO_LANG="$LANG"
    case "$LANG" in
        pt-br) KOKORO_LANG="p" ;;
        en-us) KOKORO_LANG="a" ;;
        en-gb) KOKORO_LANG="b" ;;
        fr-fr) KOKORO_LANG="f" ;;
        es)    KOKORO_LANG="e" ;;
        it)    KOKORO_LANG="i" ;;
        hi)    KOKORO_LANG="h" ;;
        ja)    KOKORO_LANG="j" ;;
        zh)    KOKORO_LANG="z" ;;
    esac

    if [ -z "$VOICE" ]; then
        case "$KOKORO_LANG" in
            p) VOICE="pm_alex" ;;
            a) VOICE="af_heart" ;;
            b) VOICE="bf_emma" ;;
            f) VOICE="ff_siwis" ;;
            e) VOICE="ef_dora" ;;
            i) VOICE="if_sara" ;;
            h) VOICE="hf_alpha" ;;
            j) VOICE="jf_alpha" ;;
            z) VOICE="zf_alpha" ;;
            *) VOICE="af_heart" ;;
        esac
    fi

    KOKORO_SPEED=$(awk "BEGIN {printf \"%.1f\", $SPEED / 10}")

    printf '%s\0%s\0%s\0%s' "$KOKORO_LANG" "$VOICE" "$KOKORO_SPEED" "$*" > "$FIFO_PATH"
else
    VOICE_ARG="$LANG"
    if [ -n "$VOICE" ]; then
        VOICE_ARG="$VOICE"
    fi
    espeak-ng -v "$VOICE_ARG" -s "$SPEED" "$*" --stdout | tee >(pw-play --latency 20 -) | pw-play --target="$SINK_NAME" --latency 20 -
fi
