import mediapipe as mp

class FaceProcessor:
    def __init__(self, static_mode=False, refine_iris=True, max_faces=1):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=static_mode,
            max_num_faces=max_faces,
            refine_landmarks=refine_iris,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def process(self, rgb_image):
        res = self.face_mesh.process(rgb_image)
        if not res.multi_face_landmarks:
            return {'landmarks': None, 'has_face': False}
        # 最初の1人分のランドマークのみを使用
        lms = res.multi_face_landmarks[0].landmark
        return {'landmarks': lms, 'has_face': True}
