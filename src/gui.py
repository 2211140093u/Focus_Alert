import cv2
import numpy as np
import os
import json
from pathlib import Path
from virtual_keyboard import VirtualKeyboard
from report_viewer import ReportViewer

class MainMenu:
    """メインメニュー画面"""
    def __init__(self, width=320, height=480):
        self.width = width
        self.height = height
        self.selected = None
        
    def draw(self):
        """メニュー画面を描画"""
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        img.fill(40)  # 暗い背景
        
        # タイトル
        title = "Focus Alert"
        font_scale = 0.8
        thickness = 2
        (text_width, text_height), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        x = (self.width - text_width) // 2
        y = 50
        cv2.putText(img, title, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        
        # ボタン
        button_height = 60
        button_width = self.width - 40
        button_x = 20
        button_spacing = 20
        start_y = 120
        
        buttons = []
        
        # 計測開始ボタン
        btn1_y = start_y
        btn1_rect = (button_x, btn1_y, button_x + button_width, btn1_y + button_height)
        color1 = (0, 150, 0) if self.selected == 'measure' else (0, 100, 0)
        cv2.rectangle(img, (button_x, btn1_y), (button_x + button_width, btn1_y + button_height), color1, -1)
        cv2.rectangle(img, (button_x, btn1_y), (button_x + button_width, btn1_y + button_height), (255, 255, 255), 2)
        text1 = "計測開始"
        (tw1, th1), _ = get_text_size_japanese(text1, 0.6)
        tx1 = button_x + (button_width - tw1) // 2
        ty1 = btn1_y + (button_height + th1) // 2
        img = put_japanese_text(img, text1, (tx1, ty1), 0.6, (255, 255, 255), 2)
        buttons.append(('measure', btn1_rect))
        
        # データ確認ボタン
        btn2_y = start_y + button_height + button_spacing
        btn2_rect = (button_x, btn2_y, button_x + button_width, btn2_y + button_height)
        color2 = (150, 150, 0) if self.selected == 'data' else (100, 100, 0)
        cv2.rectangle(img, (button_x, btn2_y), (button_x + button_width, btn2_y + button_height), color2, -1)
        cv2.rectangle(img, (button_x, btn2_y), (button_x + button_width, btn2_y + button_height), (255, 255, 255), 2)
        text2 = "データ確認"
        (tw2, th2), _ = get_text_size_japanese(text2, 0.6)
        tx2 = button_x + (button_width - tw2) // 2
        ty2 = btn2_y + (button_height + th2) // 2
        img = put_japanese_text(img, text2, (tx2, ty2), 0.6, (255, 255, 255), 2)
        buttons.append(('data', btn2_rect))
        
        # オプションボタン
        btn3_y = start_y + (button_height + button_spacing) * 2
        btn3_rect = (button_x, btn3_y, button_x + button_width, btn3_y + button_height)
        color3 = (150, 0, 150) if self.selected == 'options' else (100, 0, 100)
        cv2.rectangle(img, (button_x, btn3_y), (button_x + button_width, btn3_y + button_height), color3, -1)
        cv2.rectangle(img, (button_x, btn3_y), (button_x + button_width, btn3_y + button_height), (255, 255, 255), 2)
        text3 = "オプション"
        (tw3, th3), _ = get_text_size_japanese(text3, 0.6)
        tx3 = button_x + (button_width - tw3) // 2
        ty3 = btn3_y + (button_height + th3) // 2
        img = put_japanese_text(img, text3, (tx3, ty3), 0.6, (255, 255, 255), 2)
        buttons.append(('options', btn3_rect))
        
        # 終了ボタン（画面下部）
        btn4_y = self.height - button_height - 20
        btn4_rect = (button_x, btn4_y, button_x + button_width, btn4_y + button_height)
        color4 = (150, 0, 0) if self.selected == 'quit' else (100, 0, 0)
        cv2.rectangle(img, (button_x, btn4_y), (button_x + button_width, btn4_y + button_height), color4, -1)
        cv2.rectangle(img, (button_x, btn4_y), (button_x + button_width, btn4_y + button_height), (255, 255, 255), 2)
        text4 = "終了"
        (tw4, th4), _ = get_text_size_japanese(text4, 0.6)
        tx4 = button_x + (button_width - tw4) // 2
        ty4 = btn4_y + (button_height + th4) // 2
        img = put_japanese_text(img, text4, (tx4, ty4), 0.6, (255, 255, 255), 2)
        buttons.append(('quit', btn4_rect))
        
        return img, buttons
    
    def handle_click(self, x, y, buttons):
        """クリック位置から選択されたボタンを返す"""
        for name, (x1, y1, x2, y2) in buttons:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return name
        return None


class OptionsMenu:
    """オプション設定画面"""
    def __init__(self, width=320, height=480, settings=None):
        self.width = width
        self.height = height
        self.settings = settings or {
            'ear_threshold_ratio': 0.90,
            'ear_baseline_init': 0.45,
            'risk_threshold': 0.55,
            'cooldown_sec': 60.0,
        }
        self.selected_param = None
        self.edit_mode = False
        
    def draw(self):
        """オプション画面を描画"""
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        img.fill(40)
        
        # タイトル
        title = "オプション"
        img = put_japanese_text(img, title, (20, 30), 0.7, (255, 255, 255), 2)
        
        # 戻るボタン
        back_rect = (10, self.height - 40, 80, self.height - 10)
        cv2.rectangle(img, (10, self.height - 40), (80, self.height - 10), (100, 100, 100), -1)
        cv2.rectangle(img, (10, self.height - 40), (80, self.height - 10), (255, 255, 255), 1)
        img = put_japanese_text(img, "戻る", (15, self.height - 15), 0.4, (255, 255, 255), 1)
        
        # 保存ボタン
        save_rect = (self.width - 80, self.height - 40, self.width - 10, self.height - 10)
        cv2.rectangle(img, (self.width - 80, self.height - 40), (self.width - 10, self.height - 10), (0, 150, 0), -1)
        cv2.rectangle(img, (self.width - 80, self.height - 40), (self.width - 10, self.height - 10), (255, 255, 255), 1)
        img = put_japanese_text(img, "保存", (self.width - 75, self.height - 15), 0.4, (255, 255, 255), 1)
        
        # パラメータ表示
        y_start = 60
        line_height = 50
        params = [
            ('ear_threshold_ratio', 'EAR閾値比率', 0.70, 0.98),
            ('ear_baseline_init', 'EAR基準値', 0.30, 0.60),
            ('risk_threshold', 'リスク閾値', 0.40, 0.70),
            ('cooldown_sec', 'クールダウン(秒)', 30.0, 120.0),
        ]
        
        buttons = [('back', back_rect), ('save', save_rect)]
        
        for i, (key, label, min_val, max_val) in enumerate(params):
            y = y_start + i * line_height
            value = self.settings[key]
            
            # パラメータ名
            img = put_japanese_text(img, label, (20, y + 15), 0.4, (255, 255, 255), 1)
            
            # 値表示
            value_str = f"{value:.2f}" if isinstance(value, float) else f"{int(value)}"
            color = (0, 255, 255) if self.selected_param == key else (200, 200, 200)
            img = put_japanese_text(img, value_str, (20, y + 35), 0.5, color, 2)
            
            # 調整ボタン（-）
            minus_rect = (self.width - 100, y, self.width - 60, y + 30)
            cv2.rectangle(img, (self.width - 100, y), (self.width - 60, y + 30), (100, 100, 100), -1)
            cv2.putText(img, "-", (self.width - 85, y + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            buttons.append((f'{key}_minus', minus_rect))
            
            # 調整ボタン（+）
            plus_rect = (self.width - 50, y, self.width - 10, y + 30)
            cv2.rectangle(img, (self.width - 50, y), (self.width - 10, y + 30), (100, 100, 100), -1)
            cv2.putText(img, "+", (self.width - 35, y + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            buttons.append((f'{key}_plus', plus_rect))
            
            # クリック領域（値部分）
            value_rect = (20, y, self.width - 110, y + 40)
            buttons.append((f'{key}_select', value_rect))
        
        return img, buttons
    
    def handle_click(self, x, y, buttons):
        """クリック処理"""
        for name, (x1, y1, x2, y2) in buttons:
            if x1 <= x <= x2 and y1 <= y <= y2:
                if name == 'back':
                    return 'back'
                elif name == 'save':
                    return 'save'
                elif name.endswith('_minus'):
                    key = name.replace('_minus', '')
                    self.adjust_value(key, -1)
                    return None
                elif name.endswith('_plus'):
                    key = name.replace('_plus', '')
                    self.adjust_value(key, 1)
                    return None
                elif name.endswith('_select'):
                    key = name.replace('_select', '')
                    self.selected_param = key
                    return None
        return None
    
    def adjust_value(self, key, direction):
        """値を調整"""
        if key not in self.settings:
            return
        
        step = 0.01 if isinstance(self.settings[key], float) else 1.0
        if key == 'ear_threshold_ratio':
            step = 0.01
            min_val, max_val = 0.70, 0.98
        elif key == 'ear_baseline_init':
            step = 0.01
            min_val, max_val = 0.30, 0.60
        elif key == 'risk_threshold':
            step = 0.01
            min_val, max_val = 0.40, 0.70
        elif key == 'cooldown_sec':
            step = 5.0
            min_val, max_val = 30.0, 120.0
        else:
            return
        
        new_value = self.settings[key] + direction * step
        new_value = max(min_val, min(max_val, new_value))
        self.settings[key] = new_value
    
    def save_settings(self, path='config/settings.json'):
        """設定を保存"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=2)
    
    def load_settings(self, path='config/settings.json'):
        """設定を読み込み"""
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                self.settings.update(loaded)


class DataViewer:
    """データ確認画面"""
    def __init__(self, width=320, height=480, log_dir='logs'):
        self.width = width
        self.height = height
        self.log_dir = log_dir
        self.selected_file = None
        self.mode = 'list'  # 'list', 'view', 'edit'
        self.keyboard = VirtualKeyboard(width=width, height=height)
        self.original_note = ""  # 編集前のメモ
        self.report_viewer = ReportViewer(width=width, height=height)
        
    def get_log_files(self):
        """ログファイル一覧を取得"""
        if not os.path.exists(self.log_dir):
            return []
        files = [f for f in os.listdir(self.log_dir) if f.endswith('.csv')]
        files.sort(reverse=True)  # 新しい順
        return files
    
    def draw(self):
        """データ確認画面を描画"""
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        img.fill(40)
        
        if self.mode == 'list':
            return self._draw_list(img)
        elif self.mode == 'view':
            return self._draw_view(img)
        elif self.mode == 'edit':
            return self._draw_edit(img)
        elif self.mode == 'report':
            return self.report_viewer.draw()
        return img, []
    
    def _draw_list(self, img):
        """ファイル一覧を描画"""
        # タイトル
        img = put_japanese_text(img, "データ確認", (20, 30), 0.7, (255, 255, 255), 2)
        
        # 戻るボタン
        back_rect = (10, self.height - 40, 80, self.height - 10)
        cv2.rectangle(img, (10, self.height - 40), (80, self.height - 10), (100, 100, 100), -1)
        cv2.rectangle(img, (10, self.height - 40), (80, self.height - 10), (255, 255, 255), 1)
        img = put_japanese_text(img, "戻る", (15, self.height - 15), 0.4, (255, 255, 255), 1)
        
        buttons = [('back', back_rect)]
        
        # ファイル一覧
        files = self.get_log_files()
        y_start = 60
        item_height = 40
        
        for i, filename in enumerate(files[:8]):  # 最大8個表示
            y = y_start + i * item_height
            if y + item_height > self.height - 50:
                break
            
            # ファイル名表示
            display_name = filename[:20] + '...' if len(filename) > 20 else filename
            color = (0, 255, 255) if self.selected_file == filename else (200, 200, 200)
            cv2.putText(img, display_name, (20, y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1, cv2.LINE_AA)
            
            # クリック領域
            file_rect = (10, y, self.width - 10, y + item_height)
            buttons.append((f'file_{filename}', file_rect))
        
        return img, buttons
    
    def _draw_view(self, img):
        """ファイル詳細を表示"""
        img = put_japanese_text(img, "データ詳細", (20, 30), 0.7, (255, 255, 255), 2)
        
        if self.selected_file:
            filepath = os.path.join(self.log_dir, self.selected_file)
            if os.path.exists(filepath):
                # ファイル情報を表示
                info_text = f"ファイル: {self.selected_file[:25]}"
                img = put_japanese_text(img, info_text, (20, 70), 0.4, (255, 255, 255), 1)
                
                # ファイルサイズと更新日時
                try:
                    stat = os.stat(filepath)
                    size_kb = stat.st_size / 1024
                    mtime = os.path.getmtime(filepath)
                    from datetime import datetime
                    mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                    img = put_japanese_text(img, f"サイズ: {size_kb:.1f}KB", (20, 95), 0.35, (200, 200, 200), 1)
                    img = put_japanese_text(img, f"更新: {mtime_str}", (20, 115), 0.35, (200, 200, 200), 1)
                    
                    # メモの表示（最新のメモを表示）
                    note = self.get_all_notes()
                    if note:
                        note_preview = note[:30] + '...' if len(note) > 30 else note
                        img = put_japanese_text(img, f"メモ: {note_preview}", (20, 135), 0.3, (200, 200, 255), 1)
                except:
                    pass
        
        # 戻るボタン
        back_rect = (10, self.height - 100, 80, self.height - 70)
        cv2.rectangle(img, (10, self.height - 100), (80, self.height - 70), (100, 100, 100), -1)
        cv2.rectangle(img, (10, self.height - 100), (80, self.height - 70), (255, 255, 255), 1)
        img = put_japanese_text(img, "戻る", (15, self.height - 75), 0.4, (255, 255, 255), 1)
        
        # レポート生成ボタン
        report_rect = (self.width - 100, self.height - 100, self.width - 10, self.height - 70)
        cv2.rectangle(img, (self.width - 100, self.height - 100), (self.width - 10, self.height - 70), (0, 150, 150), -1)
        cv2.rectangle(img, (self.width - 100, self.height - 100), (self.width - 10, self.height - 70), (255, 255, 255), 1)
        img = put_japanese_text(img, "レポート", (self.width - 95, self.height - 75), 0.35, (255, 255, 255), 1)
        
        # メモ編集ボタン
        edit_rect = (10, self.height - 60, 100, self.height - 30)
        cv2.rectangle(img, (10, self.height - 60), (100, self.height - 30), (150, 150, 0), -1)
        cv2.rectangle(img, (10, self.height - 60), (100, self.height - 30), (255, 255, 255), 1)
        img = put_japanese_text(img, "メモ編集", (15, self.height - 35), 0.35, (255, 255, 255), 1)
        
        # 削除ボタン
        delete_rect = (self.width - 100, self.height - 60, self.width - 10, self.height - 30)
        cv2.rectangle(img, (self.width - 100, self.height - 60), (self.width - 10, self.height - 30), (150, 0, 0), -1)
        cv2.rectangle(img, (self.width - 100, self.height - 60), (self.width - 10, self.height - 30), (255, 255, 255), 1)
        img = put_japanese_text(img, "削除", (self.width - 85, self.height - 35), 0.4, (255, 255, 255), 1)
        
        buttons = [('back', back_rect), ('report', report_rect), ('edit', edit_rect), ('delete', delete_rect)]
        return img, buttons
    
    def _draw_edit(self, img):
        """メモ編集画面を描画（仮想キーボード付き）"""
        # 仮想キーボードを描画
        kb_img, kb_buttons = self.keyboard.draw()
        
        # ファイル名表示
        if self.selected_file:
            file_text = f"ファイル: {self.selected_file[:20]}"
            cv2.putText(kb_img, file_text, (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1, cv2.LINE_AA)
        
        return kb_img, kb_buttons
    
    def load_note_from_file(self):
        """ファイルからメモを読み込み（最新のメモを返す）"""
        return self.get_all_notes()
    
    def save_note_to_file(self, note_text):
        """メモをファイルに保存（CSVにイベントとして追加）"""
        if not self.selected_file:
            return False
        
        filepath = os.path.join(self.log_dir, self.selected_file)
        if not os.path.exists(filepath):
            return False
        
        try:
            import csv
            import time
            
            # 空のメモの場合は保存しない
            if not note_text.strip():
                return True
            
            # 新しいメモを追加（既存のメモは保持）
            with open(filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # CSVのヘッダーに合わせて記録
                # メタ情報は既存のファイルから取得できないため、Noneで記録
                writer.writerow([
                    time.time(), 'event',
                    None, None, None, None, None,  # session, participant, task, phase, block_id
                    None, None, None, None, None, None,  # ear関連
                    None, None, None, None, None, None, None,  # gaze関連
                    None, None, 'note', note_text
                ])
            return True
        except Exception as e:
            print(f"Error saving note: {e}")
            return False
    
    def get_all_notes(self):
        """ファイルからすべてのメモを取得（最新のものを返す）"""
        if not self.selected_file:
            return ""
        
        filepath = os.path.join(self.log_dir, self.selected_file)
        if not os.path.exists(filepath):
            return ""
        
        try:
            import csv
            notes = []
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('row_type') == 'event' and row.get('event') == 'note':
                        note_text = row.get('info', '')
                        if note_text:
                            notes.append(note_text)
            
            # 最新のメモを返す（複数ある場合は結合）
            if notes:
                return '\n'.join(notes)
            return ""
        except Exception as e:
            print(f"Error loading notes: {e}")
            return ""
    
    def handle_click(self, x, y, buttons):
        """クリック処理"""
        # メモ編集モードの場合、キーボードのクリック処理
        if self.mode == 'edit':
            result = self.keyboard.handle_click(x, y, buttons)
            if result == 'ok':
                # メモを保存
                note_text = self.keyboard.get_text()
                if self.save_note_to_file(note_text):
                    self.mode = 'view'
                    return 'note_saved'
                else:
                    return 'note_error'
            elif result == 'cancel':
                # 編集をキャンセル
                self.keyboard.set_text(self.original_note)
                self.mode = 'view'
                return None
            return None
        
        # 通常のクリック処理
        for name, (x1, y1, x2, y2) in buttons:
            if x1 <= x <= x2 and y1 <= y <= y2:
                if name == 'back':
                    if self.mode == 'view' or self.mode == 'edit' or self.mode == 'report':
                        if self.mode == 'report':
                            self.mode = 'view'
                        else:
                            self.mode = 'list'
                        return None
                    return 'back'
                elif name == 'report':
                    return 'report'
                elif name == 'prev' or name == 'next':
                    # レポートビューアのページ送り
                    if self.mode == 'report':
                        if name == 'prev':
                            self.report_viewer.prev_page()
                        else:
                            self.report_viewer.next_page()
                    return None
                elif name == 'edit':
                    # メモ編集モードに移行
                    self.original_note = self.load_note_from_file()
                    self.keyboard.set_text(self.original_note)
                    self.mode = 'edit'
                    return None
                elif name == 'delete':
                    return 'delete'
                elif name.startswith('file_'):
                    filename = name.replace('file_', '')
                    self.selected_file = filename
                    self.mode = 'view'
                    return None
        return None
    
    def delete_file(self):
        """選択されたファイルを削除"""
        if self.selected_file:
            filepath = os.path.join(self.log_dir, self.selected_file)
            try:
                os.remove(filepath)
                self.selected_file = None
                self.mode = 'list'
                return True
            except Exception as e:
                print(f"Error deleting file: {e}")
                return False
        return False
    
    def generate_report(self, report_dir='reports'):
        """レポートを生成（画像も保存）"""
        if not self.selected_file:
            return None
        
        filepath = os.path.join(self.log_dir, self.selected_file)
        if not os.path.exists(filepath):
            return None
        
        # レポートファイル名
        report_name = self.selected_file.replace('.csv', '.html')
        report_path = os.path.join(report_dir, report_name)
        os.makedirs(report_dir, exist_ok=True)
        
        # レポート生成スクリプトを呼び出す（画像も保存）
        import subprocess
        try:
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            report_script = os.path.join(script_dir, 'scripts', 'report.py')
            result = subprocess.run(
                ['python', report_script, '--log', filepath, '--out', report_path, 
                 '--save-images', '--image-dir', report_dir],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # レポートビューアに読み込む
                if self.report_viewer.load_report(filepath):
                    return 'viewer_ready'
                return report_path
            else:
                print(f"Report generation error: {result.stderr}")
                return None
        except Exception as e:
            print(f"Error generating report: {e}")
            return None

