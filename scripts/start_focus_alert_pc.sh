#!/bin/bash
# PC用の起動スクリプト（Mac/Linux）
# 使い方: ./scripts/start_focus_alert_pc.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJ_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJ_DIR"

# 仮想環境が存在するか確認
if [ ! -d "venv" ]; then
    echo "仮想環境が見つかりません。まず仮想環境を作成してください。"
    echo "python3 -m venv venv"
    exit 1
fi

# 仮想環境を有効化
source venv/bin/activate

# ログディレクトリを作成
mkdir -p logs

# タイムスタンプ付きログファイル名
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# アプリを起動（高解像度で起動）
python src/app.py --cam 0 --width 1280 --height 720 --log "logs/pc_${TIMESTAMP}.csv"

