import os
import csv
import smtplib
import re
import time
import logging
from datetime import datetime
from email.message import EmailMessage
from typing import Set, Dict, List
from dotenv import load_dotenv

# --- Production Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("app_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

class Config:
    """Production Configuration Management"""
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    
    CSV_PATH = "send.csv"
    ATTACH_DIR = "send folder"
    REPORT_PATH = "send_report.csv"
    
    SUBJECT = "Show-Cause Notice"
    SEND_DELAY = 1.5  # Seconds
    
    BODY_TEMPLATE = """
Respected Sir/Madam,

Please find the attached document regarding the above subject.

Thanks and Regards,
ARCHANA K. PATIL
Assistant Commissioner Of Profession Tax,
Chhatrapati Sambhajinagar.
"""

class EmailValidator:
    """Utility for structural email validation"""
    @staticmethod
    def is_valid(email: str) -> bool:
        if not email or not isinstance(email, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None

class StateManager:
    """Manages the persistence and recovery of sending state"""
    def __init__(self, report_path: str):
        self.report_path = report_path
        self.fieldnames = ["Sr. No.", "Recipient Name", "Email", "Notice Name", "Status", "Timestamp", "Error"]

    def get_sent_serials(self) -> Set[str]:
        sent_serials = set()
        if not os.path.exists(self.report_path):
            return sent_serials
        
        try:
            with open(self.report_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Status") == "Sent":
                        sent_serials.add(row.get("Sr. No."))
        except Exception as e:
            logger.error(f"Failed to read state file: {e}")
        return sent_serials

    def log_attempt(self, data: Dict):
        file_exists = os.path.exists(self.report_path)
        try:
            with open(self.report_path, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                if not file_exists:
                    writer.writeheader()
                
                log_entry = {
                    **data,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                writer.writerow(log_entry)
        except Exception as e:
            logger.error(f"Failed to write to report: {e}")

class BulkEmailEngine:
    """Core engine for managing the SMTP lifecycle and batch processing"""
    def __init__(self):
        self.state = StateManager(Config.REPORT_PATH)
        self.server = None

    def connect(self):
        try:
            self.server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
            self.server.starttls()
            self.server.login(Config.EMAIL_USER, Config.EMAIL_PASS)
            logger.info("Connected to SMTP Server successfully.")
        except Exception as e:
            logger.critical(f"SMTP Connection Failed: {e}")
            raise

    def process_batch(self):
        if not os.path.exists(Config.CSV_PATH):
            logger.error(f"Source file {Config.CSV_PATH} not found.")
            return

        sent_serials = self.state.get_sent_serials()
        logger.info(f"System ready. {len(sent_serials)} records previously completed.")

        try:
            with open(Config.CSV_PATH, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            for i, row in enumerate(rows, 1):
                self._process_single_row(i, row, sent_serials)
                
        finally:
            if self.server:
                self.server.quit()
                logger.info("SMTP connection closed.")

    def _process_single_row(self, index: int, row: Dict, sent_serials: Set[str]):
        sr_no = (row.get("Sr. No.") or "").strip()
        name = (row.get("Recipient Name") or row.get("Name") or "Taxpayer").strip()
        email = (row.get("Email") or "").strip()
        filename = f"A--{sr_no}.pdf"
        filepath = os.path.join(Config.ATTACH_DIR, filename)

        # 1. Skip logic
        if sr_no in sent_serials:
            return

        # 2. Validation
        if not EmailValidator.is_valid(email):
            logger.warning(f"Row {index}: Invalid email '{email}'")
            self.state.log_attempt(self._build_log(sr_no, name, email, filename, "Failed", "Invalid Email"))
            return

        if not os.path.isfile(filepath):
            logger.warning(f"Row {index}: Missing attachment '{filename}'")
            self.state.log_attempt(self._build_log(sr_no, name, email, filename, "Failed", "File Missing"))
            return

        # 3. Execution
        try:
            msg = self._prepare_message(email, sr_no, filepath, filename)
            self.server.send_message(msg)
            logger.info(f"SUCCESS: Sr.No {sr_no} -> {email}")
            self.state.log_attempt(self._build_log(sr_no, name, email, filename, "Sent"))
            time.sleep(Config.SEND_DELAY)
        except Exception as e:
            logger.error(f"FAILURE: Sr.No {sr_no} -> {e}")
            self.state.log_attempt(self._build_log(sr_no, name, email, filename, "Failed", str(e)))
            if "daily user sending limit" in str(e).lower():
                logger.critical("Provider quota reached. Terminating batch.")
                raise SystemExit

    def _prepare_message(self, to_email: str, sr_no: str, filepath: str, filename: str) -> EmailMessage:
        msg = EmailMessage()
        msg["From"] = Config.EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = f"{Config.SUBJECT} - {sr_no}"
        msg.set_content(Config.BODY_TEMPLATE)
        
        with open(filepath, "rb") as f:
            msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=filename)
        return msg

    def _build_log(self, sr_no, name, email, notice, status, error="") -> Dict:
        return {
            "Sr. No.": sr_no,
            "Recipient Name": name,
            "Email": email,
            "Notice Name": notice,
            "Status": status,
            "Error": error
        }

if __name__ == "__main__":
    engine = BulkEmailEngine()
    try:
        engine.connect()
        engine.process_batch()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
    except Exception as e:
        logger.error(f"Application crash: {e}")
