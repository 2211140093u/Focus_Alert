import time

class FusionScorer:
    def __init__(self):
        self.score = 0.0
        self.alpha = 0.3
        self.hi = 0.55  # アラートのしきい値
        self.lo = 0.35  # 今は未使用（将来の解除ヒステリシス用）

    def update(self, feats, perso):
        # ヒューリスティック: 長時間の閉眼と継続的な視線逸脱を強めに評価
        blink = feats['blink']
        gaze = feats['gaze']
        long_close = 1.0 if blink.get('long_close', False) else 0.0
        closed_now = 1.0 if blink.get('is_closed', False) else 0.0
        off_lvl = float(gaze.get('gaze_off_level', 1.0 if gaze.get('gaze_off', False) else 0.0))

        raw = 0.7 * long_close + 0.2 * off_lvl + 0.1 * closed_now
        self.score = self.alpha * raw + (1 - self.alpha) * self.score
        return self.score

    def get_concentration_score(self):
        """リスクスコアから集中度スコアを計算（1.0 = 完全集中、0.0 = 完全散漫）"""
        return 1.0 - self.score
    
    def should_alert(self, score, now_ts, last_alert_ts, cooldown_sec=60.0):
        # 集中度ベースのアラート判定
        # リスクスコアを集中度スコアに変換（1.0 - score）
        concentration = 1.0 - score
        # 集中度閾値（リスク閾値を集中度に変換: 1.0 - risk_threshold）
        concentration_threshold = 1.0 - self.hi
        # クールダウン付きのヒステリシス
        in_cooldown = (now_ts - last_alert_ts) < cooldown_sec
        if concentration <= concentration_threshold and not in_cooldown:
            return True
        return False
