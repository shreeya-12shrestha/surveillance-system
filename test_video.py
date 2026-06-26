import cv2
import winsound
import time
from datetime import datetime
from ultralytics import YOLO
from database import init_db, log_alert, count_after_hours

init_db() #makes new register

CLOSING_HOUR=17
REPEAT_THRESHOLD=3

general_model = YOLO("yolov8s.pt")
weapon_model = YOLO("best.pt")

def process_frame(img):

    img = cv2.flip(img, 1)

    person_results = general_model(img, classes=[0], conf=0.5, verbose=False)[0]
    img = person_results.plot()
    person_count = len(person_results.boxes)
    
    weapon_results = weapon_model(img, conf=0.5, verbose=False)[0]
    img = weapon_results.plot()

    detected = [weapon_model.names[int(b.cls[0])] for b in weapon_results.boxes]
    if detected:
        print("Detected:", detected)
    
    alert_triggered = False
    alert_message = ""
    alert_type=""
    alert_conf=0.0


    threat_classes=["guns", "knife", "violence"]
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
    return img, alert_triggered, alert_message, alert_type, alert_conf, person_count

webcam=cv2.VideoCapture(0)
last_after_hours_log=0

while True:
    ret, img= webcam.read()
    if not ret:
        break

    img, alert_triggered, alert_message, alert_type, alert_conf, person_count=process_frame(img)
    
     # CONTEXT-AWARE: after-hours pattern 
    current_hour = datetime.now().hour
    if person_count > 0 and current_hour >= CLOSING_HOUR:
        # cooldown: 10 sec ma euta matra record (har frame ma haina)
        if time.time() - last_after_hours_log > 10:
            log_alert("after-hours", 1.0)
            last_after_hours_log = time.time()
            times_seen = count_after_hours()

            if times_seen >= REPEAT_THRESHOLD:
                alert_triggered = True
                alert_message = "ALERT: Repeated after-hours pattern!"
                alert_type = "after-hours-pattern"
            else:
                print("After-hours presence logged (monitoring). Count:", times_seen)
        

    if alert_triggered:
        cv2.putText(img, alert_message,(20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        winsound.Beep(1000, 200)
        if alert_type not in ("", 'after-hours-pattern'):
            log_alert(alert_type, alert_conf)

    cv2.imshow("Surveillance System", img)
    if cv2.waitKey(1) == 27:   # ESC
        break
'''img = cv2.imread("knife.jpg")        
img, alert_triggered, alert_message, alert_type, alert_conf = process_frame(img)

if alert_triggered:
    cv2.putText(img, alert_message, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)

cv2.imshow("Surveillance System", img)
cv2.waitKey(0) ''' 
webcam.release()                        # 0 = key thichunjel screen ma rakhne
cv2.destroyAllWindows()
    