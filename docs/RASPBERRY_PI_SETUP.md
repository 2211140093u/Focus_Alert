# Raspberry Pi 5でのワンタッチ起動設定

このドキュメントでは、Raspberry Pi 5でFocus Alertシステムをワンタッチで起動できるようにする手順を説明します。

## 前提条件

- Raspberry Pi OS がインストールされていること
- Raspberry Pi Camera V3 wide が接続されていること
- 3.5インチタッチモニタ（320×480）が接続されていること

**注意**: このシステムは二重プロセス構成のため、以下のPython環境が必要です：
- **システムPython 3.13**: Picamera2用（セットアップ手順0.2でインストール）
- **pyenv Python 3.11**: MediaPipe用（セットアップ手順0.3-0.6でセットアップ）

初回セットアップ時は、**セクション0（Python環境のセットアップ）**から開始してください。

## セットアップ手順

### 0. Python環境のセットアップ

このシステムは、**二重プロセス構成**を採用しています：
- **システムPython 3.13**: Picamera2でカメラから映像を取得
- **pyenv Python 3.11**: MediaPipeで顔検出と集中力判定

#### 0.1 システムPythonの確認

まず、システムにインストールされているPythonのバージョンを確認します：

```bash
python3 --version
```

Raspberry Pi OSでは、通常Python 3.11または3.13がインストールされています。本システムでは**Python 3.13**を使用します。

#### 0.2 システムPythonへのPicamera2のインストール

Picamera2は、システムPythonにインストールする必要があります：

```bash
# システムのパッケージマネージャーでインストール
sudo apt-get update
sudo apt-get install -y python3-picamera2 python3-numpy python3-opencv python3-zmq
```

インストールが完了したら、動作確認：

```bash
python3 -c "from picamera2 import Picamera2; print('Picamera2 OK')"
```

#### 0.3 pyenvのインストール

pyenvは、複数のPythonバージョンを管理するツールです。インストール手順：

```bash
# 必要な依存パッケージをインストール
sudo apt-get update
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
  libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
  libffi-dev liblzma-dev

# pyenvをインストール
curl https://pyenv.run | bash
```

インストール後、シェルの設定ファイルにpyenvのパスを追加します：

```bash
# ~/.bashrcに追加
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# 設定を反映
source ~/.bashrc
```

インストール確認：

```bash
pyenv --version
```

#### 0.4 Python 3.11のインストール（pyenv経由）

pyenvを使ってPython 3.11をインストールします：

```bash
# Python 3.11.9をインストール（時間がかかります）
pyenv install 3.11.9

# インストールされたバージョンを確認
pyenv versions
```

#### 0.5 仮想環境の作成

プロジェクト用の仮想環境を作成します：

```bash
# プロジェクトディレクトリに移動（後で配置する場所）
cd ~/Focus_Alert

# Python 3.11.9を使用して仮想環境を作成
pyenv virtualenv 3.11.9 focus-alert-311

# このプロジェクトで使用するPythonバージョンを設定
pyenv local focus-alert-311

# 仮想環境が有効化されているか確認
python --version  # Python 3.11.9 と表示されるはず

# 実際のPython実行ファイルのパスを確認（最も確実）
python -c "import sys; print(sys.executable)"
# 出力例: /home/mm/.pyenv/versions/focus-alert-311/bin/python

# 注意: which python が ~/.pyenv/shims/python を返すのは正常です
# pyenvはshimsという仕組みでPythonを管理しているためです
```

#### 0.6 仮想環境への依存パッケージのインストール

仮想環境に必要なパッケージをインストールします：

```bash
# 仮想環境が有効化されていることを確認
python --version

# pipを最新版にアップグレード
pip install --upgrade pip

# 依存パッケージをインストール
pip install -r requirements.txt
```

インストールが完了したら、動作確認：

```bash
python -c "import mediapipe; print('MediaPipe OK')"
python -c "import cv2; print('OpenCV OK')"
python -c "import zmq; print('ZMQ OK')"
```

#### 0.7 環境設定の確認

最後に、環境設定が正しく行われているか確認します：

```bash
# システムPython（Picamera2用）
python3 --version
python3 -c "from picamera2 import Picamera2; print('System Python: OK')"

# pyenv仮想環境（MediaPipe用）
python --version
python -c "import mediapipe; print('pyenv Python: OK')"
```

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

### Python環境の問題

#### システムPythonでPicamera2がインポートできない

```bash
# Picamera2がインストールされているか確認
python3 -c "from picamera2 import Picamera2"

# インストールされていない場合
sudo apt-get install -y python3-picamera2
```

#### pyenvが認識されない

```bash
# pyenvのパスが正しく設定されているか確認
echo $PYENV_ROOT
which pyenv

# 設定ファイルを再読み込み
source ~/.bashrc

# pyenvの再インストールが必要な場合
curl https://pyenv.run | bash
```

#### 仮想環境が有効化されない

```bash
# プロジェクトディレクトリで確認
cd ~/Focus_Alert
pyenv versions
pyenv local focus-alert-311

# 仮想環境が正しく設定されているか確認
python --version  # Python 3.11.9 と表示されるはず

# 実際のPython実行ファイルのパスを確認（最も確実）
python -c "import sys; print(sys.executable)"
# 出力例: /home/mm/.pyenv/versions/focus-alert-311/bin/python

# 注意: which python が ~/.pyenv/shims/python を返すのは正常です
# pyenvはshimsという仕組みでPythonを管理しているためです
```

#### MediaPipeがインポートできない

```bash
# 仮想環境が有効化されているか確認
python --version

# 仮想環境を再作成する場合
pyenv virtualenv-delete focus-alert-311
pyenv virtualenv 3.11.9 focus-alert-311
pyenv local focus-alert-311
pip install -r requirements.txt
```

#### 依存パッケージのインストールエラー

```bash
# pipを最新版にアップグレード
pip install --upgrade pip

# 個別にインストールしてエラーを確認
pip install mediapipe
pip install opencv-python
pip install numpy
pip install zmq
```

### カメラが認識されない

```bash
# カメラの確認
libcamera-hello --list-cameras

# カメラのテスト
libcamera-hello

# カメラが認識されない場合、接続を確認
# - カメラケーブルが正しく接続されているか
# - カメラが有効化されているか（raspi-configで確認）
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

