# 📧 Automated Bulk Email Responder (Production Grade)

An enterprise-ready Python solution for stateful, large-scale email distribution. Specifically designed for **GST-PTRC show-cause notices**, this system maps recipient metadata to PDF attachments and manages delivery across Google Workspace quotas.

---

## 🚀 Key Features

*   **Production Architecture:** Object-Oriented Design (OOD) for modularity and maintainability.
*   **State Persistence:** Automatic session recovery using a persistent `send_report.csv` file.
*   **Intelligent Throttling:** Configurable pacing to safely handle Google Workspace's 2,000 emails/day limit.
*   **Audit-Ready Logging:** Real-time feedback loop tracking delivery status, recipient names, and failure reasons.
*   **Reliable File Mapping:** Dynamic resolution of PDF notices based on record serial numbers.

---

## 📂 Project Structure

```text
Bulk_emails/
├── send folder/          # Directory for PDF attachments (e.g., A--31.pdf)
├── send.csv              # Source file with Sr. No., Name, and Email
├── .env                  # Secure SMTP credentials (NOT committed)
├── bulk_sender_pro.py    # Main Production Engine
├── UNDERSTAND.md         # Deep-dive technical architecture guide
├── sync_session.bat      # One-click GitHub synchronization tool
└── README.md
```

---

## 🛠️ Setup & Usage

### 1. Prerequisites
- Python 3.10+
- Google Workspace account (recommended for 2,000/day limit)
- 2-Step Verification enabled + App Password generated.

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
EMAIL_USER=your-email@workspace.com
EMAIL_PASS=your-16-char-app-password
```

### 3. Execution
Ensure your recipients are in `send.csv` and attachments are in `send folder/`, then run:
```bash
python bulk_sender_pro.py
```

---

## 📊 Monitoring & Tracking
The system generates a **`send_report.csv`** file in real-time. Use this to:
- Verify which recipients received the notice.
- Identify and troubleshoot failed deliveries (e.g., invalid email or missing attachment).
- Automatically resume sending from where the last session stopped.

---

## 🤝 Technical Deep Dive
For a detailed explanation of the system's design patterns, rate limiting strategies, and security protocols, refer to [UNDERSTAND.md](./UNDERSTAND.md).

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



