import numpy as np

# Eye corners for normalization
LEFT_INNER = 133
LEFT_OUTER = 33
RIGHT_INNER = 362
RIGHT_OUTER = 263

# Iris landmarks (best-effort; FaceMesh refine_landmarks=True adds iris points)
# Common mapping used in community examples:
RIGHT_IRIS = [468, 469, 470, 471]
LEFT_IRIS = [473, 474, 475, 476]

class GazeEstimator:
    def __init__(self):
        self.center_smooth = np.array([0.0, 0.0])  # [x, y]
        self.alpha = 0.35  # a bit more responsive
        self.off_since = None
        self.off_seconds = 0.0
        self.last_time = None
        self.bias = 0.0  # x-axis center calibration offset
        self.bias_y = 0.0  # y-axis center calibration offset
        self.off_level = 0.0  # EMA of off boolean -> [0,1]
        self.off_alpha = 0.1

    def _centroid(self, lms, idxs):
        pts = np.array([[lms[i].x, lms[i].y] for i in idxs])
        return pts.mean(axis=0)

    def _eye_line(self, lms, inner_idx, outer_idx):
        a = np.array([lms[inner_idx].x, lms[inner_idx].y])
        b = np.array([lms[outer_idx].x, lms[outer_idx].y])
        return a, b

    def calibrate_center(self):
        # set current smoothed horiz as bias so centered gaze -> 0
        self.bias = float(self.center_smooth[0])
        self.bias_y = float(self.center_smooth[1])

    def update(self, landmarks):
        # left eye normalized horizontal-offset; positive => looking outward (toward outer corner)
        li, lo = self._eye_line(landmarks, LEFT_INNER, LEFT_OUTER)
        ri, ro = self._eye_line(landmarks, RIGHT_INNER, RIGHT_OUTER)

        # Use iris centroid if available, else eye center fallback
        has_iris = len(landmarks) >= 477
        if has_iris:
            lc = self._centroid(landmarks, LEFT_IRIS)
            rc = self._centroid(landmarks, RIGHT_IRIS)
        else:
            lc = (li + lo) * 0.5
            rc = (ri + ro) * 0.5

        # Normalize per eye by eye width
        def norm_offset(c, inner, outer):
            width = np.linalg.norm(inner - outer) + 1e-6
            # signed projection along the eye line
            dirv = (outer - inner) / width
            vec = (c - 0.5 * (inner + outer))
            # horizontal along eye line
            relx = np.dot(vec, dirv) / (width * 0.5)
            # vertical: project to perpendicular; normalize by width*0.5 as proxy scale
            perp = np.array([-dirv[1], dirv[0]])
            rely = np.dot(vec, perp) / (width * 0.5)
            return float(relx), float(rely)

        lrx, lry = norm_offset(lc, li, lo)
        rrx, rry = norm_offset(rc, ri, ro)
        horiz = 0.5 * (lrx + rrx)
        vert = 0.5 * (lry + rry)

        # Smooth
        self.center_smooth[0] = self.alpha * horiz + (1 - self.alpha) * self.center_smooth[0]
        self.center_smooth[1] = self.alpha * vert + (1 - self.alpha) * self.center_smooth[1]

        # Derive a simple off-screen metric: |horiz| beyond threshold
        thresh = 0.35  # x threshold
        thresh_y = 0.25  # y threshold (often smaller than x)
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
        # decay to center
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
