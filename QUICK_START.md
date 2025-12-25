# クイックスタートガイド

## PCでの動作確認（全手順）

### ステップ1: プロジェクトディレクトリに移動

```bash
cd Focus_Alert
```

### ステップ2: 仮想環境の作成

#### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Windows (コマンドプロンプト)
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

#### Mac/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### ステップ3: 依存パッケージのインストール

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### ステップ4: アプリケーションの起動

#### 方法1: コマンドラインから起動

```bash
# 基本的な起動（ログなし）
python src/app.py --cam 0 --width 640 --height 480

# ログを記録して起動
python src/app.py --cam 0 --width 640 --height 480 --log logs/pc_test.csv
```

#### 方法2: 起動スクリプトを使用

**Windows:**
- `scripts\start_focus_alert_pc.bat` をダブルクリック

**Mac/Linux:**
```bash
chmod +x scripts/start_focus_alert_pc.sh
./scripts/start_focus_alert_pc.sh
```

### ステップ5: 動作確認

1. カメラ映像が表示されること
2. 顔が検出されると「Face: OK」と表示されること
3. まばたきすると「Blinks」の数が増えること
4. 画面下部のボタンがクリック/タッチで反応すること

### ステップ6: 終了

- キーボードで`q`キーを押す
- または、画面下部の「Quit」ボタンをクリック

---

## Raspberry Pi 5でのワンタッチ起動

### ステップ1: デスクトップショートカットの作成

```bash
# デスクトップにショートカットファイルを作成
nano ~/Desktop/focus_alert.desktop
```

以下の内容を記述（パスを実際のプロジェクトパスに変更）：

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

### ステップ2: 実行権限の付与

```bash
chmod +x ~/Desktop/focus_alert.desktop
chmod +x ~/Focus_Alert/scripts/start_focus_alert.sh
```

### ステップ3: 起動

デスクトップの「Focus Alert」アイコンをダブルクリック

または、ターミナルから：

```bash
~/Focus_Alert/scripts/start_focus_alert.sh
```

### ステップ4: 停止

- アプリ内で「Quit」ボタンをタッチ
- または、ターミナルで`Ctrl+C`

---

## トラブルシューティング

### カメラが開けない
- カメラが他のアプリケーションで使用されていないか確認
- カメラ番号を変更（`--cam 1`など）

### 仮想環境が認識されない
- 仮想環境が正しく有効化されているか確認
- `which python`でPythonのパスを確認

### パッケージのインストールエラー
- `pip install --upgrade pip`でpipを最新化
- Python 3.10または3.11を使用しているか確認

---

詳細な情報は以下を参照：
- [PCセットアップガイド](docs/PC_SETUP.md)
- [Raspberry Piセットアップガイド](docs/RASPBERRY_PI_SETUP.md)

