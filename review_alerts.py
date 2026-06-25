import sqlite3

conn = sqlite3.connect("alerts.db")
rows = conn.execute("SELECT id, timestamp, alert_type, confidence, is_false_alarm FROM alerts").fetchall()

for row in rows:
    print(row)

# operator le false mark garne
alert_id = input("Enter the alert_id (Press Enter to skip): ")
if alert_id:
    conn.execute("UPDATE alerts SET is_false_alarm = 1 WHERE id = ?", (alert_id,))
    conn.commit()
    print("Alert", alert_id, "Marked as false alarm")
conn.close()