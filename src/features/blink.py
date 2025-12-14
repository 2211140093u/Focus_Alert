import numpy as np

# Eye landmark indices for FaceMesh (mediapipe)
# Left eye and right eye key points for EAR calculation
LEFT = [33, 160, 158, 133, 153, 144]
RIGHT = [263, 387, 385, 362, 380, 373]

class BlinkDetector:
    def __init__(self):
        self.ear_smooth = 0.0
        self.alpha = 0.2
        self.closed = False
        self.close_frames = 0
        self.blinks = 0
        self.long_close_frames = 0
        self.long_close_threshold_frames = 12  # ~400ms at 30fps
        # EWMA baseline of "open eye" EAR
        self.open_baseline = 0.45
        self.base_alpha = 0.05
        # allow disabling baseline adaptation within a session (eval phase)
        self.adapt_enabled = True

    @staticmethod
    def _ear(pts):
        # pts: [p1,p2,p3,p4,p5,p6] = [outer, upper1, lower1, inner, lower2, upper2]
        p1,p2,p3,p4,p5,p6 = pts
        # We'll compute distances directly using numpy
        def d(a,b):
            return np.hypot(a.x - b.x, a.y - b.y)
        vert = d(p2,p5) + d(p3,p6)
        horiz = d(p1,p4)
        if horiz <= 1e-6:
            return 0.0
        return vert / (2.0 * horiz)

    def _eye_ear(self, lms, idxs):
        pts = [lms[i] for i in idxs]
        return self._ear(pts)

    def update(self, landmarks):
        le = self._eye_ear(landmarks, LEFT)
        re = self._eye_ear(landmarks, RIGHT)
        ear = (le + re) * 0.5
        # smooth
        if self.ear_smooth == 0.0:
            self.ear_smooth = ear
        else:
            self.ear_smooth = self.alpha * ear + (1 - self.alpha) * self.ear_smooth

        # Update open-eye baseline when not closed (conservative)
        # Use the max of smoothed and current to avoid drifting too low during blinks
        if self.adapt_enabled:
            candidate = max(ear, self.ear_smooth)
            if not self.closed:
                self.open_baseline = (1 - self.base_alpha) * self.open_baseline + self.base_alpha * candidate

        # Relative threshold: closed if below ~80% of baseline
        thresh = self.open_baseline * 0.80

        if ear < thresh:
            self.close_frames += 1
            self.long_close_frames += 1
            now_closed = True
        else:
            now_closed = False
            # blink counted on closed->open transition
            if self.closed and 2 <= self.close_frames <= 20:
                self.blinks += 1
            self.close_frames = 0
            self.long_close_frames = 0

        self.closed = now_closed

        return {
            'ear': float(ear),
            'ear_smooth': float(self.ear_smooth),
            'ear_baseline': float(self.open_baseline),
            'ear_thresh': float(thresh),
            'blink_count': int(self.blinks),
            'is_closed': bool(self.closed),
            'long_close': bool(self.long_close_frames >= self.long_close_threshold_frames)
        }

    def miss(self):
        # No face: decay towards baseline, don't count
        self.ear_smooth = self.alpha * self.open_baseline + (1 - self.alpha) * self.ear_smooth
        self.close_frames = 0
        self.long_close_frames = 0
        self.closed = False
        return {
            'ear': float(self.ear_smooth),
            'ear_smooth': float(self.ear_smooth),
            'ear_baseline': float(self.open_baseline),
            'ear_thresh': float(self.open_baseline * 0.80),
            'blink_count': int(self.blinks),
            'is_closed': False,
            'long_close': False,
        }
