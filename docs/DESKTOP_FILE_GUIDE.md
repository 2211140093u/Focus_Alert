# デスクトップファイルの設定ガイド

## 日本語入力について

デスクトップファイル（`.desktop`）に日本語を入力する場合、UTF-8エンコーディングで保存する必要があります。

### 方法1: エディタでUTF-8で保存

```bash
# nanoエディタで開く
nano ~/Desktop/focus_alert.desktop

# 編集後、Ctrl+Oで保存、Ctrl+Xで終了
# エンコーディングは自動的にUTF-8になります
```

### 方法2: Comment行を削除または英語にする

Comment行は必須ではないため、削除しても問題ありません：

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Focus Alert
# Comment行を削除または英語にする
Comment=Concentration Monitoring System
Exec=/home/mm/Focus_Alert/scripts/start_focus_alert.sh
Icon=/home/mm/Focus_Alert/icon.png
Terminal=true
Categories=Utility;Science;
StartupNotify=true
```

### 方法3: 英語のみを使用

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Focus Alert
Comment=Concentration Monitoring System
Exec=/home/mm/Focus_Alert/scripts/start_focus_alert.sh
Icon=/home/mm/Focus_Alert/icon.png
Terminal=true
Categories=Utility;Science;
StartupNotify=true
```

## デスクトップファイルの作成手順

1. デスクトップファイルを作成：

```bash
nano ~/Desktop/focus_alert.desktop
```

2. 以下の内容を記述（パスは実際のプロジェクトパスに変更）：

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Focus Alert
Comment=Concentration Monitoring System
Exec=/home/mm/Focus_Alert/scripts/start_focus_alert.sh
Icon=/home/mm/Focus_Alert/icon.png
Terminal=true
Categories=Utility;Science;
StartupNotify=true
```

3. 実行権限を付与：

```bash
chmod +x ~/Desktop/focus_alert.desktop
```

4. デスクトップデータベースを更新：

```bash
update-desktop-database ~/.local/share/applications/
```

## トラブルシューティング

### デスクトップファイルから起動できない

1. **ログファイルを確認**：

```bash
# 最新のログファイルを確認
ls -lt ~/Focus_Alert/logs/
tail -50 ~/Focus_Alert/logs/cam_proxy_*.log
tail -50 ~/Focus_Alert/logs/app_*.log
```

2. **実行権限を確認**：

```bash
ls -l ~/Desktop/focus_alert.desktop
ls -l ~/Focus_Alert/scripts/start_focus_alert.sh
```

3. **パスを確認**：

```bash
# デスクトップファイルのExec行のパスが正しいか確認
cat ~/Desktop/focus_alert.desktop | grep Exec
```

4. **ターミナルから直接実行**：

```bash
# デスクトップファイルと同じコマンドをターミナルから実行
/home/mm/Focus_Alert/scripts/start_focus_alert.sh
```

### 空のログファイルが生成される

これは、プロセスが起動直後に終了している可能性があります。ログファイルの内容を確認してください：

```bash
# ログファイルのサイズを確認
ls -lh ~/Focus_Alert/logs/cam_proxy_*.log

# ログファイルの内容を確認（空でないか）
cat ~/Focus_Alert/logs/cam_proxy_*.log
```

もしログファイルが空の場合、起動スクリプトのエラーハンドリングを確認してください。

