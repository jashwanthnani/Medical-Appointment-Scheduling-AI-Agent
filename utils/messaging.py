# utils/messaging.py
import os
from datetime import datetime

OUTBOX_DIR = "outbox"
os.makedirs(OUTBOX_DIR, exist_ok=True)

def _write_message(fname: str, content: str, attachments=None):
    path = os.path.join(OUTBOX_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        if attachments:
            f.write("\n\nAttachments:\n")
            for a in attachments:
                f.write(f"- {a}\n")
    return path

def send_email_confirmation(to_email: str, subject: str, body: str, attachment_pdf_path: str = None):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    fname = f"email_{ts}.txt"
    attachments = [attachment_pdf_path] if attachment_pdf_path and os.path.exists(attachment_pdf_path) else None
    return _write_message(fname, f"TO: {to_email}\nSUBJECT: {subject}\n\n{body}", attachments)

def send_sms(to_phone: str, body: str):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    fname = f"sms_{ts}.txt"
    return _write_message(fname, f"TO: {to_phone}\n\n{body}")

def build_reminder_messages(name, date_str, start, email, phone):
    remind1 = f"Hi {name}, reminder of your appointment on {date_str} at {start}."
    remind2 = f"Hi {name}, have you filled the intake form? Please confirm your visit."
    remind3 = f"Hi {name}, final reminder: confirm your visit for {date_str} at {start} or reply with cancellation reason."
    return [
        ("email", email, "Appointment Reminder", remind1),
        ("sms", phone, None, remind1),
        ("email", email, "Action Needed: Intake Form + Confirmation", remind2),
        ("sms", phone, None, remind2),
        ("email", email, "Final Reminder", remind3),
        ("sms", phone, None, remind3),
    ]
