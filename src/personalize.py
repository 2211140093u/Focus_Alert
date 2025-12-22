import json
import time
import os

class Personalizer:
    def __init__(self, phase='train', calib_seconds=60,
                 ear_alpha_up=0.03, ear_alpha_down=0.005,
                 gaze_alpha=0.03, stable_frames_req=10,
                 skip_on_closed=True, skip_on_offgaze=True, skip_on_alert=True):
        self.phase = phase  # 'train'（学習）または 'eval'（評価）
        self.calib_seconds = calib_seconds
        self.start_ts = time.time()
        self.calib_started = False
        self.calib_ended = False
        # 簡易なEWMA（指数移動平均）のパラメータ
        self.ear_alpha_up = ear_alpha_up       # EARが増加（より開く）時の追従速度
        self.ear_alpha_down = ear_alpha_down   # EARが減少（眠気方向）時の追従速度（小さめで保守的）
        self.gaze_alpha = gaze_alpha
        self.stable_frames_req = stable_frames_req
        self.skip_on_closed = skip_on_closed
        self.skip_on_offgaze = skip_on_offgaze
        self.skip_on_alert = skip_on_alert
        self.stable_ctr = 0
        self.state = {
            'ear_baseline': None,
            'gaze_bias': 0.0,
        }

    def in_calibration(self):
        if self.phase != 'train':
            return False
        now = time.time()
        if not self.calib_started:
            self.calib_started = True
        if not self.calib_ended and (now - self.start_ts) >= self.calib_seconds:
            self.calib_ended = True
        return not self.calib_ended

    def _is_stable(self, feats, status, alert):
        has_face = bool(status.get('has_face', True))
        b = feats.get('blink', {})
        g = feats.get('gaze', {})
        cond = has_face
        if self.skip_on_closed:
            cond = cond and (not b.get('is_closed', False))
        if self.skip_on_offgaze:
            cond = cond and (not g.get('gaze_off', False))
        if self.skip_on_alert:
            cond = cond and (not alert)
        return cond

    def update(self, feats, status=None, alert=False):
        # 開眼基準（EARベースライン）や視線バイアスを、条件が整った時のみ更新
        b = feats.get('blink', {})
        g = feats.get('gaze', {})
        ear = b.get('ear')
        status = status or {}

        # 学習は train フェーズのみ実施
        if self.phase != 'train':
            return self.state

        # 安定判定（連続で条件を満たしたフレーム数を数える）
        if self._is_stable(feats, status, alert):
            self.stable_ctr += 1
        else:
            self.stable_ctr = 0

        if self.stable_ctr >= self.stable_frames_req:
            # EARベースラインの更新（上昇/下降で異なる係数を使用）
            if ear is not None:
                if self.state['ear_baseline'] is None:
                    self.state['ear_baseline'] = float(ear)
                else:
                    base = float(self.state['ear_baseline'])
                    x = float(ear)
                    if x >= base:
                        a = self.ear_alpha_up
                    else:
                        a = self.ear_alpha_down
                    self.state['ear_baseline'] = (1 - a) * base + a * x

            # 視線バイアスを中心側へ寄せる（現在のズレを相殺するイメージ）
            if not g.get('gaze_off', False):
                bias = -float(g.get('gaze_horiz', 0.0))  # to center it
                gb = float(self.state.get('gaze_bias', 0.0))
                a = self.gaze_alpha
                self.state['gaze_bias'] = (1 - a) * gb + a * bias
        return self.state

    def save(self, path):
        data = {
            'phase': self.phase,
            'state': self.state,
            'calib_seconds': self.calib_seconds,
            'ear_alpha_up': self.ear_alpha_up,
            'ear_alpha_down': self.ear_alpha_down,
            'gaze_alpha': self.gaze_alpha,
            'stable_frames_req': self.stable_frames_req,
            'skip_on_closed': self.skip_on_closed,
            'skip_on_offgaze': self.skip_on_offgaze,
            'skip_on_alert': self.skip_on_alert,
        }
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)

    def load(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.phase = data.get('phase', self.phase)
        self.state.update(data.get('state', {}))
        self.calib_seconds = data.get('calib_seconds', self.calib_seconds)
        self.ear_alpha_up = data.get('ear_alpha_up', self.ear_alpha_up)
        self.ear_alpha_down = data.get('ear_alpha_down', self.ear_alpha_down)
        self.gaze_alpha = data.get('gaze_alpha', self.gaze_alpha)
        self.stable_frames_req = data.get('stable_frames_req', self.stable_frames_req)
        self.skip_on_closed = data.get('skip_on_closed', self.skip_on_closed)
        self.skip_on_offgaze = data.get('skip_on_offgaze', self.skip_on_offgaze)
        self.skip_on_alert = data.get('skip_on_alert', self.skip_on_alert)

    def apply_to_detectors(self, blink_detector=None, gaze_estimator=None):
        # 必要に応じて、保存済み状態から検出器の内部ベースライン/バイアスへ反映
        if blink_detector is not None and self.state.get('ear_baseline') is not None:
            try:
                blink_detector.open_baseline = float(self.state['ear_baseline'])
            except Exception:
                pass
        if gaze_estimator is not None:
            try:
                gaze_estimator.bias = float(self.state.get('gaze_bias', 0.0))
            except Exception:
                pass
