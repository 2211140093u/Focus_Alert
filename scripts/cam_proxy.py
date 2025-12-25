#!/usr/bin/env python3
import argparse
import time
import sys
import io
import cv2
import numpy as np
import zmq

# Picamera2 はシステムの Python（3.13）に apt（python3-picamera2）でインストールされている想定
try:
    from picamera2 import Picamera2
    from picamera2.encoders import JpegEncoder
except Exception as e:
# Picamera2 を読み込めない場合は、python3-picamera2 を導入する
    print("Picamera2 の読み込みに失敗しました。python3-picamera2 をインストールしてください。", file=sys.stderr)
    raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', default='tcp://127.0.0.1:5555')
    ap.add_argument('--topic', default='frame')
    ap.add_argument('--width', type=int, default=640)
    ap.add_argument('--height', type=int, default=480)
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--quality', type=int, default=85)
    args = ap.parse_args()

    ctx = zmq.Context.instance()
    pub = ctx.socket(zmq.PUB)
    pub.bind(args.url)
    topic = args.topic.encode('utf-8')

    picam = Picamera2()
    # プレビュー用の設定を作成（サイズと色形式を指定）
    config = picam.create_preview_configuration(main={"size": (args.width, args.height), "format": "RGB888"})
    picam.configure(config)
    picam.start()

    t_prev = time.time()
    try:
        while True:
            arr = picam.capture_array()
            # Picamera2はRGB888形式で取得される
            # cv2.imencodeはBGR形式を想定しているため、RGB→BGRに変換してからエンコード
            # cv2.imdecodeもBGR形式でデコードするため、これで正しい色になる
            frame_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            # JPEG にエンコード（品質は --quality で指定）
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), args.quality]
            ok, enc = cv2.imencode('.jpg', frame_bgr, encode_param)
            if not ok:
                continue
            pub.send_multipart([topic, enc.tobytes()])
            # おおよそ指定 FPS になるように処理時間を計測（ここでは記録のみ）
            dt = time.time() - t_prev
            t_prev = time.time()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            picam.stop()
        except Exception:
            pass
        pub.close(0)
        ctx.term()


if __name__ == '__main__':
    main()
