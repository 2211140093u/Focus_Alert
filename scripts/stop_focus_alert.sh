#!/bin/bash
# Focus Alertシステムを停止するスクリプト

# プロセス名で検索して終了
pkill -f "cam_proxy.py"
pkill -f "app.py.*--backend zmq"

echo "Focus Alertシステムを停止しました。"

