import csv, time, os
from datetime import datetime

class CSVLogger:
    def __init__(self, path, meta=None, auto_name=True):
        self.path = path
        self.meta = meta or {}
        # 自動命名: パスが指定されていない、またはディレクトリのみ指定されている場合
        if auto_name and (path is None or os.path.isdir(path) or (os.path.dirname(path) and not os.path.basename(path))):
            if path is None or os.path.isdir(path):
                log_dir = path if path and os.path.isdir(path) else 'logs'
            else:
                log_dir = os.path.dirname(path)
            os.makedirs(log_dir, exist_ok=True)
            # 日時ベースのファイル名を生成
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.path = os.path.join(log_dir, f'session_{timestamp}.csv')
        else:
            os.makedirs(os.path.dirname(self.path), exist_ok=True) if os.path.dirname(self.path) else None
        self._init()

    def _init(self):
        with open(self.path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            # 共通ヘッダ
            w.writerow([
                'ts','row_type','session','participant','task','phase','block_id',
                'ear','ear_base','ear_thr','blink_count','is_closed','long_close',
                'gaze','gaze_thr','gaze_bias','gaze_y','gaze_y_thr','gaze_bias_y','gaze_offlvl',
                'risk','alert','event','info'
            ])
            # 必要に応じてメタ行を書き込む
            # 日時情報を追加
            meta_with_time = self.meta.copy()
            meta_with_time['start_time'] = datetime.now().isoformat()
            meta_with_time['start_timestamp'] = time.time()
            w.writerow([
                time.time(),'meta',
                self.meta.get('session'), self.meta.get('participant'), self.meta.get('task'), self.meta.get('phase'), None,
                None,None,None,None,None,None,
                None,None,None,None,None,None,None,
                None,None,'meta', str(meta_with_time)
            ])

    def write_frame(self, feats, score, alert, block_id=None):
        with open(self.path, 'a', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            b = feats.get('blink', {})
            g = feats.get('gaze', {})
            w.writerow([
                time.time(),'frame',
                self.meta.get('session'), self.meta.get('participant'), self.meta.get('task'), self.meta.get('phase'), block_id,
                b.get('ear'), b.get('ear_baseline'), b.get('ear_thresh'), b.get('blink_count'), b.get('is_closed'), b.get('long_close'),
                g.get('gaze_horiz'), g.get('gaze_thresh'), g.get('gaze_bias'),
                g.get('gaze_y'), g.get('gaze_y_thresh'), g.get('gaze_bias_y'), g.get('gaze_off_level'),
                score, int(alert), None, None
            ])

    def write_event(self, event, info=None, block_id=None):
        with open(self.path, 'a', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow([
                time.time(),'event',
                self.meta.get('session'), self.meta.get('participant'), self.meta.get('task'), self.meta.get('phase'), block_id,
                None,None,None,None,None,None,
                None,None,None,None,
                None,None,event, info
            ])
    
    def write_note(self, note_text):
        """メモを記録"""
        self.write_event('note', info=note_text)
