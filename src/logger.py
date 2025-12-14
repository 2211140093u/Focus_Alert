import csv, time, os

class CSVLogger:
    def __init__(self, path, meta=None):
        self.path = path
        self.meta = meta or {}
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        self._init()

    def _init(self):
        with open(self.path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            # Common header
            w.writerow([
                'ts','row_type','session','participant','task','phase','block_id',
                'ear','ear_base','ear_thr','blink_count','is_closed','long_close',
                'gaze','gaze_thr','gaze_bias','gaze_y','gaze_y_thr','gaze_bias_y','gaze_offlvl',
                'risk','alert','event','info'
            ])
            # Optionally write a meta row
            w.writerow([
                time.time(),'meta',
                self.meta.get('session'), self.meta.get('participant'), self.meta.get('task'), self.meta.get('phase'), None,
                None,None,None,None,None,None,
                None,None,None,None,None,None,None,
                None,None,'meta', str(self.meta)
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
