# 📊 Applying Sets — V1.0

🚀 **From Chaos to Control — Smarter, Sharper, Streamlined**

Welcome to V1.0 of the Job Application Tracker — a major step up from the scrappy V0 that barely held itself together (no offense, past me 😅). Originally cobbled together with trial, error, and a generous amount of AI help, this project has evolved into a structured, usable, and expandable personal assistant for job hunters.

Built with Streamlit, powered by SQLite, and polished through real job search frustration, this version is cleaner, faster, and more customizable — your digital command center for job hunting.

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

## 🔧 Features

✅ **Add New Job Applications**
Store company names, job titles, application dates, and recruiter contacts — no more Excel sheets from hell.

✅ **Update & Track Application Status**
Change statuses from "Applied" to "Interviewed", "Offered", or (let’s be real) "Ghosted".

✅ **Follow-up and Interview Dates**
Set key dates and prepare like a pro (or panic responsibly).

✅ **Priority System**
Label apps as High, Medium, or Low priority so you focus on the juicy ones.

✅ **Analytics Dashboard**
See where you're winning, where you're wasting time, and how many HRs are ghosting you. 🎯

## 🧠 Under the Hood

V0 was a working prototype. V1 is a structured, modular product. Here's what changed:

- **Frontend**: Built with Streamlit for fast, reactive UI.
- **Backend Logic**: Modularized Python functions for DB operations.
- **Database**: SQLite for storage, with future options to plug into PostgreSQL or Supabase.
- **Data Processing**: Powered by Pandas for analytics and visualization prep.
- **State Management**: Session-based logic for smoother UX.

## 💼 Why I Built This

Let’s be honest — job hunting sucks. It's stressful, chaotic, and incredibly easy to lose track of everything. I built this project:

- To organize my own job search across 40+ companies.
- To learn how to structure an app using Streamlit + SQLite.
- To explore how AI (like ChatGPT) could help me go from idea → MVP faster.
- And now, to help others who are in the same boat.

## 📷 Screenshots (V1)
<!-- ## 📷 Screenshots & Demo (V1)

| **Dashboard** | **Add Application** | **Analytics** |
|---------------|---------------------|---------------|
| ![Dashboard](path-to-local-dashboard-image) | ![Add Application](path-to-local-add-application-image) | ![Analytics](path-to-local-analytics-image) |

### 🎥 Screencast Demo

To view the screencast demo, locate the video file on your local system. Ensure it is accessible for playback or consider uploading it to a platform like YouTube for easier sharing. -->

## 🛠 Installation & Running the App

1. **Clone this repo**:
    ```bash
    git clone https://github.com/your-repo/job-tracker.git
    cd job-tracker
    ```

2. **Install requirements**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Run it**:
    ```bash
    streamlit run app.py
    ```

## 🌱 Future Improvements

- 📧 Email Reminders for follow-ups
- 📅 Google Calendar Integration
- 📈 More Advanced Data Visualization
- 🤖 AI-Powered Resume/Application Scoring

## 🤝 Contribute

Got feedback, want a feature, or just tired of being ghosted?
Open an issue, drop a PR, or send me a message.

## 📜 License

Open-source under the MIT License. Use it. Fork it. Brag about it in interviews.

## 🧠 Built With

- **Streamlit**
- **SQLite**
- **Pandas**
- **ChatGPT ,Copilot & Mistral Ai ** (massive help, not gonna lie)