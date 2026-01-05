# Focus Alert

まばたき（Blink）と視線（Gaze）に基づいて注意散漫の兆候を検知し、画面表示とCSV記録を行うシステム。

## 特長（Features）

- EAR（Eye Aspect Ratio）によるまばたき検出（開眼基準の適応: EWMA、相対しきい値、瞬目カウント、長時間閉眼の検出）
- 虹彩ランドマークを用いた視線オフセット（平滑化、中心キャリブレーション、逸脱レベルEMA）
- ヒステリシス/クールダウン付きの集中度スコアと画面オーバーレイ表示
- CSV記録（frame/event/meta）、実験用ホットキー、解析ノートブック（AUC・F1・遅延）
- 3.5インチタッチモニタ（320×480）対応の最適化されたUI
- リアルタイムカメラ状態表示

## クイックスタート

**最短手順は [QUICK_START.md](QUICK_START.md) を参照してください。**

### PCでの動作確認

詳細は [PCセットアップガイド](docs/PC_SETUP.md) を参照してください。

1. 仮想環境を作成：
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 依存パッケージをインストール：
```bash
pip install -r requirements.txt
```

3. アプリを起動：
```bash
python src/app.py --cam 0 --width 640 --height 480 --log logs/test.csv
```

または、起動スクリプトを使用：
- Windows: `scripts\start_focus_alert_pc.bat` をダブルクリック
- Mac/Linux: `./scripts/start_focus_alert_pc.sh`

### Raspberry Pi 5での起動

詳細は [Raspberry Piセットアップガイド](docs/RASPBERRY_PI_SETUP.md) を参照してください。

1. デスクトップショートカットを作成（ワンタッチ起動）
2. または、ターミナルから：
```bash
./scripts/start_focus_alert.sh
```

## システム構成

### PC環境
- Python 3.10-3.11
- OpenCV（ウェブカメラ対応）
- MediaPipe（顔・虹彩検出）

### Raspberry Pi 5環境
- System Python 3.13（Picamera2用）
- pyenv Python 3.11（アプリ用）
- Raspberry Pi Camera V3 wide
- 3.5インチタッチモニタ（320×480）
- 二重プロセス構成（ZMQ経由で通信）

## CLI Options（主要）

- `--cam` カメラ番号（既定 0）
- `--width --height` 解像度（既定 640x480）
- `--log` CSV出力パス（例: logs/run.csv）
- `--backend` カメラバックエンド（auto/opencv/picamera2/zmq）
- `--alert-mode` on | off（offで画面のアラート文言を非表示）
- `--session --participant --task` 実験メタ情報

## 操作方法

### キーボード操作
- `s` ブロック開始（block_id採番）
- `e` ブロック終了
- `m` 任意マーカー（注釈）
- `d` 注意散漫トグル（start/endをイベント記録）
- `c` 視線センター再キャリブレーション（中央注視で押下）
- `q` 終了

### タッチ操作（Raspberry Pi）
- 画面下部のボタンをタッチして操作
- Start/End/Marker/Distract/Calib/Quit

## 画面表示

### 情報パネル（左上）
- カメラ状態（接続・FPS）
- Face/Iris 検出状態
- EAR（現在値）、Blinks（まばたき回数）
- Gaze（視線方向・逸脱状態）
- Concentration（集中度スコア）

### ボタン（下部）
- Start: ブロック開始
- End: ブロック終了
- Mark: マーカー
- Dist: 注意散漫トグル
- Calib: 視線キャリブレーション
- Quit: 終了

## Logging（CSV）

- 行種別: meta / event / frame
- 代表カラム: `ts,row_type,session,participant,task,phase,block_id,ear,ear_base,ear_thr,blink_count,is_closed,long_close,gaze,gaze_thr,gaze_bias,gaze_offlvl,risk,concentration,alert,event,info`
- `event`: `block_start/end`, `marker`, `distractor_start/end`, `calibrate_center` など

## Reports

計測したCSVデータをグラフ化しHTMLファイルを作成：

```bash
python scripts/report.py --log logs/pc_test.csv --out reports/report.html
```

## トラブルシューティング

### カメラが開けない
- カメラが他のアプリケーションで使用されていないか確認
- カメラ番号を変更（`--cam 1`など）
- 権限を確認（Mac/Linuxでは`sudo`が必要な場合があります）

### MediaPipeがエラーを出す
- 仮想環境が正しく有効化されているか確認
- `pip install --upgrade mediapipe`で再インストール

### アラートが出ない
- 長瞬目（>0.5s）や視線を一定方向に1–2秒維持して確認
- 必要なら `fusion.py` の `self.hi` を下げる

### Gazeがズレる
- 画面中央注視で `c` を押してバイアス補正
- 照明や顔角度を調整

### IrisがNOになる
- 眼鏡の反射や暗さが原因
- 照明を明るく、顔を近めに、角度を調整

## ドキュメント

- [クイックスタート](QUICK_START.md) - 最短手順（推奨）
- [GUI操作ガイド](docs/GUI_GUIDE.md) - GUI版アプリケーションの操作説明（Raspberry Pi用）
- [仮想キーボード操作ガイド](docs/VIRTUAL_KEYBOARD.md) - メモ入力用仮想キーボードの使い方
- [レポートビューア操作ガイド](docs/REPORT_VIEWER.md) - アプリ内レポート表示機能の使い方
- [PCセットアップガイド](docs/PC_SETUP.md) - PCでの詳細な動作確認手順
- [Raspberry Piセットアップガイド](docs/RASPBERRY_PI_SETUP.md) - Raspberry Piでのワンタッチ起動設定
- [レポート作成ガイド](docs/REPORT_GUIDE.md) - レポートの作成方法と記録項目の説明
- [EARパラメータの詳細説明](docs/EAR_PARAMETERS.md) - EAR閾値と基準値の調整方法
- [集中度スコアの判定方法](docs/RISK_SCORE.md) - 集中度スコアの計算と判定ロジック
- [よくある質問（FAQ）](docs/FAQ.md) - よくある質問と回答
- [質問への回答まとめ](docs/ANSWERS.md) - 詳細な質問への回答
- [セットアップ手順まとめ](docs/SUMMARY.md) - 全手順の概要
- [アイコン設定ガイド](docs/INSTALL_ICON.md) - デスクトップアイコンの設定方法

## License

（ライセンス情報を記載）
