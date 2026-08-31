import os
import csv
import smtplib
import mimetypes
import re
import time
from datetime import datetime
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

CSV_PATH = "send.csv"
ATTACH_DIR = "send folder"
REPORT_PATH = "send_report.csv"

SUBJECT = "Show-Cause Notice"
BODY_TEMPLATE = """
Respected Sir/Madam,

Please find the attached document regarding the above subject.

Thanks and Regards,
ARCHANA K. PATIL
Assistant Commissioner Of Profession Tax,
Chhatrapati Sambhajinagar.
"""

# Delay between emails (seconds) to avoid rate limits
SEND_DELAY = 1.5

def is_valid_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    email = email.strip()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_sent_serials():
    """Reads the report file and returns a set of Sr. Nos that were successfully sent."""
    sent_serials = set()
    if not os.path.exists(REPORT_PATH):
        return sent_serials
    
    with open(REPORT_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("Status") == "Sent":
                sent_serials.add(row.get("Sr. No."))
    return sent_serials

def log_attempt(sr_no, name, email, notice, status, error=""):
    """Appends an attempt result to the report file."""
    file_exists = os.path.exists(REPORT_PATH)
    with open(REPORT_PATH, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Sr. No.", "Recipient Name", "Email", "Notice Name", "Status", "Timestamp", "Error"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "Sr. No.": sr_no,
            "Recipient Name": name,
            "Email": email,
            "Notice Name": notice,
            "Status": status,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Error": error
        })

def main():
    if not EMAIL_USER or not EMAIL_PASS:
        print("❌ Error: EMAIL_USER or EMAIL_PASS missing from .env")
        return

    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: CSV file not found at {CSV_PATH}")
        return

    if not os.path.exists(ATTACH_DIR):
        os.makedirs(ATTACH_DIR)
        print(f"⚠️ Created missing directory: {ATTACH_DIR}")

    sent_serials = get_sent_serials()
    print(f"🚀 Loaded {len(sent_serials)} already sent records. Starting...")

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            print("✅ Connected to Google SMTP.")

            with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            for i, row in enumerate(rows, 1):
                sr_no = (row.get("Sr. No.") or "").strip()
                # Try to get name if it exists, else default to 'Taxpayer'
                name = (row.get("Recipient Name") or row.get("Name") or "Taxpayer").strip()
                email = (row.get("Email") or "").strip()
                
                filename = f"A--{sr_no}.pdf"
                filepath = os.path.join(ATTACH_DIR, filename)

                # 1. Check if already sent
                if sr_no in sent_serials:
                    continue

                # 2. Validate email
                if not is_valid_email(email):
                    print(f"⚠️ [SKIP] Row {i} Sr.No {sr_no}: Invalid Email '{email}'")
                    log_attempt(sr_no, name, email, filename, "Failed", "Invalid Email Format")
                    continue

                # 3. Check for attachment
                if not os.path.isfile(filepath):
                    print(f"⚠️ [SKIP] Row {i} Sr.No {sr_no}: Missing File {filename}")
                    log_attempt(sr_no, name, email, filename, "Failed", "Attachment Missing")
                    continue

                # 4. Prepare Email
                msg = EmailMessage()
                msg["From"] = EMAIL_USER
                msg["To"] = email
                msg["Subject"] = f"{SUBJECT} - {sr_no}"
                msg.set_content(BODY_TEMPLATE)

                try:
                    with open(filepath, "rb") as attachment:
                        msg.add_attachment(
                            attachment.read(),
                            maintype="application",
                            subtype="pdf",
                            filename=filename
                        )

                    # 5. Send
                    server.send_message(msg)
                    print(f"✅ [SENT] Row {i} Sr.No {sr_no} to {email}")
                    log_attempt(sr_no, name, email, filename, "Sent")
                    
                    # Add delay to avoid Google Workspace burst limits
                    time.sleep(SEND_DELAY)

                except Exception as e:
                    print(f"❌ [ERROR] Row {i} Sr.No {sr_no}: {e}")
                    log_attempt(sr_no, name, email, filename, "Failed", str(e))
                    # Wait longer if we hit a rate limit
                    if "5.4.5" in str(e) or "Daily user sending limit exceeded" in str(e):
                        print("🛑 Google sending limit reached. Stopping script.")
                        break

    except Exception as e:
        print(f"🛑 Fatal Connection Error: {e}")

    print("\n" + "="*50)
    print("Process Finished. Check 'send_report.csv' for details.")
    print("="*50)

if __name__ == "__main__":
    main()
