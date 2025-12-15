#!/usr/bin/env bash
# Launches the Picamera2 -> ZMQ proxy (system python) and the Focus Alert app (pyenv 3.11)
# Usage: ./scripts/start_focus_alert.sh [--width 640] [--height 480] [--fps 30] [--quality 85]
set -euo pipefail

WIDTH=640
HEIGHT=480
FPS=30
QUALITY=85
URL="tcp://127.0.0.1:5555"
TOPIC="frame"
APP_LOG_DIR="logs"

# Parse simple flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --width) WIDTH="$2"; shift 2;;
    --height) HEIGHT="$2"; shift 2;;
    --fps) FPS="$2"; shift 2;;
    --quality) QUALITY="$2"; shift 2;;
    --url) URL="$2"; shift 2;;
    --topic) TOPIC="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJ_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJ_DIR"

# 1) Start camera proxy with system python (3.13) in background
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found. Please install system python." >&2
  exit 1
fi

mkdir -p "$APP_LOG_DIR"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
PROXY_LOG="$APP_LOG_DIR/cam_proxy_${TIMESTAMP}.log"

( \
  exec python3 "$PROJ_DIR/scripts/cam_proxy.py" \
    --url "$URL" --topic "$TOPIC" \
    --width "$WIDTH" --height "$HEIGHT" --fps "$FPS" --quality "$QUALITY" \
) >"$PROXY_LOG" 2>&1 &
PROXY_PID=$!
echo "[launcher] cam_proxy started pid=$PROXY_PID (log: $PROXY_LOG)"

# 2) Activate pyenv 3.11 app env and start app
if ! command -v pyenv >/dev/null 2>&1; then
  echo "pyenv not found. Please install pyenv and create 'focus-alert-311' env." >&2
  echo "  pyenv install 3.11.9 && pyenv virtualenv 3.11.9 focus-alert-311 && pyenv local focus-alert-311" >&2
  exit 1
fi

# Ensure local pyenv env is set for this project
if [[ ! -f "$PROJ_DIR/.python-version" ]]; then
  echo "focus-alert-311" > "$PROJ_DIR/.python-version"
fi

APP_LOG="$APP_LOG_DIR/app_${TIMESTAMP}.log"
(
  export PYTHONUNBUFFERED=1
  # run app
  exec python "$PROJ_DIR/src/app.py" \
    --backend zmq --zmq-url "$URL" --zmq-topic "$TOPIC" \
    --width "$WIDTH" --height "$HEIGHT" \
    --alert-mode off --learning off \
    --log "$APP_LOG_DIR/pi_${TIMESTAMP}.csv"
) >"$APP_LOG" 2>&1 &
APP_PID=$!
echo "[launcher] app started pid=$APP_PID (log: $APP_LOG)"

echo "[launcher] To stop: kill $PROXY_PID $APP_PID"
