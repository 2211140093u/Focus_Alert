# Raspberry Pi 5でのワンタッチ起動設定

このドキュメントでは、Raspberry Pi 5でFocus Alertシステムをワンタッチで起動できるようにする手順を説明します。

## 前提条件

- Raspberry Pi OS がインストールされていること
- Raspberry Pi Camera V3 wide が接続されていること
- 3.5インチタッチモニタ（320×480）が接続されていること
- pyenv がインストールされ、Python 3.11環境が設定されていること
- システムPython（3.13）にpicamera2がインストールされていること

## セットアップ手順

### 1. プロジェクトの配置

プロジェクトをホームディレクトリに配置します（例：`/home/pi/Focus_Alert`）

```bash
cd ~
# プロジェクトを配置（git clone またはコピー）
```

### 2. デスクトップショートカットの作成

#### 方法1: デスクトップショートカット（推奨）

1. デスクトップショートカットファイルを編集：

```bash
nano ~/Desktop/focus_alert.desktop
```

2. 以下の内容を記述（パスを実際のプロジェクトパスに変更）：

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Focus Alert
Comment=集中力モニタリングシステム
Exec=/home/pi/Focus_Alert/scripts/start_focus_alert.sh
Icon=/home/pi/Focus_Alert/icon.png
Terminal=true
Categories=Utility;Science;
StartupNotify=true
```

3. 実行権限を付与：

```bash
chmod +x ~/Desktop/focus_alert.desktop
chmod +x ~/Focus_Alert/scripts/start_focus_alert.sh
```

4. アイコン画像（オプション）：
   - 詳細は [アイコンの設定ガイド](INSTALL_ICON.md) を参照
   - `~/Focus_Alert/icon.png` にアイコン画像を配置
   - または、`Icon=`の行を削除

#### 方法2: アプリケーションメニューに追加

1. システムのアプリケーションディレクトリにコピー：

```bash
sudo cp ~/Focus_Alert/scripts/focus_alert.desktop /usr/share/applications/
```

2. パスを編集：

```bash
sudo nano /usr/share/applications/focus_alert.desktop
```

3. `Exec=`と`Icon=`のパスを実際のパスに変更

### 3. 起動スクリプトの確認

`scripts/start_focus_alert.sh`が実行可能であることを確認：

```bash
chmod +x ~/Focus_Alert/scripts/start_focus_alert.sh
```

### 4. 自動起動の設定（オプション）

システム起動時に自動的にFocus Alertを起動する場合：

#### 方法1: systemdサービス（推奨）

1. サービスファイルを作成：

```bash
sudo nano /etc/systemd/system/focus-alert.service
```

2. 以下の内容を記述：

```ini
[Unit]
Description=Focus Alert System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Focus_Alert
ExecStart=/home/pi/Focus_Alert/scripts/start_focus_alert.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. サービスを有効化：

```bash
sudo systemctl daemon-reload
sudo systemctl enable focus-alert.service
sudo systemctl start focus-alert.service
```

4. 状態確認：

```bash
sudo systemctl status focus-alert.service
```

#### 方法2: autostart（デスクトップ自動起動）

1. 自動起動ディレクトリにショートカットを配置：

```bash
mkdir -p ~/.config/autostart
cp ~/Desktop/focus_alert.desktop ~/.config/autostart/
```

### 5. タッチスクリーンの設定（必要に応じて）

3.5インチタッチモニタが正しく認識されているか確認：

```bash
# タッチデバイスの確認
xinput list

# タッチスクリーンのキャリブレーション（必要に応じて）
# xinput_calibrator をインストール
sudo apt-get install xinput-calibrator
```

### 6. 動作確認

1. **デスクトップショートカットから起動**：
   - デスクトップの「Focus Alert」アイコンをダブルクリック
   - または、ターミナルから：
     ```bash
     ~/Focus_Alert/scripts/start_focus_alert.sh
     ```

2. **確認項目**：
   - カメラ映像が表示されること
   - タッチ操作でボタンが反応すること
   - ログファイルが`logs/`ディレクトリに作成されること

### 7. 停止方法

- アプリ内で「Quit」ボタンをタッチ
- または、ターミナルで`Ctrl+C`
- systemdサービスの場合：
  ```bash
  sudo systemctl stop focus-alert.service
  ```

## トラブルシューティング

### カメラが認識されない

```bash
# カメラの確認
libcamera-hello --list-cameras

# カメラのテスト
libcamera-hello
```

### pyenv環境が認識されない

```bash
# pyenvの確認
pyenv versions

# プロジェクトディレクトリで確認
cd ~/Focus_Alert
pyenv local focus-alert-311
```

### 権限エラー

```bash
# スクリプトに実行権限を付与
chmod +x ~/Focus_Alert/scripts/*.sh
chmod +x ~/Focus_Alert/scripts/*.py
```

### ログの確認

```bash
# アプリのログ
tail -f ~/Focus_Alert/logs/app_*.log

# カメラプロキシのログ
tail -f ~/Focus_Alert/logs/cam_proxy_*.log
```

## カスタマイズ

### 解像度の変更

`scripts/start_focus_alert.sh`を編集：

```bash
WIDTH=1280
HEIGHT=720
```

### FPSの変更

```bash
FPS=30
```

### ログの無効化

`scripts/start_focus_alert.sh`の`--log`オプションを削除

