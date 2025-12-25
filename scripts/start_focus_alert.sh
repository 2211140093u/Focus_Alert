#!/usr/bin/env bash
# Picamera2からの映像をZMQで配信する送信プロセス（system python）と、解析アプリ（pyenv 3.11）を起動する
# 使い方: ./scripts/start_focus_alert.sh [--width 640] [--height 480] [--fps 30] [--quality 85]
set -euo pipefail

WIDTH=640
HEIGHT=480
FPS=30
QUALITY=85
URL="tcp://127.0.0.1:5555"
TOPIC="frame"
APP_LOG_DIR="logs"

# 簡単なオプション引数を解析
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

# 1) カメラ送信プロセスを system python (3.13) でバックグラウンド起動
# システムPythonのパスを明示的に指定（pyenvの影響を排除）
SYSTEM_PYTHON3="/usr/bin/python3"
if [ ! -x "$SYSTEM_PYTHON3" ]; then
    # 代替パスを試す
    if [ -x "/usr/bin/python3.13" ]; then
        SYSTEM_PYTHON3="/usr/bin/python3.13"
    elif [ -x "/usr/bin/python3.12" ]; then
        SYSTEM_PYTHON3="/usr/bin/python3.12"
    elif [ -x "/usr/bin/python3.11" ]; then
        SYSTEM_PYTHON3="/usr/bin/python3.11"
    else
        echo "System python3 not found. Please install system python." >&2
        exit 1
    fi
fi

mkdir -p "$APP_LOG_DIR"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
PROXY_LOG="$APP_LOG_DIR/cam_proxy_${TIMESTAMP}.log"

(
  # エラーハンドリングを改善（確実にログに出力されるように）
  exec >"$PROXY_LOG" 2>&1
  # pyenvの影響を排除（環境変数をクリア）
  unset PYENV_VERSION
  unset PYENV_VIRTUAL_ENV
  unset PYENV_ROOT
  # PATHからpyenvのshimを除外
  export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v pyenv | tr '\n' ':' | sed 's/:$//')
  # エラーハンドリングを改善（起動メッセージをログに出力）
  echo "[cam_proxy] Starting with system Python: $SYSTEM_PYTHON3"
  echo "[cam_proxy] Project directory: $PROJ_DIR"
  echo "[cam_proxy] Python version: $($SYSTEM_PYTHON3 --version 2>&1)"
  echo "[cam_proxy] Checking picamera2 import..."
  if ! "$SYSTEM_PYTHON3" -c "from picamera2 import Picamera2; print('Picamera2 OK')" 2>&1; then
    echo "[cam_proxy] ERROR: Picamera2 import failed!" >&2
    exit 1
  fi
  echo "[cam_proxy] Starting camera proxy..."
  # システムPythonを直接実行
  exec "$SYSTEM_PYTHON3" "$PROJ_DIR/scripts/cam_proxy.py" \
    --url "$URL" --topic "$TOPIC" \
    --width "$WIDTH" --height "$HEIGHT" --fps "$FPS" --quality "$QUALITY"
) &
PROXY_PID=$!
echo "[launcher] cam_proxy started pid=$PROXY_PID (log: $PROXY_LOG)"

# 2) pyenv 3.11 のアプリ用環境を有効化してアプリを起動
if ! command -v pyenv >/dev/null 2>&1; then
  echo "pyenv not found. Please install pyenv and create 'focus-alert-311' env." >&2
  echo "  pyenv install 3.11.9 && pyenv virtualenv 3.11.9 focus-alert-311 && pyenv local focus-alert-311" >&2
  exit 1
fi

# このプロジェクト用のpyenvローカル環境を設定
if [[ ! -f "$PROJ_DIR/.python-version" ]]; then
  echo "focus-alert-311" > "$PROJ_DIR/.python-version"
fi

APP_LOG="$APP_LOG_DIR/app_${TIMESTAMP}.log"
(
  # エラーハンドリングを改善（確実にログに出力されるように）
  exec >"$APP_LOG" 2>&1
  # 環境変数の設定
  export DISPLAY="${DISPLAY:-:0}"
  export PYTHONUNBUFFERED=1
  # フルスクリーンモードの制御（環境変数で無効化可能）
  # Screen Sharingで確認する場合は FOCUS_ALERT_FULLSCREEN=0 を設定
  export FOCUS_ALERT_FULLSCREEN="${FOCUS_ALERT_FULLSCREEN:-1}"
  echo "[app_gui] Starting GUI application..."
  echo "[app_gui] Python version: $(python --version 2>&1)"
  echo "[app_gui] Project directory: $PROJ_DIR"
  # GUI版アプリを起動（メインメニューから選択可能）
  exec python "$PROJ_DIR/src/app_gui.py" \
    --backend zmq --zmq-url "$URL" --zmq-topic "$TOPIC" \
    --width "$WIDTH" --height "$HEIGHT" \
    --display-width 320 --display-height 480 \
    --log-dir "$APP_LOG_DIR" \
    --config-dir "$PROJ_DIR/config"
) &
APP_PID=$!
echo "[launcher] app (GUI) started pid=$APP_PID (log: $APP_LOG)"

echo "[launcher] To stop: kill $PROXY_PID $APP_PID"
echo "[launcher] Press Ctrl+C to stop both processes"

# クリーンアップ関数
cleanup() {
    echo "[launcher] Cleaning up..."
    kill $PROXY_PID $APP_PID 2>/dev/null || true
    exit 0
}

# シグナルハンドリング: Ctrl+Cで両方のプロセスを終了
trap cleanup INT TERM

# アプリプロセスが終了したら、カメラプロキシも終了させる
# APP_PIDを監視し、終了したらPROXY_PIDも終了
(
    while kill -0 $APP_PID 2>/dev/null; do
        sleep 1
    done
    echo "[launcher] App process ended, stopping camera proxy..."
    kill $PROXY_PID 2>/dev/null || true
) &

# 両方のプロセスが終了するまで待機
wait $APP_PID 2>/dev/null || true
wait $PROXY_PID 2>/dev/null || true

cleanup
