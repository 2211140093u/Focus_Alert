# Focus Alert

まばたき（Blink）と視線（Gaze）に基づいて注意散漫の兆候を検知し、画面表示とCSV記録を行うシステム。

## 特長（Features）

- EAR（Eye Aspect Ratio）によるまばたき検出（開眼基準の適応: EWMA、相対しきい値、瞬目カウント、長時間閉眼の検出）
- 虹彩ランドマークを用いた視線オフセット（平滑化、中心キャリブレーション、逸脱レベルEMA）
- ヒステリシス/クールダウン付きのリスクスコアと画面オーバーレイ表示
- CSV記録（frame/event/meta）、実験用ホットキー、解析ノートブック（AUC・F1・遅延）

## Setup

1) Python 3.10–3.11 仮想環境を作成・有効化
2) 依存をインストール
```
pip install -r requirements.txt
```

## Quick Start

- 基本起動（表示・記録）
```
python src/app.py --cam 0 --width 640 --height 480 --log logs/run.csv
```

- カメラや解像度
```
python src/app.py --cam 0 --width 640 --height 480
```

- アラート非表示・記録のみ（可視化目的）
```
python src/app.py --alert-mode off --log logs/work.csv
```

## CLI Options（主要）

- `--cam` カメラ番号（既定 0）
- `--width --height` 解像度（既定 640x480）
- `--log` CSV出力パス（例: logs/run.csv）
- `--session --participant --task` 実験メタ情報
- `--calib-seconds` 起動直後のキャリブレーション時間（既定 60）
- `--alert-mode` on | off（offで画面のアラート文言を非表示、ログ/スコア計算は維持）

## Hotkeys（実行中）

- `s` ブロック開始（block_id採番）
- `e` ブロック終了
- `m` 任意マーカー（注釈）
- `d` 注意散漫トグル（start/endをイベント記録）
- `c` 視線センター再キャリブレーション（中央注視で押下）
- `q` 終了

## Overlay（画面左上のパネル）

- Face/Iris 検出状態
- EAR（現在/基準/閾値）、Blink数、長瞬目フラグ
- Gaze（値/閾値/バイアス/オフレベル）
- FPS、Risk、アラート表示

## Personalization（本バージョンでは未使用）

- 今回のバージョンでは、個人に合わせた学習やモデルの保存/読込はおこなわない
- セッション内の短期安定化（EARのEWMA、視線の中心キャリブレーション）だけを使用する

## Logging（CSV）

- 行種別: meta / event / frame
- 代表カラム: `ts,row_type,session,participant,task,phase,block_id,ear,ear_base,ear_thr,blink_count,is_closed,long_close,gaze,gaze_thr,gaze_bias,gaze_offlvl,risk,alert,event,info`
- `event`: `block_start/end`, `marker`, `distractor_start/end`, `calibrate_center` など

## Analysis Notebook（本バージョンでは未使用）

- `notebooks/analysis.ipynb`
  - ログ読み込みと整形
  - 可視化（Risk, EAR, Gaze, Alert, distractor）
  - 混同行列・Precision/Recall/F1・ROC-AUC
  - 検出遅延（distractor_start → 最初のアラートまで）
- 使い方: 先頭セルの `LOG_PATHS` にCSVを指定し、全セル実行

## Reports

- 計測したcsvデータをグラフ化しhtmlファイルを作成する
- 使用方法
```
python scripts/report.py --log logs/pc_test.csv --out reports/report.html
```

## Tips

- distractor区間を擬似ラベルとして感度/特異度/遅延を算出
- もしくは課題スコア（反応時間/正答率）の悪化オンセットを自動算出してラベル化

## Troubleshooting

- アラートが出ない: 長瞬目（>0.5s）や視線を一定方向に1–2秒維持して確認。必要なら `fusion.py` の `self.hi` を下げる。
- Gazeがズレる: 画面中央注視で `c` を押してバイアス補正。照明や顔角度を調整。
- IrisがNOになる: 眼鏡の反射や暗さが原因。照明を明るく、顔を近めに、角度を調整。

## Raspberry Pi 5（後段移植メモ）

- Pi OS 64-bit、libcamera有効化、mediapipe/opencvをインストール
- DSIタッチは同梱手順に従いセットアップ
- パフォーマンス: 480p推奨、Poseは後続拡張時にサブサンプリング