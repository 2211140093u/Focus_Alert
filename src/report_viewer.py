"""
レポートビューア（アプリ内でレポートを1ページずつ表示）
"""
import cv2
import numpy as np
import os
import json
from pathlib import Path
# from japanese_text import put_japanese_text, get_text_size_japanese  # English mode


class ReportViewer:
    """レポートビューア（ページ送り機能付き）"""
    
    def __init__(self, width=320, height=480, report_dir='reports'):
        self.width = width
        self.height = height
        self.report_dir = report_dir
        self.current_report = None
        self.pages = []  # ページ情報のリスト
        self.current_page = 0
        self.meta_info = {}
        self._split_part_idx = 0  # 横長グラフの分割表示用（0, 1, 2）
        self._current_image_path = None  # 現在表示中の画像パス
        
    def load_report(self, csv_file_path):
        """レポートを読み込み（CSVファイルパスから対応するレポートを探す）"""
        # CSVファイル名からレポートディレクトリを推測
        csv_name = Path(csv_file_path).stem
        report_base = os.path.join(self.report_dir, csv_name)
        
        # レポートメタデータファイルを探す
        meta_file = os.path.join(self.report_dir, csv_name + '_meta.json')
        if not os.path.exists(meta_file):
            # 別のパターンも試す（HTMLファイル名から）
            html_name = csv_name + '.html'
            html_stem = Path(html_name).stem
            meta_file = os.path.join(self.report_dir, html_stem + '_meta.json')
            if not os.path.exists(meta_file):
                return False
        
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.current_report = csv_name
            self.pages = data.get('pages', [])
            self.meta_info = data.get('meta', {})
            self.current_page = 0
            self._split_part_idx = 0
            self._current_image_path = None
            
            # 画像パスを絶対パスに変換（相対パスの場合）
            for page in self.pages:
                if page.get('type') == 'image' and page.get('path'):
                    img_path = page['path']
                    if not os.path.isabs(img_path):
                        # 相対パスの場合、report_dirからの相対パスとして解釈
                        page['path'] = os.path.join(self.report_dir, img_path)
            
            return len(self.pages) > 0
        except Exception as e:
            print(f"Error loading report: {e}")
            return False
    
    def draw(self):
        """現在のページを描画"""
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        img.fill(20)  # 暗い背景
        
        if not self.pages:
            cv2.putText(img, "No Report", (20, self.height // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            return img, []
        
        # ページ情報
        page_info = self.pages[self.current_page]
        page_type = page_info.get('type', 'image')
        page_title = page_info.get('title', '')
        image_path = page_info.get('path', '')
        
        # タイトル表示
        title_y = 20
        cv2.putText(img, page_title, (10, title_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # ページ番号表示
        page_text = f"{self.current_page + 1} / {len(self.pages)}"
        (text_w, _), _ = cv2.getTextSize(page_text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        cv2.putText(img, page_text, (self.width - text_w - 10, title_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1, cv2.LINE_AA)
        
        # コンテンツ表示エリア
        content_y = 40
        content_h = self.height - content_y - 60
        content_w = self.width - 20
        
        if page_type == 'meta':
            # メタ情報ページ
            y = content_y + 20
            for key, value in self.meta_info.items():
                if value is not None:
                    text = f"{key}: {value}"
                    cv2.putText(img, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)
                    y += 20
                    if y > self.height - 80:
                        break
        
        elif page_type == 'summary':
            # サマリ統計ページ
            summary = page_info.get('data', {})
            y = content_y + 20
            for key, value in summary.items():
                if value is not None and not (isinstance(value, float) and np.isnan(value)):
                    text = f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}"
                    cv2.putText(img, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)
                    y += 20
                    if y > self.height - 80:
                        break
        
        elif page_type == 'image' and image_path:
            # 画像ページ
            if os.path.exists(image_path):
                try:
                    page_img = cv2.imread(image_path)
                    if page_img is not None:
                        img_h, img_w = page_img.shape[:2]
                        aspect_ratio = img_w / img_h if img_h > 0 else 1.0
                        
                        # 画像が変わった場合は分割インデックスをリセット
                        if self._current_image_path != image_path:
                            self._current_image_path = image_path
                            self._split_part_idx = 0
                        
                        # 横長グラフ（アスペクト比 > 2.0）の場合、縦に3分割して表示
                        if aspect_ratio > 2.0:
                            # 横長グラフを3つに分割
                            part_w = img_w // 3
                            part_idx = self._split_part_idx  # 現在表示する部分（0, 1, 2）
                            
                            # 分割位置を計算（少し重複を持たせて見やすく）
                            overlap = 10  # 重複ピクセル数
                            x_start = max(0, part_idx * part_w - (overlap if part_idx > 0 else 0))
                            x_end = min(img_w, (part_idx + 1) * part_w + (overlap if part_idx < 2 else 0))
                            
                            # 画像を切り出し
                            part_img = page_img[:, x_start:x_end]
                            
                            # 切り出した部分を画面サイズに合わせてリサイズ
                            part_h, part_w_actual = part_img.shape[:2]
                            scale = min(content_w / part_w_actual, content_h / part_h)
                            new_w = int(part_w_actual * scale)
                            new_h = int(part_h * scale)
                            
                            resized = cv2.resize(part_img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                            
                            # 中央配置
                            x_offset = (content_w - new_w) // 2 + 10
                            y_offset = content_y + (content_h - new_h) // 2
                            
                            # 画像を配置
                            if (y_offset + new_h <= self.height and x_offset + new_w <= self.width and
                                y_offset >= 0 and x_offset >= 0):
                                img[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
                            
                            # 分割表示のインジケーター（左下に表示）
                            split_text = f"Part {part_idx + 1}/3"
                            cv2.putText(img, split_text, (10, self.height - 60), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1, cv2.LINE_AA)
                        else:
                            # 通常の画像（縦長または正方形）は従来通り
                            scale = min(content_w / img_w, content_h / img_h)
                            new_w = int(img_w * scale)
                            new_h = int(img_h * scale)
                            
                            resized = cv2.resize(page_img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                            
                            # 中央配置
                            x_offset = (content_w - new_w) // 2 + 10
                            y_offset = content_y + (content_h - new_h) // 2
                            
                            # 画像を配置（範囲チェック）
                            if (y_offset + new_h <= self.height and x_offset + new_w <= self.width and
                                y_offset >= 0 and x_offset >= 0):
                                img[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
                            else:
                                # 範囲外の場合はさらに縮小
                                scale2 = min((self.width - 20) / img_w, content_h / img_h)
                                new_w2 = int(img_w * scale2)
                                new_h2 = int(img_h * scale2)
                                resized2 = cv2.resize(page_img, (new_w2, new_h2), interpolation=cv2.INTER_LINEAR)
                                x_offset2 = (self.width - new_w2) // 2
                                y_offset2 = content_y + (content_h - new_h2) // 2
                                if (y_offset2 + new_h2 <= self.height and x_offset2 + new_w2 <= self.width and
                                    y_offset2 >= 0 and x_offset2 >= 0):
                                    img[y_offset2:y_offset2+new_h2, x_offset2:x_offset2+new_w2] = resized2
                except Exception as e:
                    cv2.putText(img, f"Image Load Error: {e}", (10, content_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1, cv2.LINE_AA)
        
        # ナビゲーションボタン
        buttons = []
        
        # 戻るボタン
        back_rect = (10, self.height - 50, 70, self.height - 10)
        cv2.rectangle(img, (10, self.height - 50), (70, self.height - 10), (100, 100, 100), -1)
        cv2.rectangle(img, (10, self.height - 50), (70, self.height - 10), (255, 255, 255), 1)
        cv2.putText(img, "Back", (15, self.height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
        buttons.append(('back', back_rect))
        
        # 前のページボタン
        if self.current_page > 0:
            prev_rect = (80, self.height - 50, 130, self.height - 10)
            cv2.rectangle(img, (80, self.height - 50), (130, self.height - 10), (80, 80, 80), -1)
            cv2.rectangle(img, (80, self.height - 50), (130, self.height - 10), (255, 255, 255), 1)
            cv2.putText(img, "<Prev", (85, self.height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
            buttons.append(('prev', prev_rect))
        
        # 次のページボタン
        if self.current_page < len(self.pages) - 1:
            next_rect = (self.width - 80, self.height - 50, self.width - 10, self.height - 10)
            cv2.rectangle(img, (self.width - 80, self.height - 50), (self.width - 10, self.height - 10), (80, 80, 80), -1)
            cv2.rectangle(img, (self.width - 80, self.height - 50), (self.width - 10, self.height - 10), (255, 255, 255), 1)
            cv2.putText(img, "Next>", (self.width - 75, self.height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
            buttons.append(('next', next_rect))
        
        return img, buttons
    
    def handle_click(self, x, y, buttons):
        """クリック処理"""
        for name, (x1, y1, x2, y2) in buttons:
            if x1 <= x <= x2 and y1 <= y <= y2:
                if name == 'back':
                    return 'back'
                elif name == 'prev':
                    # 横長グラフの分割表示の場合、まず分割部分を切り替え
                    if self._current_image_path and self._split_part_idx > 0:
                        self._split_part_idx -= 1
                        return None
                    # 通常のページ送り
                    if self.current_page > 0:
                        self.current_page -= 1
                        self._split_part_idx = 0  # ページが変わったら分割インデックスをリセット
                        self._current_image_path = None
                    return None
                elif name == 'next':
                    # 横長グラフの分割表示の場合、まず分割部分を切り替え
                    if self._current_image_path:
                        page_info = self.pages[self.current_page]
                        if page_info.get('type') == 'image':
                            image_path = page_info.get('path', '')
                            if image_path:
                                full_path = image_path if os.path.isabs(image_path) else os.path.join(self.report_dir, image_path)
                                if os.path.exists(full_path):
                                    page_img = cv2.imread(full_path)
                                    if page_img is not None:
                                        img_h, img_w = page_img.shape[:2]
                                        aspect_ratio = img_w / img_h if img_h > 0 else 1.0
                                        if aspect_ratio > 2.0 and self._split_part_idx < 2:
                                            self._split_part_idx += 1
                                            return None
                    # 通常のページ送り
                    if self.current_page < len(self.pages) - 1:
                        self.current_page += 1
                        self._split_part_idx = 0  # ページが変わったら分割インデックスをリセット
                        self._current_image_path = None
                    return None
        return None
    
    def next_page(self):
        """次のページに進む（分割表示の場合は分割部分を切り替え）"""
        # 横長グラフの分割表示の場合、まず分割部分を切り替え
        if self._current_image_path:
            page_info = self.pages[self.current_page]
            if page_info.get('type') == 'image':
                image_path = page_info.get('path', '')
                if image_path:
                    full_path = os.path.join(self.report_dir, image_path) if not os.path.isabs(image_path) else image_path
                    if os.path.exists(full_path):
                        page_img = cv2.imread(full_path)
                        if page_img is not None:
                            img_h, img_w = page_img.shape[:2]
                            aspect_ratio = img_w / img_h if img_h > 0 else 1.0
                            if aspect_ratio > 2.0 and self._split_part_idx < 2:
                                self._split_part_idx += 1
                                return True
        # 通常のページ送り
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self._split_part_idx = 0  # ページが変わったら分割インデックスをリセット
            self._current_image_path = None
            return True
        return False
    
    def prev_page(self):
        """前のページに戻る（分割表示の場合は分割部分を切り替え）"""
        # 横長グラフの分割表示の場合、まず分割部分を切り替え
        if self._current_image_path and self._split_part_idx > 0:
            self._split_part_idx -= 1
            return True
        # 通常のページ送り
        if self.current_page > 0:
            self.current_page -= 1
            self._split_part_idx = 0  # ページが変わったら分割インデックスをリセット
            self._current_image_path = None
            return True
        return False

