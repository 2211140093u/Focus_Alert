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
        # CAP_DSHOW for Windows; on Linux V4L2 default works. Try generic first.
        self.cap = cv2.VideoCapture(self.index)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        return self

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            return ok, frame
        # apply orientation
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
        # Import Picamera2, appending system dist-packages at the END only if needed,
        # so that venv's numpy/opencv remain preferred.
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
        # orientation
        transform = 0
        # Picamera2 uses Transform flags; approximate via request controls if available
        try:
            from picamera2 import Transform
            transform = 0
            if self.flip_h:
                transform |= Transform.HFLIP
            if self.flip_v:
                transform |= Transform.VFLIP
            if self.rotate in (90, 180, 270):
                # Rotation handled via transform as multiples of 90
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
        # returns RGB888; convert to BGR for OpenCV
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
        import zmq  # lazy import
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
        # non-blocking ready poller
        self.poller = self.zmq.Poller()
        self.poller.register(self.sub, self.zmq.POLLIN)
        return self

    def read(self):
        # receive [topic, jpg_bytes]
        socks = dict(self.poller.poll(1000))  # 1s timeout
        if self.sub not in socks:
            return False, None
        parts = self.sub.recv_multipart()
        if len(parts) < 2:
            return False, None
        jpg = parts[1]
        arr = np.frombuffer(jpg, dtype=np.uint8)
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

    def open(self):
        if self.backend == 'zmq':
            self.impl = _ZmqCamera(url=self.zmq_url, topic=self.zmq_topic).open()
            return self
        if self.backend in ('picamera2', 'auto'):
            try:
                self.impl = _PiCamera2Camera(width=self.width, height=self.height, fps=self.fps,
                                             rotate=self.rotate, flip_h=self.flip_h, flip_v=self.flip_v).open()
                return self
            except Exception:
                if self.backend == 'picamera2':
                    raise
        # fallback to OpenCV
        self.impl = _OpenCVCamera(index=self.index, width=self.width, height=self.height, fps=self.fps,
                                   rotate=self.rotate, flip_h=self.flip_h, flip_v=self.flip_v).open()
        return self

    def read(self):
        return self.impl.read()

    def release(self):
        if self.impl is not None:
            self.impl.release()
