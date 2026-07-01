"""
check.py — finds exactly where the program hangs.
Run:  python check.py
Watch which line prints LAST — that's where it's stuck.
"""
print("1) importing torch ...", flush=True)
import torch
print("   torch ok | CUDA available:", torch.cuda.is_available(), flush=True)

print("2) loading violence model ...", flush=True)
from violence_detector import ViolenceDetector
vdet = ViolenceDetector("violence_mobilenet_lstm.pt")
print("   violence model loaded ok", flush=True)

print("3) opening webcam (using DSHOW backend) ...", flush=True)
import cv2
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)   # CAP_DSHOW = far more reliable on Windows
ok, frame = cap.read()
cap.release()
if ok:
    print("   webcam ok | frame shape:", frame.shape, flush=True)
    print("\n>>> ALL THREE WORK — the slowness was just first-run warmup.")
else:
    print("   webcam FAILED to give a frame", flush=True)
    print("\n>>> Problem is the CAMERA, not your code. (Close Zoom/Teams/Camera app, then retry.)")