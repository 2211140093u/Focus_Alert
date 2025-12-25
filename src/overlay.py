import cv2
import numpy as np

class Overlay:
    def __init__(self):
        pass

    def draw(self, frame, feats, score, alert, fps, status=None, show_alert_text=True, cam_status=None):
        vis = frame.copy()
        h, w = vis.shape[:2]
        
        # 3.5インチタッチモニタ（320×480）向けに最適化された情報パネル
        # パネルサイズを小さくして、重要な情報のみ表示
        panel_w = min(300, w - 20)
        panel_h = 140
        panel_x = 10
        panel_y = 10
        
        # 半透明の背景
        overlay_bg = vis.copy()
        cv2.rectangle(overlay_bg, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), (0,0,0), -1)
        vis = cv2.addWeighted(vis, 0.3, overlay_bg, 0.7, 0)
        cv2.rectangle(vis, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), (255,255,255), 1)
        
        # フォントサイズを小さく（0.4）
        font_scale = 0.4
        font_thickness = 1
        line_height = 18
        y = panel_y + 20
        
        def put(t, color=(255,255,255)):
            nonlocal y
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

        # リスクスコアのバー表示（コンパクトに）
        bar_x = panel_x + 5
        bar_y = panel_y + panel_h - 25
        bar_w = panel_w - 10
        bar_h = 15
        bar_fill_w = int(bar_w * max(0.0, min(1.0, score)))
        cv2.rectangle(vis, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (80,80,80), 1)
        cv2.rectangle(vis, (bar_x, bar_y), (bar_x + bar_fill_w, bar_y + bar_h), 
                     (0,0,255) if alert else (0,255,0), -1)
        score_text = f"Risk: {score:.2f}"
        text_size = cv2.getTextSize(score_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)[0]
        cv2.putText(vis, score_text, (bar_x + (bar_w - text_size[0]) // 2, bar_y - 3), 
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, 
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

    def draw_buttons(self, frame, states=None):
        # 3.5インチタッチモニタ（320×480）向けに最適化されたタッチUIボタン
        # 返り値は辞書: 名前 -> (x1,y1,x2,y2)
        vis = frame
        h, w = vis.shape[:2]
        
        # ボタン配置: 2行×3列で6個のボタン
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
