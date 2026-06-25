import cv2
import winsound
from ultralytics import YOLO
print(YOLO("best.pt").names)

general_model = YOLO("yolov8s.pt")
weapon_model = YOLO("best.pt")

def process_frame(img):

    img = cv2.flip(img, 1)
    
    img = general_model(img, classes=[0], conf=0.5, verbose=False)[0].plot()
    
    weapon_results = weapon_model(img, conf=0.5, verbose=False)[0]
    img = weapon_results.plot()
    
    alert_triggered = False
    alert_message = ""

    threat_classes=["guns", "knife", "Violence"]
    
    for box in weapon_results.boxes:
        class_id = int(box.cls[0])
        class_name = weapon_model.names[class_id]
        if class_name.lower() in threat_classes:
            alert_triggered = True
            alert_message = "ALERT: " + class_name + " detected!"
            break
        
    return img, alert_triggered, alert_message

webcam = cv2.VideoCapture(0)

while True:
    ret, img = webcam.read()
    if not ret:
        break

    img, alert_triggered, alert_message = process_frame(img)

    if alert_triggered:
        cv2.putText(img, alert_message,(20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        winsound.Beep(1000, 200)

    cv2.imshow("Surveillance System", img)
    if cv2.waitKey(1) == 27:   # ESC
        break

webcam.release()
cv2.destroyAllWindows()