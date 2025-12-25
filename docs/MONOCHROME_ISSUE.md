# モノクロ表示の問題について

## 問題の説明

PCで試したところ映像がモノクロ（グレースケール）になっている場合の原因と対処法です。

## 考えられる原因

### 1. カメラの設定問題

一部のカメラでは、デフォルトでモノクロモードになっている場合があります。

**確認方法**:
```python
# カメラの色形式を確認
cap = cv2.VideoCapture(0)
print(cap.get(cv2.CAP_PROP_CONVERT_RGB))  # 1が正常（RGB変換有効）
```

**対処法**:
- カメラのドライバー設定を確認
- カメラアプリでカラー表示されるか確認

### 2. OpenCVの表示問題

OpenCVの`imshow`はBGR形式を想定していますが、グレースケール画像として解釈される場合があります。

**現在のコード**:
```python
# カメラからBGR形式で取得
ok, frame = cam.read()

# MediaPipe用にRGBに変換（処理のみ）
rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
fm = face.process(rgb)

# 表示は元のBGRフレームを使用
vis = overlay.draw(frame, ...)  # frameはBGR形式
cv2.imshow(win_name, vis_display)
```

**確認ポイント**:
- `frame.shape`が`(height, width, 3)`であることを確認（3チャンネル = カラー）
- `frame.shape`が`(height, width)`の場合はグレースケール

### 3. カメラドライバーの問題

一部のカメラドライバーでは、カラー出力が正しく設定されていない場合があります。

**対処法**:
```python
# capture.pyの_OpenCVCamera.open()で明示的に設定
self.cap.set(cv2.CAP_PROP_CONVERT_RGB, 1)  # RGB変換を有効化
```

### 4. カメラのハードウェア問題

カメラ自体がモノクロモードになっている可能性があります。

**確認方法**:
- 他のアプリケーション（カメラアプリなど）でカラー表示されるか確認
- カメラの設定を確認

## 対処法

### 方法1: カメラ設定の確認

```bash
# Windows: デバイスマネージャーでカメラのプロパティを確認
# Mac/Linux: カメラアプリでカラー表示されるか確認
```

### 方法2: コードで明示的に設定

`src/capture.py`の`_OpenCVCamera.open()`に以下を追加：

```python
# RGB変換を明示的に有効化
self.cap.set(cv2.CAP_PROP_CONVERT_RGB, 1)
```

### 方法3: フレーム形式の確認

`src/app.py`でフレーム形式を確認：

```python
ok, frame = cam.read()
if ok:
    print(f"Frame shape: {frame.shape}")  # (height, width, 3)が正常
    print(f"Frame dtype: {frame.dtype}")  # uint8が正常
    if len(frame.shape) == 2:
        # グレースケールの場合、カラーに変換
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
```

## デバッグ方法

### 1. フレーム情報の表示

```python
# app.pyのmain()関数内で確認
ok, frame = cam.read()
if ok:
    print(f"Frame shape: {frame.shape}")
    print(f"Frame dtype: {frame.dtype}")
    print(f"Frame min/max: {frame.min()}/{frame.max()}")
```

### 2. カメラプロパティの確認

```python
cap = cv2.VideoCapture(0)
print(f"CONVERT_RGB: {cap.get(cv2.CAP_PROP_CONVERT_RGB)}")
print(f"FORMAT: {cap.get(cv2.CAP_PROP_FORMAT)}")
```

### 3. テスト画像の保存

```python
# フレームを画像として保存して確認
cv2.imwrite('test_frame.jpg', frame)
# 画像を開いてカラーかモノクロか確認
```

## 一般的な解決策

最も可能性が高いのは、カメラドライバーの設定問題です。以下の手順を試してください：

1. **カメラアプリで確認**: 他のアプリでカラー表示されるか確認
2. **カメラドライバーの更新**: 最新のドライバーに更新
3. **カメラ設定の確認**: カメラの設定でカラーモードが有効か確認
4. **コードで明示的に設定**: `CAP_PROP_CONVERT_RGB`を1に設定

## 報告が必要な情報

問題が解決しない場合、以下の情報を報告してください：

1. OS（Windows/Mac/Linux）
2. カメラの型番
3. `frame.shape`の値
4. 他のアプリでカラー表示されるか
5. エラーメッセージ（あれば）

