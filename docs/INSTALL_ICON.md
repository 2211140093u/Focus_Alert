# アイコンの設定（オプション）

Focus Alertのデスクトップショートカットにアイコンを設定する方法です。

## 方法1: 既存のアイコンを使用

システムの既存アイコンを使用する場合、`.desktop`ファイルの`Icon=`行を以下のように変更：

```ini
Icon=application-x-executable
```

または、他の利用可能なアイコン：
- `camera-web`
- `preferences-desktop`
- `utilities-terminal`

## 方法2: カスタムアイコン画像を使用

1. アイコン画像を準備（推奨サイズ: 48x48 または 64x64 ピクセル）
   - PNG形式
   - 透明背景推奨

2. アイコンをプロジェクトディレクトリに配置：
   ```bash
   # 例: ~/Focus_Alert/icon.png
   ```

3. `.desktop`ファイルの`Icon=`行を編集：
   ```ini
   Icon=/home/pi/Focus_Alert/icon.png
   ```

## 方法3: オンラインアイコンを使用

無料のアイコンサイトからダウンロード：
- [Flaticon](https://www.flaticon.com/)
- [Icons8](https://icons8.com/)

「focus」「eye」「monitor」などのキーワードで検索

## アイコンの確認

デスクトップでアイコンが表示されない場合：

1. ファイルマネージャーで`.desktop`ファイルを右クリック
2. 「プロパティ」→「権限」タブ
3. 「実行可能」にチェックを入れる

または、コマンドラインから：
```bash
chmod +x ~/Desktop/focus_alert.desktop
```

