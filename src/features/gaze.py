import numpy as np

# 正規化のために用いる目尻・目頭のランドマーク
LEFT_INNER = 133
LEFT_OUTER = 33
RIGHT_INNER = 362
RIGHT_OUTER = 263

# 虹彩のランドマーク（FaceMesh で refine_landmarks=True のときに追加される点）
# コミュニティでよく使われる対応関係:
RIGHT_IRIS = [468, 469, 470, 471]
LEFT_IRIS = [473, 474, 475, 476]

class GazeEstimator:
    def __init__(self):
        self.center_smooth = np.array([0.0, 0.0])  # [x, y]
        self.alpha = 0.35  # やや追従性を高く設定
        self.off_since = None
        self.off_seconds = 0.0
        self.last_time = None
        self.bias = 0.0  # 水平方向の中心キャリブ補正量
        self.bias_y = 0.0  # 垂直方向の中心キャリブ補正量
        self.off_level = 0.0  # 逸脱フラグの指数移動平均（0〜1）
        self.off_alpha = 0.1

    def _centroid(self, lms, idxs):
        pts = np.array([[lms[i].x, lms[i].y] for i in idxs])
        return pts.mean(axis=0)

    def _eye_line(self, lms, inner_idx, outer_idx):
        a = np.array([lms[inner_idx].x, lms[inner_idx].y])
        b = np.array([lms[outer_idx].x, lms[outer_idx].y])
        return a, b

    def calibrate_center(self):
        # 現在の平滑化済み位置を中心バイアスとして保存し、以後は中心が 0 になるよう補正
        self.bias = float(self.center_smooth[0])
        self.bias_y = float(self.center_smooth[1])

    def update(self, landmarks):
        # 左右の目について、目頭→目尻の線分を基準とした相対オフセットを計算
        li, lo = self._eye_line(landmarks, LEFT_INNER, LEFT_OUTER)
        ri, ro = self._eye_line(landmarks, RIGHT_INNER, RIGHT_OUTER)

        # 虹彩が取得できる場合はその中心、なければ目の中心を代用
        has_iris = len(landmarks) >= 477
        if has_iris:
            lc = self._centroid(landmarks, LEFT_IRIS)
            rc = self._centroid(landmarks, RIGHT_IRIS)
        else:
            lc = (li + lo) * 0.5
            rc = (ri + ro) * 0.5

        # 目幅で正規化（左右それぞれ）
        def norm_offset(c, inner, outer):
            width = np.linalg.norm(inner - outer) + 1e-6
            # 目頭→目尻方向への符号付き射影
            dirv = (outer - inner) / width
            vec = (c - 0.5 * (inner + outer))
            # 水平（目のラインに沿った方向）
            relx = np.dot(vec, dirv) / (width * 0.5)
            # 垂直（目のラインに直交する方向）。幅*0.5で正規化して尺度を揃える
            perp = np.array([-dirv[1], dirv[0]])
            rely = np.dot(vec, perp) / (width * 0.5)
            return float(relx), float(rely)

        lrx, lry = norm_offset(lc, li, lo)
        rrx, rry = norm_offset(rc, ri, ro)
        horiz = 0.5 * (lrx + rrx)
        vert = 0.5 * (lry + rry)

        # 時系列の平滑化（指数移動平均）
        self.center_smooth[0] = self.alpha * horiz + (1 - self.alpha) * self.center_smooth[0]
        self.center_smooth[1] = self.alpha * vert + (1 - self.alpha) * self.center_smooth[1]

        # 簡易な逸脱判定: 閾値を超える水準で off とする
        thresh = 0.35  # 水平方向の閾値
        thresh_y = 0.25  # 垂直方向の閾値（水平より小さめ）
        adj = self.center_smooth[0] - self.bias
        adj_y = self.center_smooth[1] - self.bias_y
        off = (abs(adj) > thresh) or (abs(adj_y) > thresh_y)
        self.off_level = (1 - self.off_alpha) * self.off_level + self.off_alpha * (1.0 if off else 0.0)

        return {
            'gaze_horiz': float(adj),
            'gaze_y': float(adj_y),
            'gaze_off': bool(off),
            'gaze_thresh': float(thresh),
            'gaze_y_thresh': float(thresh_y),
            'has_iris': bool(has_iris),
            'gaze_off_level': float(self.off_level),
            'gaze_bias': float(self.bias),
            'gaze_bias_y': float(self.bias_y),
        }

    def miss(self):
        # 徐々に中心へ戻す（欠測時の安定動作）
        self.center_smooth[0] *= (1 - self.alpha)
        self.center_smooth[1] *= (1 - self.alpha)
        self.off_level *= (1 - self.off_alpha)
        return {
            'gaze_horiz': float(self.center_smooth[0] - self.bias),
            'gaze_y': float(self.center_smooth[1] - self.bias_y),
            'gaze_off': False,
            'gaze_thresh': 0.35,
            'gaze_y_thresh': 0.25,
            'has_iris': False,
            'gaze_off_level': float(self.off_level),
            'gaze_bias': float(self.bias),
            'gaze_bias_y': float(self.bias_y),
        }
