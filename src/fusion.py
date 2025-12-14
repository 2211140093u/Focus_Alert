import time

class FusionScorer:
    def __init__(self):
        self.score = 0.0
        self.alpha = 0.3
        self.hi = 0.55  # alert threshold
        self.lo = 0.35  # not used yet; reserved for de-latch

    def update(self, feats, perso):
        # Heuristic: emphasize long eye-closure and persistent off-gaze
        blink = feats['blink']
        gaze = feats['gaze']
        long_close = 1.0 if blink.get('long_close', False) else 0.0
        closed_now = 1.0 if blink.get('is_closed', False) else 0.0
        off_lvl = float(gaze.get('gaze_off_level', 1.0 if gaze.get('gaze_off', False) else 0.0))

        raw = 0.7 * long_close + 0.2 * off_lvl + 0.1 * closed_now
        self.score = self.alpha * raw + (1 - self.alpha) * self.score
        return self.score

    def should_alert(self, score, now_ts, last_alert_ts, cooldown_sec=60.0):
        # Hysteresis with cooldown
        in_cooldown = (now_ts - last_alert_ts) < cooldown_sec
        if score >= self.hi and not in_cooldown:
            return True
        return False
