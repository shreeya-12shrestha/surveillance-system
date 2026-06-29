import sqlite3

def view_alerts():
    conn = sqlite3.connect("alerts.db")
    rows = conn.execute(
        "SELECT id, timestamp, alert_type, confidence, is_false_alarm FROM alerts ORDER BY id DESC"
    ).fetchall()
    conn.close()

    if not rows:
        print("No alerts logged yet.")
        return

    print("\n----- ALERT LOG -----")
    print(f"{'ID':<5}{'Time':<22}{'Type':<20}{'Conf':<8}{'False?'}")
    print("-" * 60)
    for r in rows:
        aid, ts, atype, conf, false_flag = r
        false_str = "YES" if false_flag == 1 else "no"
        print(f"{aid:<5}{ts:<22}{atype:<20}{round(conf,2):<8}{false_str}")
    print("-" * 60)


def mark_false_alarm():
    alert_id = input("\nFalse alarm ko alert ID halnus (skip garna Enter): ").strip()
    if alert_id == "":
        return
    conn = sqlite3.connect("alerts.db")
    conn.execute("UPDATE alerts SET is_false_alarm = 1 WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()
    print(f"Alert {alert_id} marked as FALSE ALARM.")


if __name__ == "__main__":
    while True:
        view_alerts()
        mark_false_alarm()
        again = input("\nArko mark garne? (y/n): ").strip().lower()
        if again != "y":
            print("Exiting review.")
            break