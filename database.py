import sqlite3
import secrets
from datetime import datetime
from werkzeug.security import generate_password_hash

DATABASE = "database.db"

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Original & New Tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS colonies (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, join_code TEXT UNIQUE NOT NULL, created_at TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, email TEXT, role TEXT DEFAULT 'Operator', colony_id INTEGER, latitude REAL, longitude REAL, FOREIGN KEY(colony_id) REFERENCES colonies(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS deleted_users (id INTEGER PRIMARY KEY AUTOINCREMENT, original_user_id INTEGER, username TEXT, email TEXT, role TEXT, deleted_at TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, alert_type TEXT, confidence REAL, is_false_alarm INTEGER DEFAULT 0, operator_username TEXT DEFAULT 'system', is_broadcasted INTEGER DEFAULT 0)''')
        
        cursor.execute("SELECT * FROM users WHERE username='admin'")
        if not cursor.fetchone():
            hashed_pw = generate_password_hash('admin123')
            cursor.execute("INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, 'Admin')", ('admin', hashed_pw, 'admin@system.local'))
    conn.commit()

# --- ORIGINAL ALERT FUNCTIONS ---
def log_alert(alert_type, confidence, operator_username="system"):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO alerts (timestamp, alert_type, confidence, operator_username) VALUES (?, ?, ?, ?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), alert_type, confidence, operator_username))
        conn.commit()
        return cursor.lastrowid

def mark_false_alarm(alert_id):
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("UPDATE alerts SET is_false_alarm = 1 WHERE id = ?", (alert_id,))
        conn.commit()

def count_after_hours():
    with sqlite3.connect(DATABASE) as conn:
        count = conn.execute("SELECT COUNT(*) FROM alerts WHERE alert_type = 'after-hours'").fetchone()[0]
    return count

# --- ORIGINAL EVENT FUNCTIONS ---
def init_events():
    conn = sqlite3.connect(DATABASE)
    conn.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, event_date TEXT, name TEXT, start_hour INTEGER, end_hour INTEGER, expected_crowd INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS deleted_events (id INTEGER PRIMARY KEY AUTOINCREMENT, original_event_id INTEGER, event_date TEXT, name TEXT, start_hour INTEGER, end_hour INTEGER, expected_crowd INTEGER, deleted_at TEXT)")
    conn.commit()
    conn.close()

def add_event(event_date, name, start_hour, end_hour, expected_crowd):
    conn = sqlite3.connect(DATABASE)
    conn.execute("INSERT INTO events (event_date, name, start_hour, end_hour, expected_crowd) VALUES (?, ?, ?, ?, ?)", (event_date, name, int(start_hour), int(end_hour), int(expected_crowd)))
    conn.commit()
    conn.close()

def get_all_events():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM events ORDER BY event_date DESC").fetchall()
    conn.close()
    return rows

def get_active_event():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    hour = now.hour
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT name, expected_crowd FROM events WHERE event_date=? AND start_hour<=? AND end_hour>?", (today, hour, hour)).fetchone()
    conn.close()
    return (row["name"], row["expected_crowd"]) if row else None

# --- NEW COLONY & BROADCAST FUNCTIONS ---
def mark_alert_broadcasted(alert_id):
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("UPDATE alerts SET is_broadcasted = 1 WHERE id = ?", (alert_id,))
        conn.commit()

def create_colony(name):
    join_code = secrets.token_hex(4).upper()
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO colonies (name, join_code, created_at) VALUES (?, ?, ?)", (name, join_code, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return cursor.lastrowid, join_code

def join_colony_by_code(username, code):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        colony = cursor.execute("SELECT id FROM colonies WHERE join_code=?", (code,)).fetchone()
        if colony:
            cursor.execute("UPDATE users SET colony_id=? WHERE username=?", (colony[0], username))
            conn.commit()
            return True
        return False

def update_user_location(username, lat, lng):
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("UPDATE users SET latitude=?, longitude=? WHERE username=?", (lat, lng, username))
        conn.commit()