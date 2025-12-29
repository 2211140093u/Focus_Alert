import cv2
import numpy as np

class Overlay:
    def __init__(self):
        pass

    def draw(self, frame, feats, score, alert, fps, status=None, show_alert_text=True, cam_status=None, landscape_mode=False):
        vis = frame.copy()
        h, w = vis.shape[:2]
        
        if landscape_mode:
            # 横長画面（480x320）向け：左側にカメラ映像、右側に情報パネル
            # カメラ映像を左側に配置（縦長でトリミング、縦横比を維持）
            frame_h, frame_w = frame.shape[:2]
            frame_aspect = frame_w / frame_h if frame_h > 0 else 1.0
            
            # 左側のカメラ映像エリアの幅を決定（右側に160pxのパネルを確保）
            cam_w_max = w - 160 - 10  # 右側パネル（160px）+ 余白（10px）
            # 縦幅を増やして縦横比を修正（画面の高さより少し大きくする）
            cam_h = int(h * 1.1)  # 縦幅を10%増やす（画面からはみ出すが、縦横比を修正）
            
            # 縦横比を維持して、縦長でトリミングする
            # 元のフレームの中央部分を縦長で切り出す
            if frame_aspect > 1.0:
                # 横長のフレームの場合、中央部分を縦長で切り出す
                target_aspect = cam_w_max / cam_h  # 目標の縦横比
                if frame_aspect > target_aspect:
                    # フレームが横長すぎる場合、中央部分を切り出す
                    crop_w = int(frame_h * target_aspect)
                    crop_x = (frame_w - crop_w) // 2
                    frame_cropped = frame[:, crop_x:crop_x+crop_w]
                else:
                    frame_cropped = frame
            else:
                # 縦長のフレームの場合、そのまま使用
                frame_cropped = frame
            
            # 切り出したフレームをリサイズ（縦横比を維持）
            crop_h, crop_w = frame_cropped.shape[:2]
            scale = min(cam_w_max / crop_w, cam_h / crop_h)
            cam_w = int(crop_w * scale)
            cam_h = int(crop_h * scale)
            
            # 画面内に収まるように調整（縦方向は中央配置、横方向は左端）
            if cam_h > h:
                cam_h = h  # 画面の高さに制限
                # 縦横比を維持して幅を再計算
                cam_w = int(cam_h * (crop_w / crop_h))
            
            frame_resized = cv2.resize(frame_cropped, (cam_w, cam_h), interpolation=cv2.INTER_LINEAR)
            
            # 左側に配置
            cam_x = 0
            cam_y = (h - cam_h) // 2  # 縦方向中央配置
            
            vis = np.zeros((h, w, 3), dtype=np.uint8)
            vis.fill(20)  # 暗い背景
            vis[cam_y:cam_y+cam_h, cam_x:cam_x+cam_w] = frame_resized
            
            # 右側に情報パネル（160x320の領域）
            # 数値表示は右上、ボタンは右下に配置するため、パネルを2つに分ける
            panel_w = 160
            # 数値表示パネル（右上）
            info_panel_h = 200  # 数値表示用の高さ
            info_panel_x = w - panel_w - 10
            info_panel_y = 10
            # ボタンエリア（右下）は draw_buttons で処理
        else:
            # 縦長画面（320×480）向け：従来のレイアウト
            panel_w = min(300, w - 20)
            panel_h = 140
            panel_x = 10
            panel_y = 10
        
        # 半透明の背景（横長モードでは右上の情報パネル）
        overlay_bg = vis.copy()
        if landscape_mode:
            # 右上の情報パネル
            cv2.rectangle(overlay_bg, (info_panel_x, info_panel_y), (info_panel_x + panel_w, info_panel_y + info_panel_h), (0,0,0), -1)
            vis = cv2.addWeighted(vis, 0.2, overlay_bg, 0.8, 0)
            cv2.rectangle(vis, (info_panel_x, info_panel_y), (info_panel_x + panel_w, info_panel_y + info_panel_h), (255,255,255), 1)
            panel_x = info_panel_x
            panel_y = info_panel_y
            panel_h = info_panel_h
        else:
            # 縦長モードでは従来通り
            cv2.rectangle(overlay_bg, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), (0,0,0), -1)
            vis = cv2.addWeighted(vis, 0.3, overlay_bg, 0.7, 0)
            cv2.rectangle(vis, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), (255,255,255), 1)
        
        # フォントサイズ（横長モードでは大きめ）
        font_scale = 0.55 if landscape_mode else 0.4
        font_thickness = 2 if landscape_mode else 1
        line_height = 26 if landscape_mode else 18
        y = panel_y + 15  # 上端の余白を少し減らす
        
        def put(t, color=(255,255,255)):
            nonlocal y
            # 数値欄は省略せず、できるだけそのまま表示する
            # （パネル幅を超えた分は画面側でクリップされる）
            cv2.putText(vis, t, (panel_x + 5, y), cv2.FONT_HERSHEY_SIMPLEX, 
                       font_scale, color, font_thickness, cv2.LINE_AA)
            y += line_height
        
        # カメラ状態表示（リアルタイム確認用）
        if cam_status is not None:
            cam_ok = cam_status.get('connected', False) and cam_status.get('frame_ok', False)
            cam_color = (0, 255, 0) if cam_ok else (0, 0, 255)
            cam_text = f"Cam: {'OK' if cam_ok else 'NG'}"
            if cam_ok:
                cam_text += f" ({cam_status.get('fps', 0):.1f}fps)"
            put(cam_text, cam_color)
        
        # 検出状態
        if status is not None:
            face_ok = status.get('has_face', False)
            iris_ok = feats['gaze'].get('has_iris', False)
            face_color = (0, 255, 0) if face_ok else (0, 0, 255)
            iris_color = (0, 255, 0) if iris_ok else (0, 0, 255)
            put(f"Face: {'OK' if face_ok else 'NO'} | Iris: {'OK' if iris_ok else 'NO'}", 
                (255, 255, 255) if (face_ok and iris_ok) else (0, 0, 255))
        
        # まばたき情報（簡潔に）
        b = feats['blink']
        put(f"Blinks: {b['blink_count']} | EAR: {b['ear']:.2f}")
        if b.get('long_close', False):
            put("Long Close!", (0, 0, 255))
        
        # 視線情報（簡潔に）
        g = feats['gaze']
        gaze_off = g.get('gaze_off', False)
        gaze_color = (0, 0, 255) if gaze_off else (255, 255, 255)
        put(f"Gaze: {g['gaze_horiz']:.2f} | Off: {'YES' if gaze_off else 'NO'}", gaze_color)

        # リスクスコアのバー表示（横長モードでは大きく、情報パネル内に配置）
        if landscape_mode:
            # 横長モードでは情報パネルの下部に配置
            bar_x = panel_x + 5
            bar_y = panel_y + panel_h - 30
            bar_w = panel_w - 10
            bar_h = 20
        else:
            bar_x = panel_x + 5
            bar_y = panel_y + panel_h - 25
            bar_w = panel_w - 10
            bar_h = 15
        
        bar_fill_w = int(bar_w * max(0.0, min(1.0, score)))
        cv2.rectangle(vis, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (80,80,80), 1)
        cv2.rectangle(vis, (bar_x, bar_y), (bar_x + bar_fill_w, bar_y + bar_h), 
                     (0,0,255) if alert else (0,255,0), -1)
        score_text = f"Risk: {score:.2f}"
        score_font_scale = 0.7 if landscape_mode else font_scale
        text_size = cv2.getTextSize(score_text, cv2.FONT_HERSHEY_SIMPLEX, score_font_scale, font_thickness)[0]
        cv2.putText(vis, score_text, (bar_x + (bar_w - text_size[0]) // 2, bar_y - 3), 
                   cv2.FONT_HERSHEY_SIMPLEX, score_font_scale, 
                   (0,0,255) if alert else (0,255,0), font_thickness, cv2.LINE_AA)

        # アラート表示（大きく目立つように）
        if alert and show_alert_text:
            alert_text = "Take a break!"
            text_scale = 0.8
            text_thickness = 2
            text_size = cv2.getTextSize(alert_text, cv2.FONT_HERSHEY_SIMPLEX, text_scale, text_thickness)[0]
            text_x = (w - text_size[0]) // 2
            text_y = int(h * 0.15)
            # テキストの背景を描画
            cv2.rectangle(vis, (text_x - 5, text_y - text_size[1] - 5), 
                         (text_x + text_size[0] + 5, text_y + 5), (0,0,0), -1)
            cv2.putText(vis, alert_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                       text_scale, (0,0,255), text_thickness, cv2.LINE_AA)
        
        return vis

    def draw_buttons(self, frame, states=None, landscape_mode=False):
        # 横長画面（480x320）向けに最適化されたタッチUIボタン
        # 返り値は辞書: 名前 -> (x1,y1,x2,y2)
        vis = frame
        h, w = vis.shape[:2]
        
        if landscape_mode:
            # 横長モード：右側パネルに縦に並べる（全ボタン表示）
            labels = [
                ('start', 'Start'),
                ('end', 'Stop'),
                ('marker', 'Mark'),
                ('distract', 'Dist'),
                ('calib', 'Calib'),
                ('quit', 'Quit'),
            ]
            
            # 右側パネルに縦に配置（右下に配置）
            panel_w = 160
            panel_x = w - panel_w - 10
            pad = 5
            btn_w = panel_w - 20
            btn_h = 40  # ボタン高さを少し小さくして6個収める
            # 右下から配置
            total_btn_height = len(labels) * (btn_h + pad) + pad
            y_start = h - total_btn_height
            
            rects = {}
            for idx, (key, text) in enumerate(labels):
                y1 = y_start + pad + idx * (btn_h + pad)
                x1 = panel_x + 10
                x2 = x1 + btn_w
                y2 = y1 + btn_h
                
                # ボタンの状態に応じた色
                color = (60, 60, 60)
                active = False
                if states and key == 'distract':
                    active = bool(states.get('distract_on', False))
                if active:
                    color = (0, 120, 255)
                elif key == 'quit':
                    color = (120, 60, 60)  # Quitボタンは赤系
                elif key == 'end':
                    color = (60, 120, 60)  # Stopボタンは緑系
                
                # ボタンの描画
                cv2.rectangle(vis, (x1, y1), (x2, y2), (255, 255, 255), 2)
                cv2.rectangle(vis, (x1+2, y1+2), (x2-2, y2-2), color, -1)
                
                # テキストの中央配置（大きく）
                font_scale = 0.7
                font_thickness = 2
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)[0]
                text_x = x1 + (btn_w - text_size[0]) // 2
                text_y = y1 + (btn_h + text_size[1]) // 2
                cv2.putText(vis, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                           font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA)
                
                rects[key] = (x1, y1, x2, y2)
            
            return rects
        
        # 縦長モード：従来の2行×3列レイアウト
        labels = [
            ('start', 'Start'),
            ('end', 'End'),
            ('marker', 'Mark'),
            ('distract', 'Dist'),
            ('calib', 'Calib'),
            ('quit', 'Quit'),
        ]
        
        # ボタンサイズと配置
        pad = 4
        cols = 3
        rows = 2
        bw = (w - pad * (cols + 1)) // cols
        bh = 40  # タッチしやすいサイズ
        button_area_h = rows * bh + pad * (rows + 1)
        y_start = h - button_area_h
        
        rects = {}
        for idx, (key, text) in enumerate(labels):
            row = idx // cols
            col = idx % cols
            x1 = pad + col * (bw + pad)
            y1 = y_start + pad + row * (bh + pad)
            x2 = x1 + bw
            y2 = y1 + bh
            
            # ボタンの状態に応じた色
            color = (60, 60, 60)
            active = False
            if states and key == 'distract':
                active = bool(states.get('distract_on', False))
            if active:
                color = (0, 120, 255)
            elif key == 'quit':
                color = (60, 60, 120)  # Quitボタンは少し違う色
            
            # ボタンの描画
            cv2.rectangle(vis, (x1, y1), (x2, y2), (255, 255, 255), 2)
            cv2.rectangle(vis, (x1+2, y1+2), (x2-2, y2-2), color, -1)
            
            # テキストの中央配置
            font_scale = 0.5
            font_thickness = 1
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)[0]
            text_x = x1 + (bw - text_size[0]) // 2
            text_y = y1 + (bh + text_size[1]) // 2
            cv2.putText(vis, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                       font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA)
            
            rects[key] = (x1, y1, x2, y2)
        
        return rects
