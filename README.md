# Bulk_emails
Automated bulk email sender for GST-PTRC show‑cause notices. 
# PTRC Bulk Email Sender

Automated bulk email sender for PTRC show‑cause notices.  
The script reads a CSV of taxpayers, maps each **Sr. No.** to a PDF notice (`A--<SrNo>.pdf`), and sends personalized emails with the correct attachment to each recipient using SMTP (Gmail or Brevo).

---

## Features

- Send emails to **1,000+ recipients** with a single command.
- Per‑recipient PDF attachment based on `Sr. No.` (e.g. `Sr No 489 → A--489.pdf`).
- Resumable sending (skip Sr. Nos already sent).
- Robust email validation and file‑existence checks.
- Pluggable SMTP backends:
  - Gmail (with App Password, subject to Gmail quota).
  - Brevo SMTP relay for higher daily volume.
- Clear console logging and basic summary statistics.

---

## Project structure

Example layout:

```text
Bulk_emails/
├── SEGMENT A NOTICES/        # Folder containing all notice PDFs
│   ├── A--31.pdf
│   ├── A--32.pdf
│   ├── ...
│   └── A--1701.pdf
├── 1701.csv                  # Main CSV with Sr. No. and Email
├── .env                      # SMTP credentials (NOT committed)
├── brevo_300.py              # Script to send up to 300 emails via Brevo
├── robust_1701send.py        # Script used with Gmail (subject to daily limits)
└── README.md

You can rename/reorganize as needed; keep the paths in the scripts in sync.

Prerequisites
Python 3.10+ installed.

A working SMTP account:

Gmail with 2‑Step Verification + App Password; or

Brevo account with an active SMTP key.

Basic familiarity with running commands in Command Prompt / PowerShell or a terminal.

CSV and notice mapping
The script assumes:

CSV has at least the following columns:

Sr. No. – numeric serial number (e.g. 31, 340, 489, 1701)

Email – recipient email address

PDF notice filenames follow:

A--<SrNo>.pdf

Examples:

Sr. No. = 31 → A--31.pdf

Sr. No. = 340 → A--340.pdf

Sr. No. = 489 → A--489.pdf

Sr. No. = 1701 → A--1701.pdf

If there are gaps in serial numbers (e.g. CSV jumps from 340 to 489), the script ignores unmatched PDFs (e.g. A--341.pdf…A--488.pdf are never used).

Setup
1. Clone the repository

git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

2. Create and activate a virtual environment (optional but recommended)

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

3. Install dependencies

pip install python-dotenv

(If you add more packages later, document them here.)

SMTP configuration (.env)
Create a file named .env in the project root (same folder as the script) and do not commit it.

Option A – Gmail (App Password)

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=csnacptd0001@gmail.com
EMAIL_PASS=your_16_char_app_password

Notes:

Enable 2‑Step Verification in your Google account.

Create an App Password for “Mail” and use that as EMAIL_PASS.

Subject to Gmail’s daily sending limits (typically ~500/day for personal accounts).[web:95][web:101]

Option B – Brevo SMTP (recommended for larger batches)

SMTP_SERVER=smtp-relay.brevo.com
SMTP_PORT=587
EMAIL_USER=your-brevo-login@smtp-brevo.com
EMAIL_PASS=your_brevo_smtp_key
FROM_EMAIL=csnacptd0001@gmail.com

EMAIL_USER = Brevo SMTP login (shown on the Brevo “SMTP & API” page, not your Gmail).

EMAIL_PASS = full Brevo SMTP key value.

FROM_EMAIL = the sender shown to recipients (your Gmail), which must be verified in Brevo.[web:128][web:132]

Usage
1. Prepare files
Place all notice PDFs in the SEGMENT A NOTICES folder.

Ensure 1701.csv (or your CSV) is in the project root and contains Sr. No. and Email columns.

2. Sending via Brevo (up to 300 emails per run)
Example brevo_300.py usage:

bash
python brevo_300.py

What this script does:

Connects to Brevo SMTP with credentials from .env.

Reads all rows from 1701.csv.

Skips rows:

With invalid/empty Email.

With missing PDF A--<SrNo>.pdf.

With Sr. No. below a configured resume point (e.g. < 215).

Sends up to 300 emails in one run, logging each success.

You can adjust:

CSV path: CSV_PATH = "1701.csv"

Notices folder: ATTACH_DIR = "SEGMENT A NOTICES"

Resume serial: change if sr_no_int < 215: to your desired starting point.

Hard limit per run: change sent >= 300 to another number if your Brevo plan allows more.

3. Sending via Gmail (subject to daily quota)
Example robust_1701send.py usage:

bash
python robust_1701send.py

This script:

Uses Gmail’s SMTP server and App Password from .env.

Validates all email addresses.

Skips rows with invalid email or missing file.

Can be configured to start after a given Sr. No. so you can resume on the next day after hitting Gmail’s daily limit.[web:94][web:95]

Configuration parameters
Typical parameters you might tweak at the top of the script:

python
CSV_PATH = "1701.csv"
ATTACH_DIR = "SEGMENT A NOTICES"
SUBJECT = "Show-Cause Notice"
RESUME_AFTER_SRNO = 214   # start sending from Sr. No. 215
MAX_EMAILS_PER_RUN = 300  # Brevo free plan
FROM_EMAIL = os.getenv("FROM_EMAIL", EMAIL_USER)

Logging & robustness
The scripts log to the console:

[OK] lines for each successful send.

[SKIP] lines for:

Already-sent serial numbers (below RESUME_AFTER_SRNO).

Invalid or empty emails.

Missing PDF files.

Final summary with counts of:

Sent emails.

Skipped invalid emails.

Skipped missing files.

Skipped serials below the resume threshold.

This design lets you safely re-run the script multiple times without re-sending to already processed recipients.

Safety and rate limits
Gmail: Enforces daily sending limits. If you hit an error like
550 5.4.5 Daily user sending limit exceeded, wait for the 24‑hour window to reset or switch to Brevo/another SMTP provider.[web:95][web:96]

Brevo: Enforces plan‑specific daily caps (e.g., 300/day on free tier). The MAX_EMAILS_PER_RUN guard helps keep you within this limit.[web:128]

Always test with 1–2 rows (and small PDFs) before running a full batch.

Customization ideas
Per‑recipient subject/body using extra columns in the CSV.

HTML email body instead of plain text.

Logging to a file (e.g. bulk_send.log) with timestamps.

Simple CLI flags to choose Gmail vs Brevo at runtime.

Disclaimer
This tool is intended for legitimate transactional communication with taxpayers (e.g., PTRC notices).
Ensure you comply with:

Local regulations on electronic communication.

Provider terms of service (Gmail, Brevo, AWS SES, etc.).[web:57][web:72]

License
Add your chosen license here (e.g. MIT, Apache‑2.0), or keep it private if this is an internal project.



