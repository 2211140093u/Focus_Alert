# Raspberry Pi 5での完全セットアップガイド

このドキュメントでは、Raspberry Pi 5でFocus Alertシステムを完全にセットアップする手順を、環境設定からライブラリ導入まで詳しく説明します。

## 前提条件

### ハードウェア
- Raspberry Pi 5（またはRaspberry Pi 4）
- Raspberry Pi OS（最新版推奨）
- Raspberry Pi Camera V3 wide（または互換カメラ）
- 3.5インチタッチモニタ（320×480、または480×320横長モニタ）
- microSDカード（32GB以上推奨）
- 電源アダプタ（5V 3A以上推奨）

### ソフトウェア環境
**注意**: このシステムは二重プロセス構成のため、以下のPython環境が必要です：
- **システムPython 3.13**: Picamera2用（セットアップ手順0.2でインストール）
- **pyenv Python 3.11**: MediaPipe用（セットアップ手順0.3-0.6でセットアップ）

初回セットアップ時は、**セクション0（Python環境のセットアップ）**から順番に実行してください。

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

# 追加の依存パッケージ（必要に応じて）
sudo apt-get install -y python3-pil python3-picamera2[qt]
```

インストールが完了したら、動作確認：

```bash
# Picamera2のインポート確認
python3 -c "from picamera2 import Picamera2; print('Picamera2 OK')"

# NumPyの確認
python3 -c "import numpy; print(f'NumPy version: {numpy.__version__}')"

# OpenCVの確認
python3 -c "import cv2; print(f'OpenCV version: {cv2.__version__}')"

# ZMQの確認
python3 -c "import zmq; print(f'ZMQ version: {zmq.zmq_version()}')"
```

**トラブルシューティング:**

Picamera2がインストールできない場合：

```bash
# パッケージリストを更新
sudo apt-get update

# 古いパッケージを削除して再インストール
sudo apt-get remove --purge python3-picamera2
sudo apt-get install -y python3-picamera2

# それでも解決しない場合、ソースからビルド
# （詳細は公式ドキュメントを参照）
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
# プロジェクトディレクトリに移動
cd ~/Focus_Alert

# 仮想環境が有効化されていることを確認
python --version  # Python 3.11.9 と表示されるはず

# pipを最新版にアップグレード
pip install --upgrade pip setuptools wheel

# 依存パッケージをインストール（時間がかかります）
pip install -r requirements.txt
```

**インストール時間の目安:**
- MediaPipe: 5-10分
- OpenCV: 3-5分
- その他: 1-2分
- **合計: 約10-20分**

インストールが完了したら、動作確認：

```bash
# 各ライブラリのインポート確認
python -c "import mediapipe; print(f'MediaPipe OK: {mediapipe.__version__}')"
python -c "import cv2; print(f'OpenCV OK: {cv2.__version__}')"
python -c "import zmq; print(f'ZMQ OK: {zmq.zmq_version()}')"
python -c "import numpy; print(f'NumPy OK: {numpy.__version__}')"
python -c "import pandas; print(f'Pandas OK: {pandas.__version__}')"
python -c "import matplotlib; print(f'Matplotlib OK: {matplotlib.__version__}')"
```

**トラブルシューティング:**

**MediaPipeのインストールエラー:**

```bash
# メモリ不足の場合、スワップを増やす
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=100 を CONF_SWAPSIZE=2048 に変更
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# 個別にインストールしてエラーを確認
pip install mediapipe==0.10.14
```

**OpenCVのインストールエラー:**

```bash
# システムのOpenCVライブラリを確認
sudo apt-get install -y libopencv-dev

# pipで再インストール
pip install --upgrade opencv-python==4.10.0.84
```

**NumPyのインストールエラー:**

```bash
# システムのNumPyライブラリを確認
sudo apt-get install -y python3-numpy

# pipで再インストール
pip install --upgrade "numpy>=1.24,<2.0"
```

**メモリ不足エラー:**

```bash
# 一時ファイルを削除
pip cache purge

# 個別にインストール（メモリ使用量を減らす）
pip install mediapipe==0.10.14 --no-cache-dir
pip install opencv-python==4.10.0.84 --no-cache-dir
pip install numpy --no-cache-dir
# ... 残りも同様に
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

### 1. システムの基本設定

#### 1.1 Raspberry Pi OSの初期設定

まず、Raspberry Pi OSが最新の状態になっているか確認します：

```bash
# システムを最新の状態に更新
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get dist-upgrade -y

# 再起動（必要に応じて）
sudo reboot
```

#### 1.2 カメラの有効化

Raspberry Pi Cameraを使用するため、カメラインターフェースを有効化します：

```bash
# raspi-configを起動
sudo raspi-config

# 以下のメニューを選択：
# 3 Interface Options → I1 Camera → Enable
```

または、コマンドラインから直接有効化：

```bash
# カメラインターフェースを有効化
sudo raspi-config nonint do_camera 0

# 再起動
sudo reboot
```

再起動後、カメラが認識されているか確認：

```bash
# カメラの一覧を表示
libcamera-hello --list-cameras

# カメラのテスト（5秒間表示）
libcamera-hello -t 5000
```

#### 1.3 ディスプレイの設定（必要に応じて）

3.5インチタッチモニタを使用する場合、ドライバのインストールが必要な場合があります：

```bash
# ディスプレイの設定（メーカー提供のドライバに従う）
# 例：Waveshare 3.5インチタッチモニタの場合
# メーカーの公式ドキュメントを参照してください
```

#### 1.4 必要なシステムパッケージのインストール

基本的な開発ツールとライブラリをインストールします：

```bash
# 基本的な開発ツール
sudo apt-get install -y build-essential git curl wget

# Python開発用パッケージ
sudo apt-get install -y python3-dev python3-pip python3-venv

# 画像処理ライブラリ（OpenCV用）
sudo apt-get install -y libopencv-dev python3-opencv

# その他の必要なライブラリ
sudo apt-get install -y libjpeg-dev libpng-dev libtiff-dev
sudo apt-get install -y libavcodec-dev libavformat-dev libswscale-dev
sudo apt-get install -y libv4l-dev v4l-utils
```

### 2. プロジェクトの取得と配置

#### 2.1 プロジェクトの取得

プロジェクトをホームディレクトリに配置します：

**方法1: Gitを使用する場合（推奨）**

```bash
cd ~
git clone <リポジトリURL> Focus_Alert
cd Focus_Alert
```

**方法2: ファイルを直接コピーする場合**

```bash
cd ~
# USBメモリやネットワーク経由でプロジェクトファイルをコピー
# 例：USBメモリからコピー
cp -r /media/pi/USB/Focus_Alert ~/Focus_Alert
cd ~/Focus_Alert
```

#### 2.2 プロジェクトディレクトリの確認

```bash
# プロジェクトの構造を確認
ls -la ~/Focus_Alert

# 以下のディレクトリが存在することを確認：
# - src/          (ソースコード)
# - scripts/      (起動スクリプト)
# - docs/         (ドキュメント)
# - requirements.txt  (依存パッケージリスト)
```

### 3. デスクトップショートカットの作成

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

### 4. 起動スクリプトの確認

`scripts/start_focus_alert.sh`が実行可能であることを確認：

```bash
chmod +x ~/Focus_Alert/scripts/start_focus_alert.sh
```

### 5. 自動起動の設定（オプション）

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

### 6. タッチスクリーンの設定（必要に応じて）

3.5インチタッチモニタが正しく認識されているか確認：

```bash
# タッチデバイスの確認
xinput list

# タッチスクリーンのキャリブレーション（必要に応じて）
# xinput_calibrator をインストール
sudo apt-get install xinput-calibrator
```

### 7. 動作確認

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

### 8. 停止方法

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
pip install --upgrade pip setuptools wheel

# 個別にインストールしてエラーを確認
pip install mediapipe==0.10.14
pip install opencv-python==4.10.0.84
pip install "numpy>=1.24,<2.0"
pip install pyzmq>=25

# エラーメッセージを確認して対処
# メモリ不足の場合は、スワップを増やす（上記参照）
# コンパイルエラーの場合は、必要な開発ツールをインストール
sudo apt-get install -y build-essential python3-dev
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
# 最新のログファイルを確認
ls -lt ~/Focus_Alert/logs/

# アプリのログ（最新のものを表示）
tail -f ~/Focus_Alert/logs/app_$(ls -t ~/Focus_Alert/logs/app_*.log | head -1 | xargs basename)

# カメラプロキシのログ（最新のものを表示）
tail -f ~/Focus_Alert/logs/cam_proxy_$(ls -t ~/Focus_Alert/logs/cam_proxy_*.log | head -1 | xargs basename)

# または、すべてのログを確認
tail -f ~/Focus_Alert/logs/*.log
```

### プロジェクトファイルの権限エラー

```bash
# プロジェクトディレクトリの権限を確認
ls -la ~/Focus_Alert

# 実行権限を付与
chmod +x ~/Focus_Alert/scripts/*.sh
chmod +x ~/Focus_Alert/scripts/*.py

# ログディレクトリの作成と権限設定
mkdir -p ~/Focus_Alert/logs
chmod 755 ~/Focus_Alert/logs
```

### ディスプレイの問題

```bash
# ディスプレイの解像度を確認
xrandr

# ディスプレイの設定を変更（必要に応じて）
# 例：480x320に設定（モニタが対応している場合）
# xrandr --output HDMI-1 --mode 480x320

# タッチスクリーンのキャリブレーション
sudo apt-get install -y xinput-calibrator
xinput_calibrator
```

### カメラの問題

```bash
# カメラが認識されているか確認
libcamera-hello --list-cameras

# カメラのテスト
libcamera-hello -t 5000

# カメラが認識されない場合
# 1. カメラケーブルの接続を確認
# 2. raspi-configでカメラを有効化
sudo raspi-config
# 3. 再起動
sudo reboot

# カメラの権限エラー
# ユーザーをvideoグループに追加
sudo usermod -a -G video $USER
# 再ログインが必要
```

### Input/output error（I/Oエラー）

`Input/output error`が発生した場合、SDカードやファイルシステムの問題の可能性があります。

#### 診断手順

```bash
# 1. システムログを確認
dmesg | tail -50
journalctl -xe | tail -50

# 2. ディスクの状態を確認
df -h
sudo fsck -n /dev/mmcblk0p1  # 読み取り専用でチェック（rootパーティション）
sudo fsck -n /dev/mmcblk0p2  # 読み取り専用でチェック（メインパーティション）

# 3. ディスクの健康状態を確認（SMART情報）
sudo smartctl -a /dev/mmcblk0  # 利用可能な場合

# 4. メモリの状態を確認
free -h
```

#### 対処方法

**方法1: ファイルシステムの修復（推奨）**

```bash
# システムを読み取り専用モードで再起動
sudo reboot

# 再起動後、シングルユーザーモードで起動
# 起動時にShiftキーを押して、recovery modeを選択
# または、起動時にカーネルパラメータに init=/bin/bash を追加

# ファイルシステムを修復
sudo fsck -y /dev/mmcblk0p1
sudo fsck -y /dev/mmcblk0p2

# 再起動
sudo reboot
```

**方法2: 一時的な回避策（スクリプトの修正）**

I/Oエラーが特定のコマンド（sleepなど）で発生する場合、スクリプトを修正：

```bash
# スクリプトのバックアップ
cp ~/Focus_Alert/scripts/start_focus_alert.sh ~/Focus_Alert/scripts/start_focus_alert.sh.bak

# sleepコマンドの代わりに、より軽量な方法を使用
# または、エラーハンドリングを追加
```

**方法3: SDカードの交換（根本的な解決）**

I/Oエラーが頻繁に発生する場合、SDカードの不良が考えられます：

```bash
# 1. 現在のシステムをバックアップ
sudo dd if=/dev/mmcblk0 of=/tmp/backup.img bs=4M status=progress

# 2. 新しいSDカードにシステムをコピー
# （別のPCで実行）
# sudo dd if=backup.img of=/dev/sdX bs=4M status=progress

# 3. 新しいSDカードで起動して確認
```

**方法4: 一時的な回避策（プロセス監視の変更）**

`sleep`コマンドでI/Oエラーが発生する場合、スクリプトを修正：

```bash
# start_focus_alert.shの139行目付近を修正
# 変更前:
#     sleep 1

# 変更後（エラーハンドリングを追加）:
#     sleep 1 || break  # エラー時はループを抜ける
# または
#     /bin/sleep 1 2>/dev/null || break
```

**方法5: システムの再インストール（最終手段）**

上記の方法で解決しない場合：

1. 新しいSDカードにRaspberry Pi OSをインストール
2. プロジェクトファイルをバックアップから復元
3. 環境を再セットアップ

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

