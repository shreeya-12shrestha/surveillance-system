"""
email_alert.py — sends a Google-style security-alert email to the logged-in
operator. The email includes a "This was a false alarm" BUTTON; clicking it hits
the /dismiss route in app.py and marks the alert false in the database directly
(just like Google's "No, it wasn't me" button). No reply, no login needed.
"""
import smtplib
from email.message import EmailMessage
from datetime import datetime

SENDER   = "surveillancesystem077@gmail.com"
APP_PASS = "abfh myyc kugr njhk"
SYSTEM_NAME = "Surveillance System"
BASE_URL = "http://192.168.18.6"
DISMISS_SECRET = "kec_surveillance_2026"

def send_email_alert(to_email, message, alert_id):
    """Email the operator on a real threat, with a one-click 'false alarm' button."""
    if not to_email: return
    time_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    dismiss_url = f"{BASE_URL}/dismiss/{alert_id}/{DISMISS_SECRET}"
    broadcast_url = f"{BASE_URL}/email_broadcast/{alert_id}/{DISMISS_SECRET}"
    try:
        msg = EmailMessage()
        msg["Subject"] = f"Security Alert: {message} [ID:{alert_id}]"
        msg["From"] = f"{SYSTEM_NAME} <{SENDER}>"
        msg["To"] = to_email
        msg.set_content(
            f"SECURITY ALERT\n\n{message}\n\nAlert ID: {alert_id}\nTime: {time_str}\n\n"
            f"If this was NOT a real threat, click to dismiss it:\n{dismiss_url}\n\n"
            f"-- Automated notification, {SYSTEM_NAME}"
        )
        html = f"""
        <div style="font-family:Arial,sans-serif; max-width:480px; margin:auto; border:1px solid #e0e0e0; border-radius:10px; overflow:hidden;">
          <div style="background:#d93025; color:#ffffff; padding:16px 22px;"><h2 style="margin:0; font-size:18px;">&#9888; Security Alert</h2></div>
          <div style="padding:22px; color:#202124;">
            <p style="font-size:15px; margin-top:0;">A security event was detected.</p>
            <p><strong>Event:</strong> {message}</p>
            <a href="{dismiss_url}" style="display:inline-block; background:#d93025; color:#ffffff; text-decoration:none; padding:10px 20px; border-radius:6px; font-weight:bold;">No, it was a false alarm</a>
            <a href="{broadcast_url}" style="background:#ff9800; color:#ffffff; text-decoration:none; padding:10px 20px; border-radius:6px; font-weight:bold;">Broadcast to Colony</a>
          </div>
        </div>
        """
        msg.add_alternative(html, subtype="html")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER, APP_PASS)
            server.send_message(msg)
    except Exception as e:
        print("[EMAIL] failed:", e)

def send_colony_broadcast(emails_list, alert_message, sender_username, lat, lng, alert_id):
    """Broadcasts a verified threat to all colony members with a map link."""
    if not emails_list: return
    time_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    location_url = f"https://www.google.com/maps?q={lat},{lng}" if lat and lng else "Location not available"
    
    for email in emails_list:
        try:
            msg = EmailMessage()
            msg["Subject"] = f"COLONY ALERT: Verified Threat from {sender_username}"
            msg["From"] = f"{SYSTEM_NAME} <{SENDER}>"
            msg["To"] = email
            msg.set_content(
                f"EMERGENCY BROADCAST\n\nMember '{sender_username}' has verified a threat.\n"
                f"Event: {alert_message}\nTime: {time_str}\n\n"
                f"Location: {location_url}\n\nPlease exercise caution."
            )
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(SENDER, APP_PASS)
                server.send_message(msg)
        except Exception as e:
            print(f"[BROADCAST] failed to send to {email}:", e)