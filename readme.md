# 📊 Applying Sets — V2.0

🚀 **Outreach. Engage. Track. Win. — Your Job Hunt Command Center**

Welcome to V2.0 — the evolution is real. While V1 got you organized, V2.0 makes you *proactive*. We've added secure credential management, email outreach automation, recruiter relationship tracking, and an intelligent contact manager. This isn't just about tracking applications anymore — it's about building relationships and automating your follow-ups so you can focus on what matters: landing the job.

Built with Streamlit, powered by SQLite, secured with Fernet encryption, and supercharged with email automation, V2.0 transforms your job search from reactive to strategic.

## 🆚 What’s New Since V0?
   **Feature**                | **V0 (Prototype)**                      | **V1 (This Version)**                                      |
 |-----------------------------|-----------------------------------------|------------------------------------------------------------|
 | **UI Design**               | Basic Streamlit forms                   | Modular layout with sections and consistent UX             |
 | **Data Storage**            | SQLite (no validation or schema checks) | SQLite with structured tables, better data handling       |
 | **Application Update Flow** | Manual edits only                       | Editable dropdowns, status updates, smarter UI             |
 | **Analytics**               | Minimal, text-based                     | Pandas-powered stats with visual summaries                |
 | **Priority Tagging**        | Basic string input                      | Visual markers, filters coming soon                        |
 | **Architecture**            | Spaghetti code                          | Modularized Python functions, cleaner flow                 |
 | **Vision**                  | Just tracking                           | Tracking + strategy dashboard for smarter applications     |

## 🔧 Core Features

✅ **Track Job Applications Like a Pro**
Store company names, job titles, dates, salaries, and recruiter contacts — no Excel hell allowed.

✅ **Recruiter & Contact Manager**
Build and maintain relationships. Track interactions, notes, and communication history with every recruiter.

✅ **Secure Credential Storage**
Save email credentials with Fernet encryption. Never hardcode passwords again.

✅ **Email Outreach Engine**
Send templated follow-ups, reminders, and inquiries directly from the app. Stay persistent without being creepy.

✅ **Smart Status Tracking**
Move applications from "Applied" → "Interviewed" → "Offered" (or "Ghosted" — we all feel it).

✅ **Priority & Filter System**
Mark opportunities as High/Medium/Low. Filter by company, status, or date to focus on what matters.

✅ **Analytics Dashboard**
Real metrics: response rates, average interview time-to-hire, ghosting stats, and outreach performance.

✅ **Follow-up Scheduling**
Set reminders, track key dates, and never miss a deadline again.

## 🧠 Under the Hood — Architecture

V2.0 introduces a proper layered architecture:

- **Presentation Layer**: Streamlit UI with smart routing and context awareness
- **Business Logic**: Modularized functions for applications, contacts, analytics, and outreach
- **Security Layer**: Encrypted credential vault + password-protected master access
- **Data Layer**: SQLite with structured schemas and validation
- **Integration Layer**: Email engine with SMTP support and template system

**Key Components:**
- `database.py` — SQL operations & schema management
- `security.py` — Credential encryption & master password validation
- `email_engine.py` — SMTP integration & outreach automation
- `contacts_manager.py` — Recruiter database & relationship tracking
- `analytics.py` — Pandas-powered insights & metrics
- `job_application.py` — Core app logic
- `outreach_ui.py` — Email & follow-up interface
- `model.py` — Data models & validation

## 💼 Why V2.0?

Job hunting at scale is brutal. With 100+ applications flying out, it's impossible to:
- Remember who you talked to
- Stay consistent with follow-ups
- Keep passwords safe
- Spot patterns in your outreach success

V2.0 solves this. It's the difference between *hoping* for callbacks and *earning* them through smart, persistent, organized outreach.

## � Installation & Running

1. **Clone & Navigate**:
    ```bash
    git clone https://github.com/your-repo/applying-sets.git
    cd applying-sets
    ```

2. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set Master Password** (recommended):
    ```bash
    set MASTER_PASSWORD=your_secure_password
    ```

4. **Run the App**:
    ```bash
    streamlit run Job_tracker.py
    ```

## 🔐 Security & Privacy

- Credentials stored with **Fernet symmetric encryption**
- Master password protection for sensitive data
- Salt-based key derivation (PBKDF2-SHA256)
- No plaintext passwords in files or memory
- File permissions set to 0o600 for encrypted files

## 🌱 Roadmap — V2.1 & Beyond

- 📅 Google Calendar Integration for interview prep
- 🔔 SMS reminders for critical follow-ups
- 🤖 AI-powered response scoring & suggestions
- 📊 LinkedIn auto-import for applications
- 🌐 Cloud sync (AWS S3 or similar)
- 📱 Mobile companion app
- 🎯 ML-based job matching & recommendations

## 🤝 Contribute

Found a bug? Want a feature? Have outreach templates to share?
Open an issue, submit a PR, or send feedback. This project thrives on real job searchers using it and demanding improvements.

## 📜 License

MIT License. Use it. Improve it. Get hired with it. 🎉

## 🧠 Built With

- **Streamlit** — Interactive UI
- **SQLite** — Reliable local storage
- **Pandas** — Analytics & data processing
- **Cryptography (Fernet)** — Secure encryption
- **ChatGPT, GitHub Copilot & Mistral AI** — Accelerated development
- **Python 3.9+** — Core language