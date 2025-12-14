# Focus Alert

Blink + Gaze based attention drop detector with on-screen alerts, logging, and per-user personalization. Windows prototype first; later runs on Raspberry Pi 5 (DSI touchscreen).

## Features

- Blink detection via EAR with adaptive open-eye baseline (EWMA), relative threshold, blink counting, long-close detection
- Gaze horizontal offset using iris landmarks, smoothing, center calibration, off-level EMA
- Fusion risk score with hysteresis/cooldown and on-screen overlay
- CSV logging (frame + event + meta), experiment hotkeys, analysis notebook（AUC/F1/遅延）
- Personalization with safety guards（学習停止条件・安定フレーム・非対称EWMA）
- セッション境界保存/反映（eval中は完全固定）

## Setup

1) Python 3.10–3.11 仮想環境を作成・有効化
2) 依存をインストール
```
pip install -r requirements.txt
```

## Quick Start

- 学習（個人化）セッション（終了時のみ保存）
```
python src/app.py --phase train --learning on --model-save models/P01.json \
  --session S01 --participant P01 --task cpt --log logs/P01_train.csv
```

- 既存モデルを読み込んで評価（固定挙動）
```
python src/app.py --phase eval --model-load models/P01.json \
  --session S01 --participant P01 --task cpt --log logs/P01_eval.csv
```

- カメラや解像度
```
python src/app.py --cam 0 --width 640 --height 480
```

- アラート非表示・記録のみ（可視化目的）
```
python src/app.py --alert-mode off --learning off --log logs/P01_work.csv
```

## CLI Options（主要）

- `--cam` カメラ番号（既定 0）
- `--width --height` 解像度（既定 640x480）
- `--log` CSV出力パス（例: logs/run.csv）
- `--session --participant --task` 実験メタ情報
- `--phase` train | eval（trainのみ学習。evalは完全固定）
- `--calib-seconds` 起動直後のキャリブレーション時間（既定 60）
- `--model-save` セッション終了時に保存するモデルパス
- `--model-load` 起動時に読み込むモデルパス
- `--learning` on | off（既定 off。offの場合は学習せず、モデル読込/保存も無効）
- `--alert-mode` on | off（offで画面のアラート文言を非表示、ログ/スコア計算は維持）

## Hotkeys（実行中）

- `s` ブロック開始（block_id採番）
- `e` ブロック終了
- `m` 任意マーカー（注釈）
- `d` 注意散漫トグル（start/endをイベント記録）
- `c` 視線センター再キャリブレーション（中央注視で押下）
- `q` 終了（train時のみ保存、evalは保存なし）

## Overlay（画面左上のパネル）

- Face/Iris 検出状態
- EAR（現在/基準/閾値）、Blink数、長瞬目フラグ
- Gaze（値/閾値/バイアス/オフレベル）
- FPS、Risk、アラート表示

## Personalization（学習の安全策）

- trainのみ学習。以下の条件では学習停止:
  - 顔未検出／閉眼中／大きな視線逸れ／アラート中
- 連続安定フレーム（既定10）を満たした時だけ更新
- EAR基準は非対称EWMA（開眼側は早め、閉眼側は非常に遅い）
- eval中は完全固定（Blink側の基準適応も停止）
- セッション境界保存/反映：保存は終了時のみ、反映は起動時の`--model-load`時のみ

## Logging（CSV）

- 行種別: meta / event / frame
- 代表カラム: `ts,row_type,session,participant,task,phase,block_id,ear,ear_base,ear_thr,blink_count,is_closed,long_close,gaze,gaze_thr,gaze_bias,gaze_offlvl,risk,alert,event,info`
- `event`: `block_start/end`, `marker`, `distractor_start/end`, `calibrate_center` など

## Analysis Notebook

- `notebooks/analysis.ipynb`
  - ログ読み込みと整形
  - 可視化（Risk, EAR, Gaze, Alert, distractor）
  - 混同行列・Precision/Recall/F1・ROC-AUC
  - 検出遅延（distractor_start → 最初のアラートまで）
- 使い方: 先頭セルの `LOG_PATHS` にCSVを指定し、全セル実行

## Evaluation Tips（卒研向け）

- distractor区間を擬似ラベルとして感度/特異度/遅延を算出
- もしくは課題スコア（反応時間/正答率）の悪化オンセットを自動算出してラベル化
- 学習なし vs 安全策付き学習 vs 事前基準合わせ後 の比較で有意な差を検討

## Troubleshooting

- アラートが出ない: 長瞬目（>0.5s）や視線を一定方向に1–2秒維持して確認。必要なら `fusion.py` の `self.hi` を下げる。
- Gazeがズレる: 画面中央注視で `c` を押してバイアス補正。照明や顔角度を調整。
- IrisがNOになる: 眼鏡の反射や暗さが原因。照明を明るく、顔を近めに、角度を調整。
- 初回モデル読み込み失敗: 正常（未作成）。train終了時に自動保存、その後evalでロード。

## Raspberry Pi 5（後段移植メモ）

- Pi OS 64-bit、libcamera有効化、mediapipe/opencvをインストール
- DSIタッチは同梱手順に従いセットアップ
- パフォーマンス: 480p推奨、Poseは後続拡張時にサブサンプリング

## License

MIT（予定。必要に応じて更新）
