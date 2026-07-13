import cv2
from ultralytics import YOLO
import math
model = YOLO('yolov8s.pt') 

webcam = cv2.VideoCapture(0)

if not webcam.isOpened():
    print("Error: Could not access the webcam.")
    exit()

while True:
    success, img = webcam.read()
    if not success:
        break
        
    img = cv2.flip(img, 1)
    results = model(img, stream=True, conf=0.15)
    threat_detected = False 
    
    for r in results:
        boxes = r.boxes
        for box in boxes:
            class_name = model.names[int(box.cls[0])]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            box_color = (0, 255, 0)
            
            if class_name == 'knife':
                threat_detected = True
                box_color = (0, 0, 255)
            
            cv2.rectangle(img, (x1, y1), (x2, y2), box_color, 2)
            confidence = math.ceil((box.conf[0] * 100)) / 100
            label = f"{class_name.upper()} {confidence}"
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)

    if threat_detected:
        cv2.rectangle(img, (0, 0), (img.shape[1], 50), (0, 0, 255), -1) 
        cv2.putText(img, "WARNING: THREAT DETECTED", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)
        cv2.rectangle(img, (0, 0), (img.shape[1], img.shape[0]), (0, 0, 255), 10)

    cv2.imshow("Surveillance System", img)
    
    if cv2.waitKey(1) == 27:
        break

webcam.release()
cv2.destroyAllWindows()
