# PCでの動作確認手順

このドキュメントでは、PC上でFocus Alertシステムを動作確認する手順を説明します。

## 前提条件

- Python 3.10 または 3.11 がインストールされていること
- ウェブカメラが接続されていること
- Windows/Mac/Linux のいずれか

## セットアップ手順

### 1. プロジェクトディレクトリに移動

```bash
cd Focus_Alert
```

### 2. 仮想環境の作成

#### Windows (PowerShell)
```powershell
# Python 3.10または3.11を使用
python -m venv venv

# 仮想環境を有効化
.\venv\Scripts\Activate.ps1
```

#### Windows (コマンドプロンプト)
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

#### Mac/Linux
```bash
# Python 3.10または3.11を使用
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. カメラの確認

カメラが正常に動作するか確認します。

#### Windows
- デバイスマネージャーでカメラデバイスを確認
- カメラアプリで動作確認

#### Mac/Linux
```bash
# カメラデバイスの確認（Linux）
ls /dev/video*

# または
v4l2-ctl --list-devices
```

### 5. アプリケーションの起動

#### 基本的な起動（ログなし）
```bash
python src/app.py --cam 0 --width 640 --height 480
```

#### ログを記録して起動
```bash
python src/app.py --cam 0 --width 640 --height 480 --log logs/pc_test.csv
```

#### アラートを無効化して起動（計測のみ）
```bash
python src/app.py --cam 0 --width 640 --height 480 --alert-mode off --log logs/pc_test.csv
```

#### カメラ番号を変更する場合
複数のカメラがある場合、`--cam`オプションでカメラ番号を指定できます。
```bash
# カメラ1を使用
python src/app.py --cam 1 --width 640 --height 480
```

#### 解像度を変更する場合
```bash
python src/app.py --cam 0 --width 1280 --height 720
```

### 6. 動作確認

起動後、以下の点を確認してください：

1. **カメラ映像の表示**: 画面にカメラ映像が表示されること
2. **顔検出**: 顔が検出されると「Face: OK」と表示されること
3. **虹彩検出**: 虹彩が検出されると「Iris: OK」と表示されること
4. **まばたき検出**: まばたきすると「Blinks」の数が増えること
5. **視線検出**: 視線を動かすと「Gaze」の値が変化すること
6. **ボタン操作**: 画面下部のボタンがタッチ/クリックで反応すること

### 7. トラブルシューティング

#### カメラが開けない
- カメラが他のアプリケーションで使用されていないか確認
- カメラ番号を変更してみる（`--cam 1`など）
- カメラの権限を確認（Mac/Linuxでは`sudo`が必要な場合があります）

#### MediaPipeがエラーを出す
- 仮想環境が正しく有効化されているか確認
- `pip install --upgrade mediapipe`で再インストール

#### ウィンドウが表示されない
- ディスプレイの設定を確認
- `--display`オプションが有効になっているか確認

#### パフォーマンスが低い
- 解像度を下げる（`--width 320 --height 240`）
- 他のアプリケーションを閉じる

### 8. 終了方法

- キーボードで`q`キーを押す
- または、画面下部の「Quit」ボタンをクリック/タッチ

## よく使うコマンド例

```bash
# 基本的な起動
python src/app.py --cam 0 --width 640 --height 480 --log logs/test.csv

# 高解像度で起動
python src/app.py --cam 0 --width 1280 --height 720 --log logs/hd_test.csv

# アラート無効で計測のみ
python src/app.py --cam 0 --width 640 --height 480 --alert-mode off --log logs/measure.csv

# セッション情報を付けて記録
python src/app.py --cam 0 --width 640 --height 480 --log logs/session1.csv --session S001 --participant P01 --task typing
```

