import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("alerts.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            alert_type TEXT,
            confidence REAL,
            is_false_alarm INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def log_alert(alert_type, confidence):
    conn = sqlite3.connect("alerts.db")
    conn.execute(
        "INSERT INTO alerts (timestamp, alert_type, confidence) VALUES (?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), alert_type, confidence)
    )
    conn.commit()
    conn.close()