import numpy as np

# FaceMesh（MediaPipe）の目のランドマーク番号
# EAR（まばたき指標）計算に使う左右の主要点
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
        self.long_close_threshold_frames = 12  # 30fps時におよそ400ms
        # 開眼時 EAR の基準値（EWMAでゆっくり更新）
        self.open_baseline = 0.45
        self.base_alpha = 0.05
        # セッション中の基準値の適応を無効化できるフラグ（評価フェーズなど）
        self.adapt_enabled = True

    @staticmethod
    def _ear(pts):
        # pts: [p1,p2,p3,p4,p5,p6] = [外側, 上まぶた1, 下まぶた1, 内側, 下まぶた2, 上まぶた2]
        p1,p2,p3,p4,p5,p6 = pts
        # numpy を用いて距離を計算
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
        # 平滑化（指数移動平均）
        if self.ear_smooth == 0.0:
            self.ear_smooth = ear
        else:
            self.ear_smooth = self.alpha * ear + (1 - self.alpha) * self.ear_smooth

        # 閉眼していない時に開眼基準値を更新（保守的）
        # 瞬目中に基準値が下がりすぎないよう、現在値と平滑値の大きい方を採用
        if self.adapt_enabled:
            candidate = max(ear, self.ear_smooth)
            if not self.closed:
                self.open_baseline = (1 - self.base_alpha) * self.open_baseline + self.base_alpha * candidate

        # 相対しきい値: 基準値の約90%未満で「閉眼」とみなす
        thresh = self.open_baseline * 0.90

        if ear < thresh:
            self.close_frames += 1
            self.long_close_frames += 1
            now_closed = True
        else:
            now_closed = False
            # 閉→開の遷移時に、一定範囲の継続フレーム数なら「瞬目」とカウント
            if self.closed and 1 <= self.close_frames <= 20:
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
        # 顔を見失った時: 平滑値を基準値へ緩やかに戻し、カウントはしない
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
