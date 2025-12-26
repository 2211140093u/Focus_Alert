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
    ap.add_argument('--quality', type=int, default=85)
    args = ap.parse_args()

    ctx = zmq.Context.instance()
    pub = ctx.socket(zmq.PUB)
    pub.bind(args.url)
    topic = args.topic.encode('utf-8')

    picam = Picamera2()
    
    # 【変更点1】 formatを "BGR888" に指定します
    # これにより、カメラから直接 OpenCV が好む BGR 形式でデータが来ます
    config = picam.create_preview_configuration(
        main={"size": (args.width, args.height), "format": "BGR888"}
    )
    picam.configure(config)
    picam.start()

    t_prev = time.time()
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), args.quality]

    try:
        while True:
            # 取得される arr は既に BGR 形式です
            arr = picam.capture_array()

            # 【変更点2】 cv2.cvtColor は不要なので削除しました
            # そのままエンコードします
            ok, enc = cv2.imencode('.jpg', arr, encode_param)
            
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