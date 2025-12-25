"""
GUI版のメインアプリケーション
メインメニューから計測開始/データ確認/オプションを選択できる
"""
import argparse
import time
import cv2
import numpy as np
import sys
import os

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from capture import Camera
from mediapipe_wrappers import FaceProcessor
from features.blink import BlinkDetector
from features.gaze import GazeEstimator
from fusion import FusionScorer
from personalize import Personalizer
from overlay import Overlay
from logger import CSVLogger
from gui import MainMenu, OptionsMenu, DataViewer


def run_measurement(args, settings=None):
    """計測を実行"""
    # 設定を適用
    if settings:
        args.ear_threshold_ratio = settings.get('ear_threshold_ratio', args.ear_threshold_ratio)
        args.ear_baseline_init = settings.get('ear_baseline_init', args.ear_baseline_init)
        # リスク閾値とクールダウンはfusion.pyとapp.pyで直接設定する必要がある
    
    try:
        cam = Camera(index=args.cam, width=args.width, height=args.height, fps=30,
                    backend=args.backend, rotate=args.rotate, flip_h=args.flip_h, flip_v=args.flip_v,
                    zmq_url=args.zmq_url, zmq_topic=args.zmq_topic).open()
    except Exception as e:
        print(f"Error: Failed to open camera: {e}")
        return False
    
    face = FaceProcessor(static_mode=False, refine_iris=True, max_faces=1)
    blink = BlinkDetector()
    blink.open_baseline = args.ear_baseline_init
    blink.ear_threshold_ratio = args.ear_threshold_ratio
    gaze = GazeEstimator()
    fusion = FusionScorer()
    # 設定からリスク閾値を適用
    if settings:
        fusion.hi = settings.get('risk_threshold', fusion.hi)
    perso = Personalizer(phase=args.phase, calib_seconds=args.calib_seconds)
    
    try:
        blink.adapt_enabled = (args.phase == 'train') and (args.learning == 'on')
    except Exception:
        pass
    
    overlay = Overlay()
    
    # ログファイルの自動命名
    log_path = args.log if args.log else ('logs' if args.auto_log_name else None)
    logger = CSVLogger(log_path, meta={
        'session': args.session,
        'participant': args.participant,
        'task': args.task,
        'phase': args.phase,
        'ear_threshold_ratio': args.ear_threshold_ratio,
        'ear_baseline_init': args.ear_baseline_init,
        'risk_threshold': fusion.hi,
    }, auto_name=args.auto_log_name) if log_path else None
    
    if logger:
        print(f"Logging to: {logger.path}")
    
    last_alert_time = 0.0
    cooldown_sec = settings.get('cooldown_sec', 60.0) if settings else 60.0
    alert_enabled = (args.alert_mode == 'on')
    block_id = None
    distractor_on = False
    
    # マウス/タッチ入力
    last_click = {'x': None, 'y': None, 'ts': 0}
    win_name = 'Focus Alert - Measurement'
    
    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            last_click['x'] = x
            last_click['y'] = y
            last_click['ts'] = time.time()
        elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):
            last_click['x'] = x
            last_click['y'] = y
            last_click['ts'] = time.time()
    
    # 表示解像度
    if args.display_width is None or args.display_height is None:
        if args.backend == 'zmq':
            display_width = args.display_width if args.display_width else 320
            display_height = args.display_height if args.display_height else 480
        else:
            display_width = args.display_width if args.display_width else args.width
            display_height = args.display_height if args.display_height else args.height
    else:
        display_width = args.display_width
        display_height = args.display_height
    
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, display_width, display_height)
    if args.backend == 'zmq':
        cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    frame_failure_count = 0
    max_failures = 30
    
    while True:
        ok, frame = cam.read()
        if not ok:
            frame_failure_count += 1
            if frame_failure_count >= max_failures:
                print(f"Warning: Camera frame read failed {frame_failure_count} times consecutively.")
            if frame is None:
                frame = np.zeros((args.height, args.width, 3), dtype=np.uint8)
                cv2.putText(frame, "Camera Error", (50, args.height//2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            frame_failure_count = 0
        
        t0 = time.time()
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            fm = face.process(rgb)
        except Exception as e:
            print(f"Error processing frame: {e}")
            fm = None
        
        feats = {}
        status = {
            'has_face': bool(fm and fm.get('has_face', False)),
            'phase': args.phase,
            'calibrating': perso.in_calibration() if args.phase == 'train' else False,
        }
        if fm is not None and fm['landmarks'] is not None:
            lms = fm['landmarks']
            feats['blink'] = blink.update(lms)
            feats['gaze'] = gaze.update(lms)
        else:
            feats['blink'] = blink.miss()
            feats['gaze'] = gaze.miss()
        
        score = fusion.update(feats, perso)
        now = time.time()
        alert = fusion.should_alert(score, now, last_alert_time, cooldown_sec) if alert_enabled else False
        if alert:
            last_alert_time = now
        
        fps = 1.0 / max(1e-3, (time.time() - t0))
        
        cam_status_dict = cam.get_status() if hasattr(cam, 'get_status') else {}
        cam_status = {
            'connected': cam_status_dict.get('connected', cam.impl is not None),
            'frame_ok': ok,
            'fps': fps,
            'consecutive_failures': cam_status_dict.get('consecutive_failures', 0),
        }
        
        vis = overlay.draw(frame, feats, score, alert, fps, status=status, 
                          show_alert_text=alert_enabled, cam_status=cam_status)
        btn_rects = overlay.draw_buttons(vis, states={'distract_on': distractor_on})
        
        if logger:
            logger.write_frame(feats, score, alert, block_id=block_id)
        
        # フレームを表示解像度にリサイズ
        h, w = vis.shape[:2]
        target_w, target_h = display_width, display_height
        
        if w == target_w and h == target_h:
            vis_display = vis
            btn_rects_scaled = btn_rects
        else:
            scale = min(target_w / w, target_h / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            vis_resized = cv2.resize(vis, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            vis_display = np.zeros((target_h, target_w, 3), dtype=np.uint8)
            y_offset = (target_h - new_h) // 2
            x_offset = (target_w - new_w) // 2
            vis_display[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = vis_resized
            
            btn_rects_scaled = {}
            for name, (x1, y1, x2, y2) in btn_rects.items():
                btn_rects_scaled[name] = (
                    int(x1 * scale + x_offset),
                    int(y1 * scale + y_offset),
                    int(x2 * scale + x_offset),
                    int(y2 * scale + y_offset)
                )
        
        cv2.imshow(win_name, vis_display)
        cv2.setMouseCallback(win_name, on_mouse)
        key = cv2.waitKey(1) & 0xFF
        
        if last_click['x'] is not None:
            x, y = last_click['x'], last_click['y']
            last_click['x'] = None
            for name, (x1,y1,x2,y2) in btn_rects_scaled.items():
                if x1 <= x <= x2 and y1 <= y <= y2:
                    if name == 'start':
                        key = ord('s')
                    elif name == 'end':
                        key = ord('e')
                    elif name == 'marker':
                        key = ord('m')
                    elif name == 'distract':
                        key = ord('d')
                    elif name == 'calib':
                        key = ord('c')
                    elif name == 'quit':
                        key = ord('q')
                    break
        
        if key == ord('q'):
            break
        if key == ord('c'):
            gaze.calibrate_center()
            if logger:
                logger.write_event('calibrate_center', block_id=block_id)
        if key == ord('s'):
            block_id = 1 if block_id is None else (block_id + 1)
            if logger:
                logger.write_event('block_start', info=f'block={block_id}', block_id=block_id)
        if key == ord('e'):
            if logger:
                logger.write_event('block_end', info=f'block={block_id}', block_id=block_id)
        if key == ord('m'):
            if logger:
                logger.write_event('marker', block_id=block_id)
        if key == ord('d'):
            distractor_on = not distractor_on
            if logger:
                logger.write_event('distractor_start' if distractor_on else 'distractor_end', block_id=block_id)
    
    cam.release()
    cv2.destroyAllWindows()
    return True


def main_gui():
    """GUI版のメイン関数"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--cam', type=int, default=0)
    parser.add_argument('--width', type=int, default=640)
    parser.add_argument('--height', type=int, default=480)
    parser.add_argument('--display-width', type=int, default=320)
    parser.add_argument('--display-height', type=int, default=480)
    parser.add_argument('--backend', type=str, default='zmq', choices=['auto','opencv','picamera2','zmq'])
    parser.add_argument('--log-dir', type=str, default='logs')
    parser.add_argument('--config-dir', type=str, default='config')
    args = parser.parse_args()
    
    # 設定の読み込み
    settings_path = os.path.join(args.config_dir, 'settings.json')
    options_menu = OptionsMenu(width=args.display_width, height=args.display_height)
    options_menu.load_settings(settings_path)
    
    # データビューア
    data_viewer = DataViewer(width=args.display_width, height=args.display_height, log_dir=args.log_dir)
    
    # メインメニュー
    main_menu = MainMenu(width=args.display_width, height=args.display_height)
    
    win_name = 'Focus Alert - Main Menu'
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, args.display_width, args.display_height)
    cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    last_click = {'x': None, 'y': None, 'ts': 0}
    current_screen = 'main'  # 'main', 'measure', 'data', 'options'
    
    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            last_click['x'] = x
            last_click['y'] = y
            last_click['ts'] = time.time()
        elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):
            last_click['x'] = x
            last_click['y'] = y
            last_click['ts'] = time.time()
    
    cv2.setMouseCallback(win_name, on_mouse)
    
    while True:
        if current_screen == 'main':
            img, buttons = main_menu.draw()
            cv2.imshow(win_name, img)
            
            if last_click['x'] is not None:
                x, y = last_click['x'], last_click['y']
                last_click['x'] = None
                selected = main_menu.handle_click(x, y, buttons)
                if selected == 'measure':
                    current_screen = 'measure'
                    cv2.destroyWindow(win_name)
                elif selected == 'data':
                    current_screen = 'data'
                elif selected == 'options':
                    current_screen = 'options'
        
        elif current_screen == 'measure':
            # 計測を開始
            measure_args = argparse.Namespace(
                cam=args.cam,
                width=args.width,
                height=args.height,
                display_width=args.display_width,
                display_height=args.display_height,
                backend=args.backend,
                rotate=0,
                flip_h=False,
                flip_v=False,
                zmq_url='tcp://127.0.0.1:5555',
                zmq_topic='frame',
                session=None,
                participant=None,
                task=None,
                phase='eval',
                calib_seconds=60,
                model_save=None,
                model_load=None,
                learning='off',
                alert_mode='on',
                log=None,
                auto_log_name=True,
                ear_threshold_ratio=options_menu.settings.get('ear_threshold_ratio', 0.90),
                ear_baseline_init=options_menu.settings.get('ear_baseline_init', 0.45),
            )
            run_measurement(measure_args, settings=options_menu.settings)
            current_screen = 'main'
            cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(win_name, args.display_width, args.display_height)
            cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.setMouseCallback(win_name, on_mouse)
        
        elif current_screen == 'data':
            img, buttons = data_viewer.draw()
            cv2.imshow(win_name, img)
            
            if last_click['x'] is not None:
                x, y = last_click['x'], last_click['y']
                last_click['x'] = None
                result = data_viewer.handle_click(x, y, buttons)
                if result == 'back':
                    if data_viewer.mode == 'report':
                        data_viewer.mode = 'view'
                    else:
                        current_screen = 'main'
                elif result == 'report':
                    # レポート生成
                    report_result = data_viewer.generate_report()
                    if report_result == 'viewer_ready':
                        # レポートビューアを起動
                        data_viewer.mode = 'report'
                    elif report_result:
                        print(f"Report generated: {report_result}")
                        # レポート表示（簡易版：パスを表示）
                        img, _ = data_viewer.draw()
                        cv2.putText(img, "Report generated!", (20, 150), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
                        cv2.imshow(win_name, img)
                        cv2.waitKey(2000)  # 2秒表示
                    else:
                        img, _ = data_viewer.draw()
                        cv2.putText(img, "Report failed!", (20, 150), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA)
                        cv2.imshow(win_name, img)
                        cv2.waitKey(2000)
                elif result == 'delete':
                    # 削除確認（簡易版：即座に削除）
                    if data_viewer.delete_file():
                        print("File deleted")
                    else:
                        print("Failed to delete file")
                elif result == 'note_saved':
                    # メモが保存された
                    print(f"Note saved for {data_viewer.selected_file}")
                    # 成功メッセージを表示（簡易版）
                    img, _ = data_viewer.draw()
                    cv2.putText(img, "Note saved!", (20, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
                    cv2.imshow(win_name, img)
                    cv2.waitKey(1500)  # 1.5秒表示
                elif result == 'note_error':
                    # メモ保存エラー
                    print("Failed to save note")
                    img, _ = data_viewer.draw()
                    cv2.putText(img, "Save failed!", (20, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA)
                    cv2.imshow(win_name, img)
                    cv2.waitKey(1500)
                elif result == 'prev' or result == 'next':
                    # レポートビューアのページ送り（既に処理済み）
                    pass
            
            # キーボード操作（レポートビューア用）
            if data_viewer.mode == 'report':
                key = cv2.waitKey(1) & 0xFF
                if key == ord('a') or key == ord('A'):  # 前のページ
                    data_viewer.report_viewer.prev_page()
                elif key == ord('d') or key == ord('D'):  # 次のページ
                    data_viewer.report_viewer.next_page()
        
        elif current_screen == 'options':
            img, buttons = options_menu.draw()
            cv2.imshow(win_name, img)
            
            if last_click['x'] is not None:
                x, y = last_click['x'], last_click['y']
                last_click['x'] = None
                result = options_menu.handle_click(x, y, buttons)
                if result == 'back':
                    current_screen = 'main'
                elif result == 'save':
                    options_menu.save_settings(settings_path)
                    print(f"Settings saved to {settings_path}")
                    current_screen = 'main'
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') and current_screen == 'main':
            break
    
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main_gui()

