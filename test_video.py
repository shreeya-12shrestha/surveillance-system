import cv2
import time
import winsound
from datetime import datetime
from ultralytics import YOLO
from database import init_db, log_alert, count_after_hours
from violence_detector import ViolenceDetector   # NEW: temporal violence model

# ----------------- SETTINGS -----------------
CLOSING_HOUR = 17          # working hours pachi (5 PM) = after-hours
CROWD_THRESHOLD = 3        # yati bhanda badi manche after-hours = crowd
REPEAT_THRESHOLD = 3       # after-hours presence yati choti = suspicious pattern
DWELL_THRESHOLD = 15       # yati second bhanda badi basyo = loitering
THREAT_CLASSES = ["guns", "knife", "violence"]   # alert dine classes (false-alarm reduction)

# ----------------- SETUP -----------------
init_db()
general_model = YOLO("yolov8s.pt")    # person detection (pretrained)
weapon_model = YOLO("best.pt")         # weapon/violence detection (custom-trained)
violence_detector = ViolenceDetector("violence_mobilenet_lstm.pt")   # NEW: load trained violence model

track_start_time = {}      # har tracked person kahile pahile dekhiyo
last_after_hours_log = 0   # after-hours logging cooldown


def detect_weapon_threat(weapon_results):
    """Weapon/violence detect garcha. FALSE-ALARM REDUCTION: khali threat
    classes (gun/knife/violence) ma matra alert, NonViolence (normal) ma haina."""
    for box in weapon_results.boxes:
        class_name = weapon_model.names[int(box.cls[0])]
        if class_name.lower() in THREAT_CLASSES:
            conf = float(box.conf[0])
            return True, class_name, conf, "ALERT: " + class_name + " detected!"
    return False, "", 0.0, ""


def check_loitering(person_results, current_hour):
    """Tracking-based dwell-time. CONTEXT-AWARE: loitering alert khali
    after-hours ma (working hour ma manche basnu normal ho)."""
    if person_results.boxes.id is None or current_hour < CLOSING_HOUR:
        return False
    ids = person_results.boxes.id.int().tolist()
    now = time.time()
    for pid in ids:
        if pid not in track_start_time:
            track_start_time[pid] = now
        if now - track_start_time[pid] > DWELL_THRESHOLD:
            return True
    return False


def process_frame(img):
    img = cv2.flip(img, 1)
    current_hour = datetime.now().hour

    # 1) Person detection + tracking (ByteTrack ID)
    person_results = general_model.track(img, classes=[0], conf=0.5,
                                         persist=True, verbose=False)[0]
    img = person_results.plot()
    person_count = len(person_results.boxes)

    # 2) Weapon/violence detection
    weapon_results = weapon_model(img, conf=0.5, verbose=False)[0]
    img = weapon_results.plot()

    # 3) Threat decision (with false-alarm reduction)
    alert_triggered, alert_type, alert_conf, alert_message = detect_weapon_threat(weapon_results)

    # 4) Loitering (after-hours dwell-time)
    if not alert_triggered and check_loitering(person_results, current_hour):
        alert_triggered = True
        alert_type = "loitering"
        alert_message = "ALERT: Loitering detected after hours!"

    return img, alert_triggered, alert_message, alert_type, alert_conf, person_count


def apply_context_rules(person_count, alert_triggered, alert_message, alert_type):
    """CONTEXT-AWARE after-hours rules: same situation context anusar
    farak treat huncha (crowd = immediate, single = pattern-based)."""
    global last_after_hours_log
    current_hour = datetime.now().hour
    if current_hour < CLOSING_HOUR:
        return alert_triggered, alert_message, alert_type

    # Rule 1: crowd after-hours = immediate alert
    if person_count >= CROWD_THRESHOLD:
        return True, "ALERT: Crowd detected after working hours!", "after-hours-crowd"

    # Rule 2: few person after-hours = log; repeated pattern = alert
    elif person_count > 0:
        if time.time() - last_after_hours_log > 10:
            log_alert("after-hours", 1.0)
            last_after_hours_log = time.time()
            if count_after_hours() >= REPEAT_THRESHOLD:
                return True, "ALERT: Repeated after-hours pattern!", "after-hours-pattern"
            else:
                print("After-hours presence logged (monitoring).")

    return alert_triggered, alert_message, alert_type


# ----------------- MAIN LOOP -----------------
webcam = cv2.VideoCapture(0)

while True:
    ret, img = webcam.read()
    if not ret:
        break

    # NEW: feed the clean raw frame to the violence model (before boxes/flip)
    is_violent, violence_prob = violence_detector.update(img)

    img, alert_triggered, alert_message, alert_type, alert_conf, person_count = process_frame(img)

    # context-aware after-hours rules
    alert_triggered, alert_message, alert_type = apply_context_rules(
        person_count, alert_triggered, alert_message, alert_type)

    # NEW: temporal violence detection raises an alert
    if is_violent:
        alert_triggered = True
        alert_type = "violence"
        alert_message = "ALERT: Violence detected!"
        alert_conf = violence_prob

    # NEW: always show the live violence score (green = calm, red = violent) -- great for the demo
    cv2.putText(img, f"Violence: {violence_prob:.2f}", (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 0, 255) if is_violent else (0, 255, 0), 2)

    # ALERT: on-screen + SOUND + database log
    if alert_triggered:
        cv2.putText(img, alert_message, (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        winsound.Beep(1000, 200)   # sound alert on any intrusion/threat
        if alert_type not in ("", "after-hours-pattern", "after-hours-crowd"):
            log_alert(alert_type, alert_conf)

    cv2.imshow("Surveillance System", img)
    if cv2.waitKey(1) == 27:   # ESC to exit
        break

webcam.release()
cv2.destroyAllWindows()