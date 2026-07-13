"""
context_engine.py
--------------------------------------------------------------------------------
Context-Aware Threat Assessment Engine for the Real-Time Surveillance System.
"""
import time
from collections import deque

# response tiers as ordered numbers (higher = more severe)
IGNORE, LOG, NOTIFY, ALARM = 0, 1, 2, 3
TIER_NAME = {IGNORE: "IGNORE", LOG: "LOG", NOTIFY: "NOTIFY", ALARM: "ALARM"}


class ThreatAssessor:
    def __init__(self,
                 violence_threshold=0.75,   # confidence for a frame to count as violent
                 violence_streak=25,        # violent frames in a row before it's 'real' (filters brief hugs)
                 fight_max_people=5,        # <= this many people = normal fight threshold
                 crowd_violence_threshold=0.90,  # crowds need HIGHER confidence to alarm (they over-score)
                 weapon_conf=0.60,          # ignore weapon detections below this confidence
                 closing_hour=17,           # after-hours starts (5 PM)
                 dwell_seconds=15,          # loitering threshold
                 log_cooldown=30,           # seconds between repeated LOGs of same type
                 notify_cooldown=20):       # seconds between repeated NOTIFYs of same type
        self.violence_threshold = violence_threshold
        self.violence_streak_needed = violence_streak
        self.fight_max_people = fight_max_people
        self.crowd_violence_threshold = crowd_violence_threshold
        self.weapon_conf = weapon_conf
        self.closing_hour = closing_hour
        self.dwell_seconds = dwell_seconds
        self.log_cooldown = log_cooldown
        self.notify_cooldown = notify_cooldown

        self._violent_streak = 0     # consecutive violent frames
        self._people_hist = deque(maxlen=40)   # recent person counts (smooths flicker)
        self._track_start = {}       # person_id -> first-seen time (loitering)
        self._last_fire = {}         # alert_type -> last time we acted on it

    # ---------- helper rules ----------
    def _sustained_violence(self, prob):
        if prob >= self.violence_threshold:
            self._violent_streak += 1
        else:
            self._violent_streak = 0
        return self._violent_streak >= self.violence_streak_needed

    def _strong_weapons(self, weapons):
        return [name for (name, conf) in weapons if conf >= self.weapon_conf]

    def _loitering(self, track_ids, now, after_hours):
        if not after_hours:
            self._track_start.clear()
            return False
        for pid in track_ids:
            self._track_start.setdefault(pid, now)
            if now - self._track_start[pid] > self.dwell_seconds:
                return True
        return False

    def _cooldown_ok(self, alert_type, now, cooldown):
        if now - self._last_fire.get(alert_type, -1e9) >= cooldown:
            self._last_fire[alert_type] = now
            return True
        return False

    # ---------- main decision ----------
    def assess(self, violence_prob=0.0, weapons=None, person_count=0,
               track_ids=None, current_hour=None, now=None,
               event_active=False, event_expected_crowd=0):
        weapons = weapons or []
        track_ids = track_ids or []
        now = time.time() if now is None else now
        if current_hour is None:
            current_hour = time.localtime(now).tm_hour
        after_hours = (current_hour >= self.closing_hour) or (current_hour < 5)
        
        # NEW: Log single person appearing after hours
        if after_hours and person_count >= 1:
            if self._cooldown_ok("after-hours-person", now, self.log_cooldown):
                return LOG, "after-hours-person", f"logged: Single person detected after hours", 0.5
            return IGNORE, "", "", 0.0
        
        if event_active:
            after_hours = False                     
        crowd_limit = max(3, event_expected_crowd) if event_active else 3

        sustained = self._sustained_violence(violence_prob)
        guns_knives = self._strong_weapons(weapons)
        has_weapon = len(guns_knives) > 0

        # ================= ESCALATION MATRIX =================

        # 1) weapon + sustained violence -> ALARM
        if has_weapon and sustained:
            return ALARM, "weapon+violence", f"ALARM: {guns_knives[0]} with violence!", violence_prob

        # 2) sustained violence decision
        self._people_hist.append(person_count)
        smoothed_people = max(self._people_hist)      
        is_crowd = smoothed_people > self.fight_max_people and not event_active

        if sustained:
            if is_crowd:
                if self._cooldown_ok("crowd-motion", now, self.notify_cooldown):
                    return NOTIFY, "crowd-motion", "NOTIFY: High activity in a crowd (review)", 0.5
                return IGNORE, "", "", 0.0
            return ALARM, "violence", "ALARM: Violence detected!", violence_prob

        # 3) weapon among several people -> notify
        if has_weapon and person_count >= 2:
            if self._cooldown_ok("weapon-near-people", now, self.notify_cooldown):
                return NOTIFY, "weapon-near-people", f"NOTIFY: {guns_knives[0]} near people", 0.7
            return IGNORE, "", "", 0.0

        # 4) crowd after hours -> notify
        if after_hours and person_count >= crowd_limit:
            if self._cooldown_ok("after-hours-crowd", now, self.notify_cooldown):
                return NOTIFY, "after-hours-crowd", "NOTIFY: Crowd after working hours", 0.6
            return IGNORE, "", "", 0.0

        # 5) loitering after hours -> notify
        if self._loitering(track_ids, now, after_hours):
            if self._cooldown_ok("loitering", now, self.notify_cooldown):
                return NOTIFY, "loitering", "NOTIFY: Loitering after hours", 0.5
            return IGNORE, "", "", 0.0

        # 6) LONE weapon -> SILENT LOG
        if has_weapon:
            if self._cooldown_ok("weapon-seen", now, self.log_cooldown):
                return LOG, "weapon-seen", f"logged: {guns_knives[0]} seen (monitoring)", 0.4
            return IGNORE, "", "", 0.0

        return IGNORE, "", "", 0.0