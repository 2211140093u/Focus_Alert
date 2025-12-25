# レポート作成ガイド

このドキュメントでは、Focus Alertシステムで記録されたデータからレポートを作成する方法と、記録される項目について説明します。

## レポートの作成方法

### 基本的な使用方法

```bash
python scripts/report.py --log logs/pc_test.csv --out reports/report.html
```

### 複数のログファイルをまとめてレポート化

```bash
python scripts/report.py --log logs/session1.csv logs/session2.csv --out reports/combined_report.html
```

### タイトルを指定

```bash
python scripts/report.py --log logs/pc_test.csv --out reports/report.html --title "集中力計測レポート - 2024年1月"
```

## 記録される項目

### CSVログの構造

CSVログファイルは以下の3種類の行タイプで構成されます：

1. **meta行**: セッションのメタ情報
2. **event行**: イベント（ブロック開始/終了、マーカーなど）
3. **frame行**: 各フレームの検出データ

### 主要なカラム

#### メタ情報
- `session`: セッションID
- `participant`: 参加者ID
- `task`: タスク名
- `phase`: フェーズ（train/eval）
- `block_id`: ブロックID

#### まばたき検出（Blink）
- `ear`: Eye Aspect Ratio（現在値）
- `ear_base`: EAR基準値（開眼時の基準）
- `ear_thr`: EAR閾値（この値未満で閉眼と判定）
- `blink_count`: まばたき回数（累積）
- `is_closed`: 現在閉眼しているか（True/False）
- `long_close`: 長時間閉眼しているか（True/False、約400ms以上）

#### 視線検出（Gaze）
- `gaze`: 視線の水平方向オフセット（正規化値）
- `gaze_y`: 視線の垂直方向オフセット（正規化値）
- `gaze_thr`: 視線逸脱の閾値（水平方向）
- `gaze_y_thr`: 視線逸脱の閾値（垂直方向）
- `gaze_bias`: 視線の中心バイアス（キャリブレーション値）
- `gaze_bias_y`: 視線の垂直バイアス（キャリブレーション値）
- `gaze_offlvl`: 視線逸脱レベル（0.0-1.0、1.0に近いほど逸脱）

#### 統合スコア
- `risk`: リスクスコア（0.0-1.0、集中力低下の指標）
- `alert`: アラートが発火したか（1/0）

#### イベント
- `event`: イベントタイプ（block_start, block_end, marker, distractor_start, distractor_end, calibrate_center）
- `info`: イベントの追加情報

## レポートに含まれる内容

### 1. メタ情報テーブル

セッションの基本情報を表示：
- セッションID、参加者ID、タスク名
- フェーズ、ブロック数、総フレーム数

### 2. サマリ統計

- `frames`: 総フレーム数
- `risk_mean`: リスクスコアの平均値
- `risk_p95`: リスクスコアの95パーセンタイル
- `blink_count_max`: 最大まばたき回数
- `long_close_count`: 長時間閉眼の回数
- `off_level_mean`: 視線逸脱レベルの平均値
- `distractor_ratio`: 注意散漫区間の割合

### 3. 時系列グラフ

3つのサブプロットで構成：

#### リスクスコア（上段）
- 時系列でのリスクスコアの変化
- アラートが発火した時点を赤い点で表示
- 注意散漫区間（distractor）をオレンジの縦線で表示

#### EAR（中段）
- EARの現在値（緑線）
- EAR基準値（薄緑線）
- EAR閾値（赤の破線）

#### 視線（下段）
- 視線の水平方向オフセット（紫線）
- 視線逸脱の閾値（グレーの破線）

### 4. 分布ヒストグラム

3つのヒストグラム：
- リスクスコアの分布
- EARの分布
- 視線オフセットの分布

### 5. 視線の2次元表示（オプション）

`gaze_y`カラムが存在する場合、以下の2つの図が追加されます：

#### 散布図
- 視線のX-Y座標の散布図
- 閾値の補助線を表示

#### ヒートマップ
- 視線のX-Y座標の密度分布
- 色の濃淡で頻度を表現

## レポートの見方

### リスクスコアの解釈

- **0.0-0.3**: 低リスク（集中している）
- **0.3-0.55**: 中リスク（注意が必要）
- **0.55以上**: 高リスク（アラート発火、集中力低下）

### EARの解釈

- **EAR > 閾値**: 目が開いている
- **EAR < 閾値**: 目が閉じている
- **EAR基準値**: 個人の開眼時の基準値（適応的に更新）

### 視線の解釈

- **gaze ≈ 0**: 画面中央を注視
- **|gaze| > 閾値**: 視線が逸脱している
- **gaze_offlvl**: 逸脱の程度（1.0に近いほど長時間逸脱）

## トラブルシューティング

### レポートが生成されない

```bash
# ログファイルの存在確認
ls -l logs/*.csv

# ログファイルの内容確認（最初の数行）
head -n 5 logs/pc_test.csv
```

### グラフが表示されない

- CSVファイルに必要なカラムが含まれているか確認
- `pandas`, `matplotlib`, `seaborn`がインストールされているか確認

### データが正しく表示されない

- CSVファイルのエンコーディングを確認（UTF-8推奨）
- タイムスタンプ（`ts`）が正しく記録されているか確認

## カスタマイズ

### レポートスクリプトの修正

`scripts/report.py`を編集することで、以下のカスタマイズが可能です：

- グラフの色やスタイル
- 追加の統計指標
- 新しいグラフの追加
- HTMLテンプレートの変更

## 例: 実際の使用フロー

1. **計測の実行**
   ```bash
   python src/app.py --cam 0 --width 1280 --height 720 --log logs/session1.csv --session S001 --participant P01 --task typing
   ```

2. **レポートの生成**
   ```bash
   python scripts/report.py --log logs/session1.csv --out reports/session1_report.html
   ```

3. **レポートの確認**
   - ブラウザで`reports/session1_report.html`を開く
   - 時系列グラフで集中力の変化を確認
   - サマリ統計で全体の傾向を把握

## 参考

- [PCセットアップガイド](PC_SETUP.md) - 計測の実行方法
- [Raspberry Piセットアップガイド](RASPBERRY_PI_SETUP.md) - Raspberry Piでの実行方法

