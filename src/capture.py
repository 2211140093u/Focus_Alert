import cv2

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
        from picamera2 import Picamera2
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


class Camera:
    def __init__(self, index=0, width=640, height=480, fps=30, backend='auto', rotate=0, flip_h=False, flip_v=False):
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps
        self.backend = backend
        self.rotate = rotate
        self.flip_h = flip_h
        self.flip_v = flip_v
        self.impl = None

    def open(self):
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
