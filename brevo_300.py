import os
import csv
import smtplib
import mimetypes
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp-relay.brevo.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

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

def main():
    print("Connecting to Brevo SMTP...")
    
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        print("✅ Brevo connected!")

        sent = 0
        with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                sr_no_raw = row["Sr. No."].strip()
            
                # RESUME FROM 215 + LIMIT 300
                try:
                    sr_no_int = int(sr_no_raw)
                    if sr_no_int < 215 or sent >= 300:
                        continue
                except ValueError:
                    continue

                to_email = row["Email"].strip()
                if not to_email or "@" not in to_email:
                    print(f"[SKIP] Row {row_num}: '{to_email}'")
                    continue

                filename = f"A--{sr_no_raw}.pdf"
                filepath = os.path.join(ATTACH_DIR, filename)

                if not os.path.isfile(filepath):
                    print(f"[SKIP] Row {row_num} Sr.{sr_no_raw}: {filename}")
                    continue

                msg = EmailMessage()
                msg["From"] = EMAIL_USER
                msg["To"] = to_email
                msg["Subject"] = SUBJECT
                msg.set_content(BODY_TEMPLATE)

                # Attachment
                ctype, _ = mimetypes.guess_type(filepath)
                if ctype is None:
                    ctype = "application/pdf"
                maintype, subtype = ctype.split("/", 1)

                with open(filepath, "rb") as f:
                    msg.add_attachment(
                        f.read(),
                        maintype=maintype,
                        subtype=subtype,
                        filename=filename
                    )

                server.send_message(msg)
                sent += 1
                print(f"✅ Row {row_num} Sr.No {sr_no_raw} -> {to_email} ({sent}/300)")

    print(f"\n🎉 BREVO: {sent} emails sent! Next batch tomorrow.")

if __name__ == "__main__":
    main()
