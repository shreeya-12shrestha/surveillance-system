import cv2
from ultralytics import YOLO

general_model = YOLO("yolov8s.pt")
weapon_model = YOLO("best.pt")

# photo padhne (webcam haina)
img = cv2.imread("man.jpg")
img = cv2.resize(img, (800, 600)) 

# person detect
img = general_model(img, classes=[0], conf=0.5, verbose=False)[0].plot()

# weapon detect
weapon_results = weapon_model(img, conf=0.5, verbose=False)[0]
img = weapon_results.plot()

# alert message screen ma
alert_message = ""
threat_classes = ["guns", "knife", "violence"]
for box in weapon_results.boxes:
    class_name = weapon_model.names[int(box.cls[0])]
    print("Detected:", class_name)
    if class_name.lower() in threat_classes:
        alert_message = "ALERT: " + class_name + " detected!"
        break

if alert_message:
    cv2.putText(img, alert_message, (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

cv2.imshow("Surveillance System", img)
cv2.waitKey(0)              
cv2.destroyAllWindows()