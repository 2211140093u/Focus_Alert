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
        self._zoom_scale = 1.0  # 拡大縮小スケール（1.0 = 通常、2.0 = 2倍など）
        self._zoom_offset_x = 0  # 拡大時のオフセット（パン用）
        self._zoom_offset_y = 0
        
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
            # パスを正規化（絶対パスに統一）
            if not os.path.isabs(image_path):
                # 相対パスの場合、report_dirからの相対パスとして解釈
                image_path = os.path.join(self.report_dir, image_path)
            image_path = os.path.normpath(image_path)  # パスを正規化
            
            # デバッグ用：画像パスを出力
            if not os.path.exists(image_path):
                print(f"Image not found: {image_path}")
                print(f"Report dir: {self.report_dir}")
                print(f"Original path: {page_info.get('path', '')}")
                # 別のパスパターンも試す
                alt_paths = [
                    os.path.join(os.path.dirname(self.report_dir), image_path) if os.path.isabs(self.report_dir) else None,
                    os.path.join(os.getcwd(), 'reports', os.path.basename(image_path)),
                    os.path.join(os.getcwd(), image_path),
                ]
                for alt_path in alt_paths:
                    if alt_path and os.path.exists(alt_path):
                        print(f"Found image at alternative path: {alt_path}")
                        image_path = alt_path
                        break
            
            if os.path.exists(image_path):
                try:
                    page_img = cv2.imread(image_path)
                    if page_img is not None:
                        img_h, img_w = page_img.shape[:2]
                        aspect_ratio = img_w / img_h if img_h > 0 else 1.0
                        
                        # 画像が変わった場合は分割インデックスをリセット
                        current_path_norm = os.path.normpath(self._current_image_path) if self._current_image_path else None
                        if current_path_norm != image_path:
                            self._current_image_path = image_path
                            self._split_part_idx = 0
                        
                        # 時系列グラフ（タイトルに「時系列グラフ」が含まれる）は分割せず、1枚の画像として表示
                        is_timeseries = '時系列グラフ' in page_title or 'Timeseries' in page_title
                        
                        # 横長グラフ（アスペクト比 > 2.0）の場合、時系列グラフ以外は縦に3分割して表示
                        if aspect_ratio > 2.0 and not is_timeseries:
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
                            # 通常の画像（縦長または正方形）は拡大縮小対応
                            # 基本スケールを計算
                            base_scale = min(content_w / img_w, content_h / img_h)
                            # 拡大縮小スケールを適用
                            scale = base_scale * self._zoom_scale
                            new_w = int(img_w * scale)
                            new_h = int(img_h * scale)
                            
                            resized = cv2.resize(page_img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                            
                            # 中央配置（拡大時はオフセットを考慮）
                            x_offset = (content_w - new_w) // 2 + 10 + self._zoom_offset_x
                            y_offset = content_y + (content_h - new_h) // 2 + self._zoom_offset_y
                            
                            # 画像の表示範囲を計算（画面内に収まるように）
                            display_x1 = max(10, x_offset)
                            display_y1 = max(content_y, y_offset)
                            display_x2 = min(self.width - 10, x_offset + new_w)
                            display_y2 = min(self.height - 60, y_offset + new_h)
                            
                            # 元画像からの切り出し位置を計算
                            src_x1 = max(0, (10 - x_offset) / scale) if x_offset < 10 else 0
                            src_y1 = max(0, (content_y - y_offset) / scale) if y_offset < content_y else 0
                            src_x2 = min(img_w, (self.width - 10 - x_offset) / scale) if x_offset + new_w > self.width - 10 else img_w
                            src_y2 = min(img_h, (self.height - 60 - y_offset) / scale) if y_offset + new_h > self.height - 60 else img_h
                            
                            # 切り出し
                            if src_x2 > src_x1 and src_y2 > src_y1:
                                src_w = int(src_x2 - src_x1)
                                src_h = int(src_y2 - src_y1)
                                src_img = resized[int(src_y1*scale):int(src_y2*scale), int(src_x1*scale):int(src_x2*scale)]
                                
                                # 表示サイズに合わせてリサイズ
                                if src_w > 0 and src_h > 0:
                                    display_w = display_x2 - display_x1
                                    display_h = display_y2 - display_y1
                                    if display_w > 0 and display_h > 0:
                                        final_img = cv2.resize(src_img, (display_w, display_h), interpolation=cv2.INTER_LINEAR)
                                        img[display_y1:display_y2, display_x1:display_x2] = final_img
                            
                            # 拡大縮小インジケーター
                            if self._zoom_scale != 1.0:
                                zoom_text = f"Zoom: {self._zoom_scale:.1f}x"
                                cv2.putText(img, zoom_text, (10, self.height - 60), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1, cv2.LINE_AA)
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
        
        # 拡大縮小ボタン（画像ページの場合のみ）
        if page_type == 'image':
            # 拡大ボタン
            zoom_in_rect = (140, self.height - 50, 190, self.height - 10)
            cv2.rectangle(img, (140, self.height - 50), (190, self.height - 10), (80, 120, 80), -1)
            cv2.rectangle(img, (140, self.height - 50), (190, self.height - 10), (255, 255, 255), 1)
            cv2.putText(img, "+", (165, self.height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
            buttons.append(('zoom_in', zoom_in_rect))
            
            # 縮小ボタン
            zoom_out_rect = (200, self.height - 50, 250, self.height - 10)
            cv2.rectangle(img, (200, self.height - 50), (250, self.height - 10), (80, 120, 80), -1)
            cv2.rectangle(img, (200, self.height - 50), (250, self.height - 10), (255, 255, 255), 1)
            cv2.putText(img, "-", (225, self.height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
            buttons.append(('zoom_out', zoom_out_rect))
            
            # リセットボタン
            zoom_reset_rect = (260, self.height - 50, 310, self.height - 10)
            cv2.rectangle(img, (260, self.height - 50), (310, self.height - 10), (120, 80, 80), -1)
            cv2.rectangle(img, (260, self.height - 50), (310, self.height - 10), (255, 255, 255), 1)
            cv2.putText(img, "Reset", (265, self.height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)
            buttons.append(('zoom_reset', zoom_reset_rect))
            
            # パンボタン（拡大時のみ有効、横長画面に合わせてコンパクトに配置）
            if self._zoom_scale > 1.0:
                # パンエリアの開始位置（Resetボタンの右側）
                pan_start_x = 320
                pan_btn_size = 35
                pan_btn_y_top = self.height - 50
                pan_btn_y_mid = self.height - 30
                pan_btn_y_bottom = self.height - 10
                
                # 上移動
                pan_up_rect = (pan_start_x + pan_btn_size, pan_btn_y_top, pan_start_x + pan_btn_size * 2, pan_btn_y_mid)
                cv2.rectangle(img, (pan_start_x + pan_btn_size, pan_btn_y_top), (pan_start_x + pan_btn_size * 2, pan_btn_y_mid), (120, 120, 80), -1)
                cv2.rectangle(img, (pan_start_x + pan_btn_size, pan_btn_y_top), (pan_start_x + pan_btn_size * 2, pan_btn_y_mid), (255, 255, 255), 1)
                cv2.putText(img, "^", (pan_start_x + pan_btn_size + 12, pan_btn_y_top + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
                buttons.append(('pan_up', pan_up_rect))
                
                # 左移動
                pan_left_rect = (pan_start_x, pan_btn_y_mid, pan_start_x + pan_btn_size, pan_btn_y_bottom)
                cv2.rectangle(img, (pan_start_x, pan_btn_y_mid), (pan_start_x + pan_btn_size, pan_btn_y_bottom), (120, 120, 80), -1)
                cv2.rectangle(img, (pan_start_x, pan_btn_y_mid), (pan_start_x + pan_btn_size, pan_btn_y_bottom), (255, 255, 255), 1)
                cv2.putText(img, "<", (pan_start_x + 12, pan_btn_y_mid + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
                buttons.append(('pan_left', pan_left_rect))
                
                # 右移動
                pan_right_rect = (pan_start_x + pan_btn_size * 2, pan_btn_y_mid, pan_start_x + pan_btn_size * 3, pan_btn_y_bottom)
                cv2.rectangle(img, (pan_start_x + pan_btn_size * 2, pan_btn_y_mid), (pan_start_x + pan_btn_size * 3, pan_btn_y_bottom), (120, 120, 80), -1)
                cv2.rectangle(img, (pan_start_x + pan_btn_size * 2, pan_btn_y_mid), (pan_start_x + pan_btn_size * 3, pan_btn_y_bottom), (255, 255, 255), 1)
                cv2.putText(img, ">", (pan_start_x + pan_btn_size * 2 + 12, pan_btn_y_mid + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
                buttons.append(('pan_right', pan_right_rect))
                
                # 下移動
                pan_down_rect = (pan_start_x + pan_btn_size, pan_btn_y_mid, pan_start_x + pan_btn_size * 2, pan_btn_y_bottom)
                cv2.rectangle(img, (pan_start_x + pan_btn_size, pan_btn_y_mid), (pan_start_x + pan_btn_size * 2, pan_btn_y_bottom), (120, 120, 80), -1)
                cv2.rectangle(img, (pan_start_x + pan_btn_size, pan_btn_y_mid), (pan_start_x + pan_btn_size * 2, pan_btn_y_bottom), (255, 255, 255), 1)
                cv2.putText(img, "v", (pan_start_x + pan_btn_size + 12, pan_btn_y_mid + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
                buttons.append(('pan_down', pan_down_rect))
        
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
                        self._zoom_scale = 1.0  # ズームもリセット
                        self._zoom_offset_x = 0
                        self._zoom_offset_y = 0
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
                        self._zoom_scale = 1.0  # ズームもリセット
                        self._zoom_offset_x = 0
                        self._zoom_offset_y = 0
                    return None
                elif name == 'zoom_in':
                    # 拡大（最大3倍まで）
                    self._zoom_scale = min(3.0, self._zoom_scale * 1.2)
                    return None
                elif name == 'zoom_out':
                    # 縮小（最小0.5倍まで）
                    self._zoom_scale = max(0.5, self._zoom_scale / 1.2)
                    # 縮小時はオフセットもリセット
                    if self._zoom_scale <= 1.0:
                        self._zoom_offset_x = 0
                        self._zoom_offset_y = 0
                    return None
                elif name == 'zoom_reset':
                    # ズームリセット
                    self._zoom_scale = 1.0
                    self._zoom_offset_x = 0
                    self._zoom_offset_y = 0
                    return None
                elif name == 'pan_up':
                    # 上に移動
                    self._zoom_offset_y += 20
                    return None
                elif name == 'pan_down':
                    # 下に移動
                    self._zoom_offset_y -= 20
                    return None
                elif name == 'pan_left':
                    # 左に移動
                    self._zoom_offset_x += 20
                    return None
                elif name == 'pan_right':
                    # 右に移動
                    self._zoom_offset_x -= 20
                    return None
        return None
    
    def next_page(self):
        """次のページに進む（分割表示の場合は分割部分を切り替え）"""
        # 横長グラフの分割表示の場合、まず分割部分を切り替え
        if self._current_image_path and os.path.exists(self._current_image_path):
            page_img = cv2.imread(self._current_image_path)
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

