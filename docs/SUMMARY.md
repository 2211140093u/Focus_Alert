# セットアップ手順まとめ

## PCでの動作確認

### 最短手順（3ステップ）

1. **仮想環境を作成・有効化**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **依存パッケージをインストール**
   ```bash
   pip install -r requirements.txt
   ```

3. **アプリを起動**
   ```bash
   python src/app.py --cam 0 --width 640 --height 480 --log logs/test.csv
   ```

詳細: [PCセットアップガイド](PC_SETUP.md)

---

## Raspberry Pi 5でのワンタッチ起動

### 最短手順（2ステップ）

1. **デスクトップショートカットを作成**
   ```bash
   # scripts/focus_alert.desktop を ~/Desktop/ にコピー
   cp scripts/focus_alert.desktop ~/Desktop/
   chmod +x ~/Desktop/focus_alert.desktop
   ```

2. **デスクトップのアイコンをダブルクリック**

詳細: [Raspberry Piセットアップガイド](RASPBERRY_PI_SETUP.md)

---

## ファイル構成

### 起動スクリプト

- **PC用（Windows）**: `scripts/start_focus_alert_pc.bat`
- **PC用（Mac/Linux）**: `scripts/start_focus_alert_pc.sh`
- **Raspberry Pi用**: `scripts/start_focus_alert.sh`
- **停止用**: `scripts/stop_focus_alert.sh`

### ドキュメント

- **クイックスタート**: `QUICK_START.md` - 最短手順
- **PCセットアップ**: `docs/PC_SETUP.md` - PCでの詳細手順
- **Raspberry Piセットアップ**: `docs/RASPBERRY_PI_SETUP.md` - Raspberry Piでの詳細手順
- **アイコン設定**: `docs/INSTALL_ICON.md` - アイコンの設定方法

---

## よくある質問

### Q: PCでカメラが認識されない
A: カメラ番号を変更（`--cam 1`など）してみてください。詳細は[PCセットアップガイド](PC_SETUP.md)のトラブルシューティングを参照。

### Q: Raspberry Piで起動しない
A: スクリプトに実行権限があるか確認してください：
```bash
chmod +x ~/Focus_Alert/scripts/start_focus_alert.sh
```

### Q: ログファイルはどこに保存される？
A: `logs/`ディレクトリに保存されます。ファイル名にはタイムスタンプが含まれます。

### Q: 自動起動したい
A: systemdサービスまたはautostartを使用します。詳細は[Raspberry Piセットアップガイド](RASPBERRY_PI_SETUP.md)を参照。

---

## 次のステップ

1. 動作確認が完了したら、実際の計測を開始
2. ログファイルを分析（`scripts/report.py`を使用）
3. 必要に応じてパラメータを調整

