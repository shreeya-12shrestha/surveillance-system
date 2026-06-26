import cv2
import winsound
from datetime import datetime
from ultralytics import YOLO
print(YOLO("best.pt").names)
from database import init_db, log_alert

init_db() #makes new register

general_model = YOLO("yolov8s.pt")
weapon_model = YOLO("best.pt")

def process_frame(img):

    #img = cv2.flip(img, 1)
    
    img = general_model(img, classes=[0], conf=0.5, verbose=False)[0].plot()
    
    weapon_results = weapon_model(img, conf=0.5, verbose=False)[0]
    img = weapon_results.plot()

    detected = [weapon_model.names[int(b.cls[0])] for b in weapon_results.boxes]
    if detected:
        print("Detected:", detected)
    
    alert_triggered = False
    alert_message = ""
    alert_type=""
    alert_conf=0.0

    current_hour=datetime.now().hour
    CLOSING_HOUR=17

    threat_classes=["guns", "knife", "Violence"]
    # weapon/violence threat
    for box in weapon_results.boxes:
        class_id = int(box.cls[0])
        class_name = weapon_model.names[class_id]
        if class_name.lower() in threat_classes:
            alert_triggered = True
            alert_type=class_name
            alert_conf=float(box.conf[0])
            alert_message = "ALERT: " + class_name + " detected!"
            break
    
    #context rule: if person is repeatedly seen afterhours then alert
    person_results=general_model(img, classes=[0], conf=0.5, verbose=False)[0]
    person_count=len(person_results.boxes)
    if person_count>0 and current_hour>=CLOSING_HOUR:
        alert_triggered=True
        if alert_type="":
            alert_type="after-hours"
            alert_message="ALERT: Person detected after hours"
        
    return img, alert_triggered, alert_message, alert_type, alert_conf

webcam = cv2.VideoCapture(0)

while True:
    ret, img = webcam.read('knife.jpg')
    if not ret:
        break

    img, alert_triggered, alert_message, alert_type, alert_conf = process_frame(img)

    if alert_triggered:
        cv2.putText(img, alert_message,(20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        winsound.Beep(1000, 200)
        log_alert(alert_type, alert_conf)

    cv2.imshow("Surveillance System", img)
    if cv2.waitKey(1) == 27:   # ESC
        break
'''img = cv2.imread("knife.jpg")        
img, alert_triggered, alert_message, alert_type, alert_conf = process_frame(img)

if alert_triggered:
    cv2.putText(img, alert_message, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)

cv2.imshow("Surveillance System", img)
cv2.waitKey(0) '''                         # 0 = key thichunjel screen ma rakhne
cv2.destroyAllWindows()
    