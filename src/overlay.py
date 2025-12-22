import cv2

class Overlay:
    def __init__(self):
        pass

    def draw(self, frame, feats, score, alert, fps, status=None, show_alert_text=True):
        vis = frame.copy()
        h, w = vis.shape[:2]
        # 情報パネル描画
        cv2.rectangle(vis, (10, 10), (400, 170), (0,0,0), -1)
        cv2.rectangle(vis, (10, 10), (400, 170), (255,255,255), 1)
        y = 35
        def put(t):
            nonlocal y
            cv2.putText(vis, t, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)
            y += 22
        put(f"FPS: {fps:.1f}")
        if status is not None:
            put(f"Face: {'YES' if status.get('has_face', False) else 'NO'} | Iris: {'YES' if feats['gaze'].get('has_iris', False) else 'NO'}")
        b = feats['blink']
        g = feats['gaze']
        put(f"EAR: {b['ear']:.3f} base={b.get('ear_baseline',0):.3f} thr={b.get('ear_thresh',0):.3f} closed={b['is_closed']}")
        put(f"Blinks: {b['blink_count']} long={b['long_close']}")
        put(f"GazeX: {g['gaze_horiz']:.2f} thr={g.get('gaze_thresh',0):.2f} bias={g.get('gaze_bias',0):.2f}")
        put(f"GazeY: {g.get('gaze_y',0.0):.2f} thr={g.get('gaze_y_thresh',0.0):.2f} bias={g.get('gaze_bias_y',0.0):.2f} offlvl={g.get('gaze_off_level',0):.2f}")

        # リスクスコアのバー表示
        bar_w = int(250 * max(0.0, min(1.0, score)))
        cv2.rectangle(vis, (20, 140), (270, 150), (80,80,80), 1)
        cv2.rectangle(vis, (20, 140), (20+bar_w, 150), (0,0,255) if alert else (0,255,0), -1)
        cv2.putText(vis, f"Risk {score:.2f}", (280, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255) if alert else (0,255,0), 1, cv2.LINE_AA)

        if alert and show_alert_text:
            cv2.putText(vis, "Take a short break", (int(w*0.25), int(h*0.1)), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 2, cv2.LINE_AA)
        return vis

    def draw_buttons(self, frame, states=None):
        # 簡易タッチUIボタン: Start, End, Marker, Distract, Calib, Quit
        # 返り値は辞書: 名前 -> (x1,y1,x2,y2)
        vis = frame
        h, w = vis.shape[:2]
        labels = [
            ('start', 'Start'),
            ('end', 'End'),
            ('marker', 'Marker'),
            ('distract', 'Distract'),
            ('calib', 'Calib'),
            ('quit', 'Quit'),
        ]
        pad = 6
        bw = max(70, int(w/7))
        bh = 36
        y1 = h - bh - pad
        rects = {}
        for i, (key, text) in enumerate(labels):
            x1 = pad + i * (bw + pad)
            x2 = min(w - pad, x1 + bw)
            x1 = max(pad, x1)
            color = (60,60,60)
            active = False
            if states and key == 'distract':
                active = bool(states.get('distract_on', False))
            cv2.rectangle(vis, (x1, y1), (x2, y1+bh), (255,255,255), 1)
            cv2.rectangle(vis, (x1+1, y1+1), (x2-1, y1+bh-1), (0,120,255) if active else color, -1)
            cv2.putText(vis, text, (x1+8, y1+bh-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)
            rects[key] = (x1, y1, x2, y1+bh)
        return rects
