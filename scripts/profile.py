import time
import psutil
import cv2

if __name__ == '__main__':
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    last = time.time()
    f = 0
    while True:
        ok, _ = cap.read()
        if not ok:
            break
        f += 1
        now = time.time()
        if now - last >= 1.0:
            cpu = psutil.cpu_percent(interval=None)
            print(f"FPS ~ {f}, CPU {cpu}%")
            f = 0
            last = now
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
