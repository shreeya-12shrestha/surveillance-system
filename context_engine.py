"""
Context-Aware Threat Assessment Engine for the Real-Time Surveillance System.
"""
import time
from collections import deque

IGNORE, LOG, NOTIFY, ALARM = 0, 1, 2, 3
TIER_NAME = {IGNORE: "IGNORE", LOG: "LOG", NOTIFY: "NOTIFY", ALARM: "ALARM"}

class ThreatAssessor:
    def __init__(self,
                 fight_max_people=2,
                 weapon_conf=0.60,
                 closing_hour=11,
                 dwell_seconds=10,
                 log_cooldown=30,
                 notify_cooldown=20):
        self.fight_max_people = fight_max_people
        self.weapon_conf = weapon_conf
        self.closing_hour = closing_hour
        self.dwell_seconds = dwell_seconds
        self.log_cooldown = log_cooldown
        self.notify_cooldown = notify_cooldown

        self._people_hist = deque(maxlen=40)
        self._track_start = {}
        self._last_fire = {}
        

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

    def assess(self, weapons=None, person_count=0,
               track_ids=None, current_hour=None, now=None,
               event_active=False, event_expected_crowd=0):
        weapons = weapons or []
        track_ids = track_ids or []
        now = time.time() if now is None else now
        if current_hour is None:
            current_hour = time.localtime(now).tm_hour
        after_hours = (current_hour >= self.closing_hour) or (current_hour < 5)
        
        if event_active:
            after_hours = False                     
        crowd_limit = max(3, event_expected_crowd) if event_active else 3

        guns_knives = self._strong_weapons(weapons)
        has_weapon = len(guns_knives) > 0
        self._people_hist.append(person_count)
        smoothed_people = max(self._people_hist) if self._people_hist else person_count

        if has_weapon and person_count >= 2:
            if self._cooldown_ok("weapon-near-people", now, self.notify_cooldown):
                return NOTIFY, "weapon-near-people", f"NOTIFY: {guns_knives[0]} near people", 0.7
            return IGNORE, "", "", 0.0

        if self._loitering(track_ids, now, after_hours):
            if self._cooldown_ok("loitering", now, self.notify_cooldown):
                return NOTIFY, "loitering", "NOTIFY: Loitering after hours", 0.5
            return IGNORE, "", "", 0.0
        if smoothed_people > self.fight_max_people and not event_active:
            if self._cooldown_ok("crowd-detected", now, self.notify_cooldown):
                return NOTIFY, "crowd-detected", f"NOTIFY: Crowd detected ({smoothed_people} people)", 0.6
            
        if after_hours and person_count >= crowd_limit:
            if self._cooldown_ok("after-hours-crowd", now, self.notify_cooldown):
                return NOTIFY, "after-hours-crowd", "NOTIFY: Crowd after working hours", 0.6
            return IGNORE, "", "", 0.0

        if after_hours and person_count >= 1:
            if self._cooldown_ok("after-hours-person", now, self.log_cooldown):
                return LOG, "after-hours-person", f"logged: Single person detected after hours", 0.5
            
        if has_weapon:
            if self._cooldown_ok("weapon-seen", now, self.log_cooldown):
                return LOG, "weapon-seen", f"logged: {guns_knives[0]} seen (monitoring)", 0.4
            return IGNORE, "", "", 0.0

        return IGNORE, "", "", 0.0