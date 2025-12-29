import argparse
import time
import cv2
import numpy as np

from capture import Camera
from mediapipe_wrappers import FaceProcessor
from features.blink import BlinkDetector
from features.gaze import GazeEstimator
from fusion import FusionScorer
from personalize import Personalizer
from overlay import Overlay
from logger import CSVLogger


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--cam', type=int, default=0)
    p.add_argument('--width', type=int, default=640, help='カメラから取得するフレームの幅（ピクセル）')
    p.add_argument('--height', type=int, default=480, help='カメラから取得するフレームの高さ（ピクセル）')
    p.add_argument('--display-width', type=int, default=None, help='表示ウィンドウの幅（未指定時はカメラ解像度または320×480）')
    p.add_argument('--display-height', type=int, default=None, help='表示ウィンドウの高さ（未指定時はカメラ解像度または320×480）')
    p.add_argument('--display', action='store_true', default=True)
    p.add_argument('--log', type=str, default=None, help='CSVの保存先（例: logs/run.csv、ディレクトリのみ指定で自動命名）')
    p.add_argument('--auto-log-name', action='store_true', default=True, help='ログファイル名を自動生成（日時ベース）')
    p.add_argument('--alert-mode', type=str, default='on', choices=['on','off'], help='off にするとアラート表示を無効化')
    # カメラのバックエンド/向き（Raspberry Pi を想定）
    p.add_argument('--backend', type=str, default='auto', choices=['auto','opencv','picamera2','zmq'], help='使用するカメラバックエンド')
    p.add_argument('--rotate', type=int, default=0, choices=[0,90,180,270], help='フレームの回転角（度）')
    p.add_argument('--flip-h', action='store_true', help='左右反転')
    p.add_argument('--flip-v', action='store_true', help='上下反転')
    p.add_argument('--zmq-url', type=str, default='tcp://127.0.0.1:5555', help='ZMQ カメラプロキシのURL（backend=zmq 用）')
    p.add_argument('--zmq-topic', type=str, default='frame', help='ZMQ のトピック名（backend=zmq 用）')
    # 実験のメタ情報
    p.add_argument('--session', type=str, default=None)
    p.add_argument('--participant', type=str, default=None)
    p.add_argument('--task', type=str, default=None)
    p.add_argument('--phase', type=str, default='train', choices=['train','eval'])
    p.add_argument('--calib-seconds', type=int, default=60)
    # パーソナライズの保存/読み込み（学習OFFの場合は未使用）
    p.add_argument('--model-save', type=str, default=None)
    p.add_argument('--model-load', type=str, default=None)
    # 学習のON/OFF（デフォルトOFF）
    p.add_argument('--learning', type=str, default='off', choices=['on','off'], help='パーソナライズ学習の有効/無効')
    # まばたき検出の調整
    p.add_argument('--ear-threshold-ratio', type=float, default=0.90, help='EAR閾値の比率（基準値の何%で閉眼と判定するか、デフォルト0.90）')
    p.add_argument('--ear-baseline-init', type=float, default=0.45, help='EAR基準値の初期値（デフォルト0.45）')
    return p.parse_args()


def main():
    args = parse_args()

    try:
    cam = Camera(index=args.cam, width=args.width, height=args.height, fps=30,
                backend=args.backend, rotate=args.rotate, flip_h=args.flip_h, flip_v=args.flip_v,
                zmq_url=args.zmq_url, zmq_topic=args.zmq_topic).open()
    except Exception as e:
        print(f"Error: Failed to open camera: {e}")
        print("Please check camera connection and permissions.")
        return
    face = FaceProcessor(static_mode=False, refine_iris=True, max_faces=1)

    blink = BlinkDetector()
    # まばたき検出の閾値を調整
    blink.open_baseline = args.ear_baseline_init
    blink.ear_threshold_ratio = args.ear_threshold_ratio
    gaze = GazeEstimator()
    fusion = FusionScorer()
    perso = Personalizer(phase=args.phase, calib_seconds=args.calib_seconds)
    # 評価フェーズではベースラインの適応を無効化（次回以降の学習のみ反映）
    try:
        blink.adapt_enabled = (args.phase == 'train') and (args.learning == 'on')
    except Exception:
        pass
    # 学習ONかつモデル指定がある場合は読み込み
    learning_enabled = (args.learning == 'on')
    if learning_enabled and args.model_load:
        try:
            perso.load(args.model_load)
            perso.apply_to_detectors(blink_detector=blink, gaze_estimator=gaze)
        except Exception as e:
            print('Failed to load model:', e)
    overlay = Overlay()
    # ログファイルの自動命名（ディレクトリのみ指定、または未指定の場合）
    log_path = args.log if args.log else ('logs' if args.auto_log_name else None)
    logger = CSVLogger(log_path, meta={
        'session': args.session,
        'participant': args.participant,
        'task': args.task,
        'phase': args.phase,
        'calib_seconds': args.calib_seconds,
        'model_load': args.model_load,
        'learning': args.learning,
        'backend': args.backend,
        'rotate': args.rotate,
        'flip_h': args.flip_h,
        'flip_v': args.flip_v,
        'ear_threshold_ratio': args.ear_threshold_ratio,
        'ear_baseline_init': args.ear_baseline_init,
    }, auto_name=args.auto_log_name) if log_path else None
    
    if logger:
        print(f"Logging to: {logger.path}")

    last_alert_time = 0.0
    cooldown_sec = 60.0
    alert_enabled = (args.alert_mode == 'on')
    block_id = None
    distractor_on = False

    # マウス/タッチ入力の取得
    last_click = {'x': None, 'y': None, 'ts': 0}
    win_name = 'Focus Alert (Blink+Gaze)'
    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            last_click['x'] = x
            last_click['y'] = y
            last_click['ts'] = time.time()
        elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):
            # ドラッグ中もタッチとして扱う（タッチスクリーン対応）
            last_click['x'] = x
            last_click['y'] = y
            last_click['ts'] = time.time()

    # 表示解像度の決定（PC用とRaspberry Pi用で分岐）
    # 未指定の場合は、Raspberry Pi用（320×480）またはカメラ解像度の小さい方
    if args.display_width is None or args.display_height is None:
        # Raspberry Pi用のデフォルト（3.5インチタッチモニタ）
        # PCではカメラ解像度をそのまま表示
        if args.backend == 'zmq':
            # Raspberry Pi用: 320×480に固定
            display_width = args.display_width if args.display_width else 320
            display_height = args.display_height if args.display_height else 480
        else:
            # PC用: カメラ解像度をそのまま使用（または指定値）
            display_width = args.display_width if args.display_width else args.width
            display_height = args.display_height if args.display_height else args.height
    else:
        display_width = args.display_width
        display_height = args.display_height

    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, display_width, display_height)
    # Raspberry Pi用のみフルスクリーン
    if args.backend == 'zmq':
        cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    frame_failure_count = 0
    max_failures = 30  # 約1秒間（30fps想定）連続で失敗したら警告
    
    while True:
        ok, frame = cam.read()
        if not ok:
            frame_failure_count += 1
            if frame_failure_count >= max_failures:
                print(f"Warning: Camera frame read failed {frame_failure_count} times consecutively.")
                # 完全に停止せず、エラー表示を続ける
            # エラー時も空のフレームで処理を続行（UIでエラー表示）
            if frame is None:
                # ダミーフレームを作成（エラー表示用）
                frame = np.zeros((args.height, args.width, 3), dtype=np.uint8)
                cv2.putText(frame, "Camera Error", (50, args.height//2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            frame_failure_count = 0  # 成功したらリセット
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

        # まずスコアを更新し、アラート判定
        score = fusion.update(feats, perso)
        now = time.time()
        alert = fusion.should_alert(score, now, last_alert_time, cooldown_sec) if alert_enabled else False
        if alert:
            last_alert_time = now

        # 次に、学習ONの場合のみパーソナライズを更新
        if learning_enabled:
            perso.update(feats, status=status, alert=alert)

        fps = 1.0 / max(1e-3, (time.time() - t0))
        
        # カメラ状態を取得
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

        # フレームを表示解像度にリサイズ（アスペクト比を維持しつつフィット）
        h, w = vis.shape[:2]
        target_w, target_h = display_width, display_height
        
        # カメラ解像度と表示解像度が同じ場合はリサイズ不要
        if w == target_w and h == target_h:
            vis_display = vis
            btn_rects_scaled = btn_rects
        else:
            scale = min(target_w / w, target_h / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            vis_resized = cv2.resize(vis, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # 黒背景に中央配置
            vis_display = np.zeros((target_h, target_w, 3), dtype=np.uint8)
            y_offset = (target_h - new_h) // 2
            x_offset = (target_w - new_w) // 2
            vis_display[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = vis_resized
            
            # ボタン矩形をリサイズ後の座標に変換
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
        # タッチ入力 → ボタン矩形のヒットテストでキーを擬似的に発火
        if last_click['x'] is not None:
            x, y = last_click['x'], last_click['y']
            last_click['x'] = None
            # リサイズ後の座標で判定
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
            # 視線の中心をキャリブレーション
            gaze.calibrate_center()
            if logger:
                logger.write_event('calibrate_center', block_id=block_id)
        if key == ord('s'):
            # 新しいブロックを開始
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
    # 終了時、学習ONかつ保存先指定があればパーソナライズを保存
    if learning_enabled and args.model_save:
        try:
            perso.save(args.model_save)
            print('Saved model to', args.model_save)
        except Exception as e:
            print('Failed to save model:', e)


if __name__ == '__main__':
    main()
