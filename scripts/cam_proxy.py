#!/usr/bin/env python3
import argparse
import time
import sys
import cv2
import zmq
import numpy as np

try:
    from picamera2 import Picamera2
except Exception as e:
    print("Picamera2 の読み込みに失敗しました。", file=sys.stderr)
    raise

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', default='tcp://127.0.0.1:5555')
    ap.add_argument('--topic', default='frame')
    ap.add_argument('--width', type=int, default=640)
    ap.add_argument('--height', type=int, default=480)
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--quality', type=int, default=85)
    ap.add_argument('--rotate', type=int, default=180, choices=[0, 90, 180, 270], help='Camera rotation in degrees')
    args = ap.parse_args()

    ctx = zmq.Context.instance()
    pub = ctx.socket(zmq.PUB)
    pub.bind(args.url)
    topic = args.topic.encode('utf-8')

    picam = Picamera2()
    
    # ストリームの設定（size, format のみ。ここに fps は入れない）
    # あえて RGB888 で取得（こちらの方が内部的に安定することがある）
    # カメラの回転設定を追加
    try:
        from picamera2 import Transform
        transform = 0
        if args.rotate == 90:
            transform = Transform.ROT90
        elif args.rotate == 180:
            transform = Transform.ROT180
        elif args.rotate == 270:
            transform = Transform.ROT270
        config = picam.create_preview_configuration(
            main={"size": (args.width, args.height), "format": "RGB888"},
            transform=transform
        )
    except Exception:
        # Transformが使えない場合は通常の設定
        config = picam.create_preview_configuration(
            main={"size": (args.width, args.height), "format": "RGB888"}
        )
    picam.configure(config)

    # カメラ全体の設定（ここで fps を指定する）
    picam.set_controls({"FrameRate": args.fps})

    picam.start()

    t_prev = time.time()
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), args.quality]

    try:
        while True:
            # NumPy配列として取得（この時点では RGB 順）
            arr = picam.capture_array()

            # 【重要】RGB から BGR へ変換
            # OpenCVのimencodeは「BGR」の並びを想定してJPEGを作るため、ここでの変換が不可欠です
            frame_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            
            # エンコードして送信（BGR形式でエンコード）
            ok, enc = cv2.imencode('.jpg', frame_bgr, encode_param)
            
            if not ok:
                continue
                
            pub.send_multipart([topic, enc.tobytes()])
            
            # FPS計算など（省略）
            t_prev = time.time()

    except KeyboardInterrupt:
        pass
    finally:
        picam.stop()
        pub.close(0)
        ctx.term()

if __name__ == '__main__':
    main()