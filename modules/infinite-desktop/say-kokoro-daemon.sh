#!/usr/bin/env bash
set -e
KOKORO_DIR="$HOME/.local/share/say-kokoro"
VENV_DIR="$KOKORO_DIR/venv"
PID_FILE="/tmp/say-kokoro-daemon.pid"
CMD="${1:-status}"

start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Kokoro daemon already running"
        return
    fi
    if [ ! -d "$VENV_DIR" ]; then
        /home/pg/scripts/setup-kokoro.sh
    fi
    nohup nix-shell /home/pg/scripts/kokoro/shell.nix --run \
        "source '$VENV_DIR/bin/activate' && python3 /home/pg/scripts/say-kokoro.py" \
        > /tmp/say-kokoro-daemon.log 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Kokoro daemon started"
    else
        echo "Failed to start"
        rm -f "$PID_FILE"
    fi
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Kokoro daemon not running"
        return
    fi
    PID=$(cat "$PID_FILE")
    kill "$PID" 2>/dev/null || true
    rm -f /tmp/say-kokoro.fifo "$PID_FILE"
    echo "Kokoro daemon stopped"
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "running"
    else
        echo "stopped"
    fi
}

case "$CMD" in
    start) start ;;
    stop) stop ;;
    status) status ;;
    restart) stop; sleep 1; start ;;
    *)
        if [ ! -d "$VENV_DIR" ]; then
            /home/pg/scripts/setup-kokoro.sh
        fi
        exec nix-shell /home/pg/scripts/kokoro/shell.nix --run \
            "source '$VENV_DIR/bin/activate' && python3 /home/pg/scripts/say-kokoro.py"
        ;;
esac
