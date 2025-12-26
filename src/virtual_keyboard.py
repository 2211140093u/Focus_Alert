"""
仮想キーボード（メモ入力用）
3.5インチタッチモニタ（320×480）向けに最適化
"""
import cv2
import numpy as np
# from japanese_text import put_japanese_text, get_text_size_japanese  # English mode


class VirtualKeyboard:
    """仮想キーボード"""
    
    def __init__(self, width=320, height=480):
        self.width = width
        self.height = height
        self.text = ""  # 入力中のテキスト
        self.cursor_pos = 0  # カーソル位置
        self.shift = False  # シフトキーの状態
        self.mode = 'alpha'  # 'alpha'（英数字）、'symbol'（記号）、'kana'（かな）
        self.romaji_buffer = ""  # ローマ字入力バッファ
        
        # キーボードレイアウト
        self.alpha_layout = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
            ['z', 'x', 'c', 'v', 'b', 'n', 'm'],
        ]
        
        self.symbol_layout = [
            ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')'],
            ['-', '_', '=', '+', '[', ']', '{', '}', '\\', '|'],
            [';', ':', '"', "'", ',', '.', '?', '/'],
            ['~', '`', '<', '>'],
        ]
        
        # かなキーボードレイアウト（50音順）
        self.kana_layout = [
            ['あ', 'い', 'う', 'え', 'お'],
            ['か', 'き', 'く', 'け', 'こ'],
            ['さ', 'し', 'す', 'せ', 'そ'],
            ['た', 'ち', 'つ', 'て', 'と'],
            ['な', 'に', 'ぬ', 'ね', 'の'],
            ['は', 'ひ', 'ふ', 'へ', 'ほ'],
            ['ま', 'み', 'む', 'め', 'も'],
            ['や', '（', 'ゆ', '）', 'よ'],
            ['ら', 'り', 'る', 'れ', 'ろ'],
            ['わ', 'を', 'ん', 'ー', '、'],
        ]
        
        # ローマ字→かな変換テーブル（簡易版）
        self.romaji_to_kana = {
            'a': 'あ', 'i': 'い', 'u': 'う', 'e': 'え', 'o': 'お',
            'ka': 'か', 'ki': 'き', 'ku': 'く', 'ke': 'け', 'ko': 'こ',
            'sa': 'さ', 'si': 'し', 'shi': 'し', 'su': 'す', 'se': 'せ', 'so': 'そ',
            'ta': 'た', 'ti': 'ち', 'chi': 'ち', 'tu': 'つ', 'tsu': 'つ', 'te': 'て', 'to': 'と',
            'na': 'な', 'ni': 'に', 'nu': 'ぬ', 'ne': 'ね', 'no': 'の',
            'ha': 'は', 'hi': 'ひ', 'hu': 'ふ', 'fu': 'ふ', 'he': 'へ', 'ho': 'ほ',
            'ma': 'ま', 'mi': 'み', 'mu': 'む', 'me': 'め', 'mo': 'も',
            'ya': 'や', 'yu': 'ゆ', 'yo': 'よ',
            'ra': 'ら', 'ri': 'り', 'ru': 'る', 're': 'れ', 'ro': 'ろ',
            'wa': 'わ', 'wo': 'を', 'n': 'ん',
            'ga': 'が', 'gi': 'ぎ', 'gu': 'ぐ', 'ge': 'げ', 'go': 'ご',
            'za': 'ざ', 'ji': 'じ', 'zi': 'じ', 'zu': 'ず', 'ze': 'ぜ', 'zo': 'ぞ',
            'da': 'だ', 'di': 'ぢ', 'du': 'づ', 'de': 'で', 'do': 'ど',
            'ba': 'ば', 'bi': 'び', 'bu': 'ぶ', 'be': 'べ', 'bo': 'ぼ',
            'pa': 'ぱ', 'pi': 'ぴ', 'pu': 'ぷ', 'pe': 'ぺ', 'po': 'ぽ',
            'kya': 'きゃ', 'kyu': 'きゅ', 'kyo': 'きょ',
            'sha': 'しゃ', 'shu': 'しゅ', 'sho': 'しょ',
            'cha': 'ちゃ', 'chu': 'ちゅ', 'cho': 'ちょ',
            'nya': 'にゃ', 'nyu': 'にゅ', 'nyo': 'にょ',
            'hya': 'ひゃ', 'hyu': 'ひゅ', 'hyo': 'ひょ',
            'mya': 'みゃ', 'myu': 'みゅ', 'myo': 'みょ',
            'rya': 'りゃ', 'ryu': 'りゅ', 'ryo': 'りょ',
            'gya': 'ぎゃ', 'gyu': 'ぎゅ', 'gyo': 'ぎょ',
            'ja': 'じゃ', 'ju': 'じゅ', 'jo': 'じょ',
            'bya': 'びゃ', 'byu': 'びゅ', 'byo': 'びょ',
            'pya': 'ぴゃ', 'pyu': 'ぴゅ', 'pyo': 'ぴょ',
        }
        
    def draw(self):
        """キーボードを描画"""
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        img.fill(30)  # 暗い背景
        
        # タイトル
        title = "Note Input"
        cv2.putText(img, title, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        
        # テキスト表示エリア
        text_area_y = 50
        text_area_h = 60
        cv2.rectangle(img, (5, text_area_y), (self.width - 5, text_area_y + text_area_h), (50, 50, 50), -1)
        cv2.rectangle(img, (5, text_area_y), (self.width - 5, text_area_y + text_area_h), (200, 200, 200), 2)
        
        # 入力テキストの表示（折り返し対応）
        text_lines = self._wrap_text(self.text, max_width=self.width - 20)
        y_offset = text_area_y + 20
        for i, line in enumerate(text_lines[:2]):  # 最大2行表示
            cv2.putText(img, line, (10, y_offset + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
        
        # カーソル表示（点滅効果のため、時間ベースで表示/非表示を切り替え）
        import time
        cursor_visible = int(time.time() * 2) % 2 == 0  # 0.5秒ごとに点滅
        if cursor_visible:
            cursor_x = 10 + self._get_cursor_x()
            if cursor_x < self.width - 10:
                cv2.line(img, (cursor_x, text_area_y + 10), (cursor_x, text_area_y + text_area_h - 10), (0, 255, 255), 2)
                # カーソルの上に小さな三角形を描画（より見やすく）
                cv2.line(img, (cursor_x - 3, text_area_y + 5), (cursor_x, text_area_y + 10), (0, 255, 255), 1)
                cv2.line(img, (cursor_x + 3, text_area_y + 5), (cursor_x, text_area_y + 10), (0, 255, 255), 1)
        
        # キーボードエリア
        keyboard_y = text_area_y + text_area_h + 10
        keyboard_h = self.height - keyboard_y - 50
        
        # 現在のレイアウトを取得
        if self.mode == 'alpha':
            layout = self.alpha_layout
        elif self.mode == 'symbol':
            layout = self.symbol_layout
        else:  # kana
            layout = self.kana_layout
        
        # キーのサイズ計算（かなモードは少し小さく）
        if self.mode == 'kana':
            key_height = 32
            key_spacing = 2
        else:
            key_height = 35
            key_spacing = 3
        buttons = {}
        
        # 各行を描画
        y = keyboard_y
        for row_idx, row in enumerate(layout):
            row_width = len(row) * (key_height + key_spacing) - key_spacing
            x_start = (self.width - row_width) // 2
            
            for col_idx, key_char in enumerate(row):
                x = x_start + col_idx * (key_height + key_spacing)
                
                # キーの描画
                key_rect = (x, y, x + key_height, y + key_height)
                cv2.rectangle(img, (x, y), (x + key_height, y + key_height), (80, 80, 80), -1)
                cv2.rectangle(img, (x, y), (x + key_height, y + key_height), (150, 150, 150), 1)
                
                # キーの文字（シフト時は大文字、かなモードはそのまま）
                if self.mode == 'kana':
                    display_char = key_char
                    font_scale = 0.6
                else:
                    display_char = key_char.upper() if (self.shift and self.mode == 'alpha') else key_char
                    font_scale = 0.5
                (text_w, text_h), _ = cv2.getTextSize(display_char, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
                text_x = x + (key_height - text_w) // 2
                text_y = y + (key_height + text_h) // 2
                cv2.putText(img, display_char, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 1, cv2.LINE_AA)
                
                buttons[f'key_{key_char}'] = key_rect
            
            y += key_height + key_spacing
        
        # 機能キー行
        func_y = y + 10
        
        # スペースキー（カーソルキーの右に配置）
        space_w = 100
        space_x = right_arrow_x + arrow_w + 5
        space_rect = (space_x, func_y, space_x + space_w, func_y + key_height)
        cv2.rectangle(img, (space_x, func_y), (space_x + space_w, func_y + key_height), (80, 80, 80), -1)
        cv2.rectangle(img, (space_x, func_y), (space_x + space_w, func_y + key_height), (150, 150, 150), 1)
        cv2.putText(img, "SPACE", (space_x + 20, func_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
        buttons['key_space'] = space_rect
        
        # 削除キー（Backspace）
        del_w = 60
        del_x = space_x + space_w + 5
        del_rect = (del_x, func_y, del_x + del_w, func_y + key_height)
        cv2.rectangle(img, (del_x, func_y), (del_x + del_w, func_y + key_height), (100, 50, 50), -1)
        cv2.rectangle(img, (del_x, func_y), (del_x + del_w, func_y + key_height), (150, 150, 150), 1)
        cv2.putText(img, "DEL", (del_x + 10, func_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
        buttons['key_backspace'] = del_rect
        
        # シフトキー
        shift_w = 50
        shift_x = space_x - shift_w - 5
        shift_rect = (shift_x, func_y, shift_x + shift_w, func_y + key_height)
        shift_color = (100, 100, 50) if self.shift else (80, 80, 80)
        cv2.rectangle(img, (shift_x, func_y), (shift_x + shift_w, func_y + key_height), shift_color, -1)
        cv2.rectangle(img, (shift_x, func_y), (shift_x + shift_w, func_y + key_height), (150, 150, 150), 1)
        cv2.putText(img, "SHIFT", (shift_x + 2, func_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1, cv2.LINE_AA)
        buttons['key_shift'] = shift_rect
        
        # モード切替キー（英数字/記号/かな）
        mode_w = 50
        mode_x = 5
        mode_rect = (mode_x, func_y, mode_x + mode_w, func_y + key_height)
        if self.mode == 'symbol':
            mode_color = (50, 100, 100)
        elif self.mode == 'kana':
            mode_color = (100, 50, 100)
        else:
            mode_color = (80, 80, 80)
        cv2.rectangle(img, (mode_x, func_y), (mode_x + mode_w, func_y + key_height), mode_color, -1)
        cv2.rectangle(img, (mode_x, func_y), (mode_x + mode_w, func_y + key_height), (150, 150, 150), 1)
        if self.mode == 'alpha':
            mode_text = "記号"
        elif self.mode == 'symbol':
            mode_text = "かな"
        else:  # kana
            mode_text = "ABC"
        cv2.putText(img, mode_text, (mode_x + 5, func_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1, cv2.LINE_AA)
        buttons['key_mode'] = mode_rect
        
        # カーソル移動キー（左右矢印）
        arrow_w = 30
        arrow_h = key_height
        # 左矢印
        left_arrow_x = mode_x + mode_w + 5
        left_arrow_rect = (left_arrow_x, func_y, left_arrow_x + arrow_w, func_y + arrow_h)
        cv2.rectangle(img, (left_arrow_x, func_y), (left_arrow_x + arrow_w, func_y + arrow_h), (80, 80, 80), -1)
        cv2.rectangle(img, (left_arrow_x, func_y), (left_arrow_x + arrow_w, func_y + arrow_h), (150, 150, 150), 1)
        cv2.putText(img, "<", (left_arrow_x + 8, func_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        buttons['key_left'] = left_arrow_rect
        
        # 右矢印
        right_arrow_x = left_arrow_x + arrow_w + 3
        right_arrow_rect = (right_arrow_x, func_y, right_arrow_x + arrow_w, func_y + arrow_h)
        cv2.rectangle(img, (right_arrow_x, func_y), (right_arrow_x + arrow_w, func_y + arrow_h), (80, 80, 80), -1)
        cv2.rectangle(img, (right_arrow_x, func_y), (right_arrow_x + arrow_w, func_y + arrow_h), (150, 150, 150), 1)
        cv2.putText(img, ">", (right_arrow_x + 8, func_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        buttons['key_right'] = right_arrow_rect
        
        # 確定ボタン
        ok_w = 60
        ok_x = self.width - ok_w - 5
        ok_rect = (ok_x, func_y, ok_x + ok_w, func_y + key_height)
        cv2.rectangle(img, (ok_x, func_y), (ok_x + ok_w, func_y + key_height), (0, 150, 0), -1)
        cv2.rectangle(img, (ok_x, func_y), (ok_x + ok_w, func_y + key_height), (150, 150, 150), 1)
        cv2.putText(img, "OK", (ok_x + 10, func_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
        buttons['key_ok'] = ok_rect
        
        # キャンセルボタン
        cancel_w = 50
        cancel_x = ok_x - cancel_w - 5
        cancel_rect = (cancel_x, func_y, cancel_x + cancel_w, func_y + key_height)
        cv2.rectangle(img, (cancel_x, func_y), (cancel_x + cancel_w, func_y + key_height), (150, 0, 0), -1)
        cv2.rectangle(img, (cancel_x, func_y), (cancel_x + cancel_w, func_y + key_height), (150, 150, 150), 1)
        cv2.putText(img, "Cancel", (cancel_x + 5, func_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)
        buttons['key_cancel'] = cancel_rect
        
        return img, buttons
    
    def _wrap_text(self, text, max_width):
        """テキストを折り返し（文字幅を正確に計算）"""
        lines = []
        current_line = ""
        current_width = 0
        
        for char in text:
            # 文字幅の計算（英数字: 8px、かな: 12px）
            if ord(char) >= 0x3040 and ord(char) <= 0x309F:  # ひらがな
                char_width = 12
            elif ord(char) >= 0x30A0 and ord(char) <= 0x30FF:  # カタカナ
                char_width = 12
            elif ord(char) >= 0x4E00 and ord(char) <= 0x9FFF:  # 漢字
                char_width = 12
            else:
                char_width = 8
            
            if current_width + char_width > max_width and current_line:
                lines.append(current_line)
                current_line = char
                current_width = char_width
            else:
                current_line += char
                current_width += char_width
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [""]
    
    def _get_cursor_x(self):
        """カーソルのX座標を取得（より正確に計算）"""
        text_before_cursor = self.text[:self.cursor_pos]
        if not text_before_cursor:
            return 0
        
        # 現在の行のテキストを取得
        lines = self._wrap_text(self.text, max_width=self.width - 20)
        if not lines:
            return 0
        
        # カーソル位置がどの行にあるか計算
        char_count = 0
        for line_idx, line in enumerate(lines):
            if char_count + len(line) >= self.cursor_pos:
                # この行にある
                pos_in_line = self.cursor_pos - char_count
                # 行内の位置からX座標を計算
                line_text = line[:pos_in_line]
                # 文字幅を正確に計算
                width = 0
                for c in line_text:
                    if ord(c) >= 0x3040 and ord(c) <= 0x309F:  # ひらがな
                        width += 12
                    elif ord(c) >= 0x30A0 and ord(c) <= 0x30FF:  # カタカナ
                        width += 12
                    elif ord(c) >= 0x4E00 and ord(c) <= 0x9FFF:  # 漢字
                        width += 12
                    else:
                        width += 8
                return width
            char_count += len(line)
        
        # 最後の行の末尾
        if lines:
            last_line = lines[-1]
            width = 0
            for c in last_line:
                if ord(c) >= 0x3040 and ord(c) <= 0x309F:  # ひらがな
                    width += 12
                elif ord(c) >= 0x30A0 and ord(c) <= 0x30FF:  # カタカナ
                    width += 12
                elif ord(c) >= 0x4E00 and ord(c) <= 0x9FFF:  # 漢字
                    width += 12
                else:
                    width += 8
            return width
        return 0
    
    def handle_click(self, x, y, buttons):
        """クリック処理"""
        for name, (x1, y1, x2, y2) in buttons.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                if name == 'key_space':
                    self.insert_char(' ')
                    return None
                elif name == 'key_backspace':
                    self.backspace()
                    return None
                elif name == 'key_shift':
                    self.shift = not self.shift
                    return None
                elif name == 'key_mode':
                    # モード切替: alpha -> symbol -> kana -> alpha
                    if self.mode == 'alpha':
                        self.mode = 'symbol'
                    elif self.mode == 'symbol':
                        self.mode = 'kana'
                    else:  # kana
                        self.mode = 'alpha'
                    self.shift = False  # モード切替時はシフトを解除
                    self.romaji_buffer = ""  # ローマ字バッファをクリア
                    return None
                elif name == 'key_left':
                    self.move_cursor(-1)
                    return None
                elif name == 'key_right':
                    self.move_cursor(1)
                    return None
                elif name == 'key_ok':
                    return 'ok'
                elif name == 'key_cancel':
                    return 'cancel'
                elif name.startswith('key_'):
                    char = name.replace('key_', '')
                    if self.mode == 'kana':
                        # かな入力
                        self.insert_kana(char)
                    elif self.mode == 'alpha' and self.shift:
                        char = char.upper()
                        self.insert_char(char)
                        # シフトキーは1回の入力で自動解除
                        if self.shift:
                            self.shift = False
                    else:
                        self.insert_char(char)
                    return None
        return None
    
    def insert_char(self, char):
        """文字を挿入"""
        self.text = self.text[:self.cursor_pos] + char + self.text[self.cursor_pos:]
        self.cursor_pos += 1
    
    def insert_kana(self, kana):
        """かなを挿入（直接入力）"""
        self.text = self.text[:self.cursor_pos] + kana + self.text[self.cursor_pos:]
        self.cursor_pos += len(kana)
    
    def insert_romaji(self, char):
        """ローマ字を入力（かなに変換）"""
        self.romaji_buffer += char.lower()
        
        # ローマ字→かな変換を試行
        converted = self._convert_romaji(self.romaji_buffer)
        if converted:
            # 変換成功：バッファをクリアしてかなを挿入
            self.romaji_buffer = ""
            self.insert_kana(converted)
        elif len(self.romaji_buffer) > 3:
            # 3文字以上で変換できない場合は、最初の1文字をそのまま挿入
            first_char = self.romaji_buffer[0]
            self.romaji_buffer = self.romaji_buffer[1:]
            self.insert_char(first_char)
    
    def _convert_romaji(self, romaji):
        """ローマ字をかなに変換（簡易版）"""
        # 長いものから順にマッチング
        for length in range(min(len(romaji), 3), 0, -1):
            substr = romaji[:length]
            if substr in self.romaji_to_kana:
                return self.romaji_to_kana[substr]
        return None
    
    def move_cursor(self, direction):
        """カーソルを移動（-1: 左、1: 右）"""
        new_pos = self.cursor_pos + direction
        self.cursor_pos = max(0, min(len(self.text), new_pos))
    
    def backspace(self):
        """バックスペース（1文字削除）"""
        if self.cursor_pos > 0:
            self.text = self.text[:self.cursor_pos - 1] + self.text[self.cursor_pos:]
            self.cursor_pos -= 1
    
    def set_text(self, text):
        """テキストを設定"""
        self.text = text
        self.cursor_pos = len(text)
    
    def get_text(self):
        """入力されたテキストを取得"""
        return self.text
    
    def clear(self):
        """入力をクリア"""
        self.text = ""
        self.cursor_pos = 0
        self.shift = False
        self.mode = 'alpha'
        self.romaji_buffer = ""

