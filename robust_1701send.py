import os
import csv
import smtplib
import mimetypes
import re
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# CONFIGURE THESE PATHS:
CSV_PATH = "1701.csv"
ATTACH_DIR = "SEGMENT A NOTICES"

SUBJECT = "Show-Cause Notice"
BODY_TEMPLATE = """

Respected Sir/Madam,
Please find an attachment regarding above subjects.


Thanks and Regards,
ARCHANA K. PATIL
CSN-ACPT-D-0001
Mobile: 9822637644
Assistant Commissioner Of Profession Tax,
Chhatrapati Sambhajinagar.
"""

def is_valid_email(email: str) -> bool:
    """Strict email validation"""
    if not email or not isinstance(email, str):
        return False
    email = email.strip()
    if len(email) > 254:
        return False
    # Basic regex for valid email format
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def srno_to_filename(sr_no: str) -> str:
    """Convert Sr No to filename"""
    sr_no_clean = sr_no.strip()
    return f"A--{sr_no_clean}.pdf"

def attach_file_if_exists(msg: EmailMessage, filepath: str) -> bool:
    """Attach file if it exists"""
    if not os.path.isfile(filepath):
        return False

    try:
        ctype, encoding = mimetypes.guess_type(filepath)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)

        with open(filepath, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(filepath),
            )
        return True
    except Exception as e:
        print(f"[ERROR] Attach failed {filepath}: {e}")
        return False

def main():
    if not EMAIL_USER or not EMAIL_PASS:
        raise RuntimeError("EMAIL_USER or EMAIL_PASS missing from .env")

    print("Reading CSV...")
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:  # utf-8-sig handles BOM
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Total rows in CSV: {len(rows)}")

    sent_count = 0
    skipped_bad_email = 0
    skipped_no_file = 0
    skipped_before_101 = 0
    bad_emails_sample = []

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            print("SMTP connected successfully")

            for i, row in enumerate(rows, 1):
                sr_no_raw = (row.get("Sr. No.") or "").strip()
                email_raw = (row.get("Email") or "").strip()

                # STRICT VALIDATION
                if not is_valid_email(email_raw):
                    skipped_bad_email += 1
                    if len(bad_emails_sample) < 5:  # Show first 5 bad emails
                        bad_emails_sample.append(f"Sr.{sr_no_raw}: '{email_raw}'")
                    print(f"[SKIP] Row {i} Sr.No {sr_no_raw}: invalid email '{email_raw}'")
                    continue

                # START FROM 215
                try:
                    sr_no_int = int(sr_no_raw)
                    if sr_no_int <= 214:
                        skipped_before_101 += 1
                        print(f"[SKIP] Row {i} Sr.No {sr_no_raw}: already sent")
                        continue
                except ValueError:
                    print(f"[SKIP] Row {i} Sr.No '{sr_no_raw}': not a number")
                    skipped_bad_email += 1
                    continue

                # Build and send email
                filename = srno_to_filename(sr_no_raw)
                filepath = os.path.join(ATTACH_DIR, filename)

                msg = EmailMessage()
                msg["From"] = EMAIL_USER
                msg["To"] = email_raw  # Already validated
                msg["Subject"] = SUBJECT
                msg.set_content(BODY_TEMPLATE)

                if not attach_file_if_exists(msg, filepath):
                    print(f"[SKIP] Row {i} Sr.No {sr_no_raw}: missing {filename}")
                    skipped_no_file += 1
                    continue

                try:
                    server.send_message(msg)
                    sent_count += 1
                    print(f"[OK]  Row {i} Sr.No {sr_no_raw} -> {email_raw} ({sent_count})")
                    
                    # Small delay to be nice to Gmail servers
                    if sent_count % 10 == 0:
                        print(f"--- Sent {sent_count} emails, continuing ---")
                        
                except smtplib.SMTPRecipientsRefused as e:
                    print(f"[SMTP ERROR] Row {i} Sr.No {sr_no_raw}: {e}")
                    skipped_bad_email += 1

    except Exception as e:
        print(f"[FATAL ERROR] {e}")

    print("\n" + "="*50)
    print("FINAL SUMMARY")
    print("="*50)
    print(f"Emails sent:           {sent_count}")
    print(f"Skipped bad/empty email: {skipped_bad_email}")
    if bad_emails_sample:
        print("Sample bad emails:")
        for sample in bad_emails_sample:
            print(f"  {sample}")
    print(f"Skipped no file:       {skipped_no_file}")
    print(f"Skipped <= Sr.100:     {skipped_before_101}")

if __name__ == "__main__":
    main()
