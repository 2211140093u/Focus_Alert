import cv2
import numpy as np

class _OpenCVCamera:
    def __init__(self, index=0, width=640, height=480, fps=30, rotate=0, flip_h=False, flip_v=False):
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps
        self.rotate = rotate
        self.flip_h = flip_h
        self.flip_v = flip_v
        self.cap = None

    def open(self):
        # Windows では CAP_DSHOW を使うことがありますが、まずは汎用的な方法を試します（Linux では V4L2 が既定）。
        self.cap = cv2.VideoCapture(self.index)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        # RGB変換を明示的に有効化（モノクロ問題の対策）
        self.cap.set(cv2.CAP_PROP_CONVERT_RGB, 1)
        
        # カメラ品質の最適化設定
        # 自動露出を有効化（明るさの自動調整）
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # 0.75 = 自動露出モード
        # 自動フォーカスを有効化（可能な場合）
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        # ホワイトバランスを自動に
        self.cap.set(cv2.CAP_PROP_AUTO_WB, 1)
        # 明るさを適度に設定（0.0-1.0、デフォルトは0.5）
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
        # コントラストを適度に設定
        self.cap.set(cv2.CAP_PROP_CONTRAST, 0.5)
        # 彩度を適度に設定
        self.cap.set(cv2.CAP_PROP_SATURATION, 0.5)
        # シャープネスを適度に設定
        self.cap.set(cv2.CAP_PROP_SHARPNESS, 0.5)
        
        return self

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            return ok, frame
        # 画像の向きを調整（回転・反転）
        if self.rotate in (90, 180, 270):
            if self.rotate == 90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif self.rotate == 180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            else:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        if self.flip_h:
            frame = cv2.flip(frame, 1)
        if self.flip_v:
            frame = cv2.flip(frame, 0)
        return True, frame

    def release(self):
        if self.cap is not None:
            self.cap.release()


class _PiCamera2Camera:
    def __init__(self, width=640, height=480, fps=30, rotate=0, flip_h=False, flip_v=False):
        # Picamera2 を読み込む。失敗した場合のみシステムの dist-packages を末尾に追加し、
        # venv（仮想環境）側の numpy/opencv を優先したままにします。
        try:
            from picamera2 import Picamera2  # type: ignore
        except Exception:
            import sys
            p = '/usr/lib/python3/dist-packages'
            if p not in sys.path:
                sys.path.append(p)
            from picamera2 import Picamera2  # type: ignore
        self.Picamera2 = Picamera2
        self.width = width
        self.height = height
        self.fps = fps
        self.rotate = rotate
        self.flip_h = flip_h
        self.flip_v = flip_v
        self.cam = None

    def open(self):
        self.cam = self.Picamera2()
        config = self.cam.create_preview_configuration(main={"size": (self.width, self.height), "format": "RGB888"})
        self.cam.configure(config)
        # 向き（回転・反転）の指定
        transform = 0
        # Picamera2 は Transform フラグを使います。利用可能ならそれを使って近い挙動を指定します。
        try:
            from picamera2 import Transform
            transform = 0
            if self.flip_h:
                transform |= Transform.HFLIP
            if self.flip_v:
                transform |= Transform.VFLIP
            if self.rotate in (90, 180, 270):
                # 回転は 90 度単位で Transform で指定
                if self.rotate == 90:
                    transform |= Transform.ROT90
                elif self.rotate == 180:
                    transform |= Transform.ROT180
                else:
                    transform |= Transform.ROT270
            self.cam.configure(self.cam.create_preview_configuration(main={"size": (self.width, self.height), "format": "RGB888"}, transform=transform))
        except Exception:
            pass
        self.cam.start()
        return self

    def read(self):
        # 取得画像は RGB888 なので、OpenCV で扱いやすいよう BGR に変換します。
        import numpy as np
        arr = self.cam.capture_array()
        frame = arr[:, :, ::-1].copy()
        return True, frame

    def release(self):
        try:
            if self.cam:
                self.cam.stop()
        except Exception:
            pass


class _ZmqCamera:
    def __init__(self, url='tcp://127.0.0.1:5555', topic='frame'):
        import zmq  # 遅延インポート（必要になってから読み込む）
        self.zmq = zmq
        self.url = url
        self.topic = topic.encode('utf-8')
        self.ctx = None
        self.sub = None

    def open(self):
        self.ctx = self.zmq.Context.instance()
        self.sub = self.ctx.socket(self.zmq.SUB)
        self.sub.connect(self.url)
        self.sub.setsockopt(self.zmq.SUBSCRIBE, self.topic)
        # ノンブロッキングで受信可否を監視するポーラ
        self.poller = self.zmq.Poller()
        self.poller.register(self.sub, self.zmq.POLLIN)
        return self

    def read(self):
        # 受信形式は [topic, jpg_bytes]
        socks = dict(self.poller.poll(1000))  # タイムアウト 1 秒
        if self.sub not in socks:
            return False, None
        parts = self.sub.recv_multipart()
        if len(parts) < 2:
            return False, None
        jpg = parts[1]
        arr = np.frombuffer(jpg, dtype=np.uint8)
        # cv2.imdecodeはJPEGをBGR形式でデコードする
        # 送信側でRGB→BGRに変換してからエンコードしているため、デコード後は既にBGR形式
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return False, None
        return True, frame

    def release(self):
        try:
            if self.sub is not None:
                self.sub.close(0)
            if self.ctx is not None:
                self.ctx.term()
        except Exception:
            pass


class Camera:
    def __init__(self, index=0, width=640, height=480, fps=30, backend='auto', rotate=0, flip_h=False, flip_v=False,
                 zmq_url='tcp://127.0.0.1:5555', zmq_topic='frame'):
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps
        self.backend = backend
        self.rotate = rotate
        self.flip_h = flip_h
        self.flip_v = flip_v
        self.impl = None
        self.zmq_url = zmq_url
        self.zmq_topic = zmq_topic
        self._last_read_ok = False
        self._consecutive_failures = 0

    def open(self):
        try:
            if self.backend == 'zmq':
                self.impl = _ZmqCamera(url=self.zmq_url, topic=self.zmq_topic).open()
                return self
            if self.backend in ('picamera2', 'auto'):
                try:
                    self.impl = _PiCamera2Camera(width=self.width, height=self.height, fps=self.fps,
                                                 rotate=self.rotate, flip_h=self.flip_h, flip_v=self.flip_v).open()
                    return self
                except Exception as e:
                    if self.backend == 'picamera2':
                        raise
                    print(f"Warning: Picamera2 failed, falling back to OpenCV: {e}")
            # 最後の手段として OpenCV カメラにフォールバック
            self.impl = _OpenCVCamera(index=self.index, width=self.width, height=self.height, fps=self.fps,
                                       rotate=self.rotate, flip_h=self.flip_h, flip_v=self.flip_v).open()
            return self
        except Exception as e:
            print(f"Error opening camera: {e}")
            raise

    def read(self):
        if self.impl is None:
            return False, None
        try:
            ok, frame = self.impl.read()
            self._last_read_ok = ok
            if ok:
                self._consecutive_failures = 0
            else:
                self._consecutive_failures += 1
            return ok, frame
        except Exception as e:
            self._last_read_ok = False
            self._consecutive_failures += 1
            print(f"Error reading camera frame: {e}")
            return False, None

    def get_status(self):
        """カメラの状態を取得"""
        return {
            'connected': self.impl is not None,
            'last_read_ok': self._last_read_ok,
            'consecutive_failures': self._consecutive_failures,
            'backend': self.backend,
        }

    def release(self):
        if self.impl is not None:
            try:
                self.impl.release()
            except Exception as e:
                print(f"Error releasing camera: {e}")
            finally:
                self.impl = None
