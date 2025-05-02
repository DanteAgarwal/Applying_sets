import re
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st
from src.database import (
    add_job_application,
    delete_job_application,
    fetch_all_jobs,
    update_job_application,
)


class JobApplicationForm:
    def __init__(self, session):
        self.session = session

    def add_job_ui(self):
        st.markdown("### ➕ Add New Job Application")  # noqa: RUF001
        st.info("Fill the form below to track your job application. You got this! 🚀")
        st.markdown("---")
        with st.form("job_form"):
            col1, col2 = st.columns(2)
            with col1:
                date_applied = self._get_date_input("📅 Date Applied", datetime.now(tz=timezone.utc))
                company_name = st.text_input("🏢 Company Name", placeholder="Eg. Google, Amazon...")
                job_title = st.text_input("💼 Job Title", placeholder="Eg. Data Analyst, Backend Developer...")
                location = st.text_input("📍 Location", placeholder="Eg. Remote, Bangalore")
                job_link = st.text_input("🔗 Job Posting Link", placeholder="Paste URL")
                priority = st.selectbox("⚡ Priority", ["High", "Medium", "Low"])

            with col2:
                status = st.selectbox(
                    "📌 Application Status",
                    ["Applied", "Interview Scheduled", "Offer Received", "Rejected", "Ghosted"],
                )
                follow_up_date = self._get_date_input("📬 Follow-up Date", datetime.now(tz=timezone.utc) + timedelta(days=7))
                interview_date = self._get_date_input("🎤 Interview Date", None)
                recruiter_contact = st.text_input("👤 Recruiter Contact")
                networking_contact = st.text_input("🧠 Networking Contact")
                notes = st.text_area("📝 Notes", placeholder="Any additional notes...")

            if st.form_submit_button("💾 Save Application"):
                self._handle_form_submission(
                    date_applied,
                    company_name,
                    job_title,
                    location,
                    job_link,
                    status,
                    follow_up_date,
                    interview_date,
                    recruiter_contact,
                    networking_contact,
                    notes,
                    priority,
                )

    def _get_date_input(self, label, default_value):
        return st.date_input(label, default_value)

    def _handle_form_submission(
        self,
        date_applied,
        company_name,
        job_title,
        location,
        job_link,
        status,
        follow_up_date,
        interview_date,
        recruiter_contact,
        networking_contact,
        notes,
        priority,
    ):
        errors = self._validate_form_input(date_applied, company_name, job_title, job_link, follow_up_date, interview_date)
        if errors:
            for error in errors:
                st.error(error)
        else:
            job_data = self._create_job_data(
                date_applied,
                company_name,
                job_title,
                location,
                job_link,
                status,
                follow_up_date,
                interview_date,
                recruiter_contact,
                networking_contact,
                notes,
                priority,
            )
            add_job_application(self.session, job_data)
            st.success(f"✅ Application for *{job_title}* at *{company_name}* saved!")
            st.balloons()

    def _validate_form_input(self, date_applied, company_name, job_title, job_link, follow_up_date, interview_date):
        errors = []
        if not company_name:
            errors.append("Company Name is required.")
        if not job_title:
            errors.append("Job Title is required.")
        if job_link and not self.is_valid_url(job_link):
            errors.append("Job Link is not a valid URL.")
        if date_applied > datetime.now(tz=timezone.utc).date():
            errors.append("Date Applied cannot be in the future.")
        if follow_up_date < date_applied:
            errors.append("Follow-up Date cannot be before Date Applied.")
        if interview_date and interview_date < date_applied:
            errors.append("Interview Date cannot be before Date Applied.")
        if job_link and not self.is_job_link_unique(job_link):
            errors.append("Job Link must be unique.")
        return errors

    def _create_job_data(
        self,
        date_applied,
        company_name,
        job_title,
        location,
        job_link,
        status,
        follow_up_date,
        interview_date,
        recruiter_contact,
        networking_contact,
        notes,
        priority,
    ):
        return {
            "date_applied": date_applied,
            "company_name": company_name,
            "job_title": job_title,
            "location": location,
            "job_link": job_link,
            "status": status,
            "follow_up_date": follow_up_date,
            "interview_date": interview_date,
            "recruiter_contact": recruiter_contact,
            "networking_contact": networking_contact,
            "notes": notes,
            "priority": priority,
        }

    def is_valid_url(self, url):
        url_pattern = re.compile(
            r"^(https?|ftp):\/\/"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
            r"\[?[A-F0-9]*:[A-F0-9:]+\]?)?"
            r"(?::\d+)?"
            r"(?:\/[^\s]*)?$",
            re.IGNORECASE,
        )
        return re.match(url_pattern, url) is not None

    def is_job_link_unique(self, job_link):
        jobs = fetch_all_jobs(self.session)
        return jobs[jobs["job_link"] == job_link].empty


class JobCard:
    def __init__(self, job):
        self.job = job

    def render(self):
        st.markdown(
            f"""
            <div class="job-card" style="padding:10px; margin-bottom:10px;
            border-radius:10px; border:1px solid #dee2e6; background-color:white;">
                <h4 style="margin-bottom:5px;">{self.job.iloc[3]} @ {self.job.iloc[2]}</h4>
                <div>
                    <span class="tag-badge {self.job.iloc[6].split()[0]}">{self.job.iloc[6]}</span>
                    <span style="color: #495057;">📅 {self.job.iloc[1]}</span> |
                    <a href="{self.job.iloc[5]}" target="_blank">🔗 Job Link</a>
                </div>
                <div style="margin-top:5px; color:#495057;">{self.job.iloc[11]}</div>
            </div>
        """,
            unsafe_allow_html=True,
        )


class JobManager:
    def __init__(self, session):
        self.session = session

    def view_update_ui(self):
        st.markdown("## 📋 View, Filter & Manage Job Applications")
        jobs = fetch_all_jobs(self.session)

        if jobs.empty:
            st.warning("No applications found. Start adding now!")
            return

        filtered_jobs = self._filter_jobs_ui(jobs)
        self._display_jobs_ui(filtered_jobs)
        self._update_delete_ui(jobs)

    def _filter_jobs_ui(self, jobs):
        with st.expander("🔎 Filter & Search"):
            search_text = st.text_input("🔍 Search Company or Title", "")
            status_filter = st.selectbox(
                "📌 Filter by Status", ["All", "Applied", "Interview Scheduled", "Offer Received", "Rejected", "Ghosted"]
            )
            date_filter = st.date_input("📅 Applications Since", datetime.now(tz=timezone.utc) - timedelta(days=30))

        return jobs[
            (jobs["company_name"].str.contains(search_text, case=False) | jobs["job_title"].str.contains(search_text, case=False))
            & ((jobs["status"] == status_filter) if status_filter != "All" else True)
            & (pd.to_datetime(jobs["date_applied"]).dt.date >= date_filter)
        ]

    def _display_jobs_ui(self, filtered_jobs):
        st.markdown("### 📄 Job Applications")

        with st.expander("💡 Jobs Cards", expanded=True):
            self._paginate_jobs(filtered_jobs)

    def _paginate_jobs(self, filtered_jobs):
        jobs_per_page = 3
        total_jobs = len(filtered_jobs)
        total_pages = (total_jobs + jobs_per_page - 1) // jobs_per_page

        if "page" not in st.session_state:
            st.session_state.page = 1

        col1, _, _, col4 = st.columns([1, 1, 2, 1])
        with col1:
            if st.button("⬅️ Previous") and st.session_state.page > 1:
                st.session_state.page -= 1
        with col4:
            if st.button("Next ➡️") and st.session_state.page < total_pages:
                st.session_state.page += 1

        page = st.session_state.page
        start_idx = (page - 1) * jobs_per_page
        end_idx = start_idx + jobs_per_page
        current_jobs = filtered_jobs.iloc[start_idx:end_idx]

        for _, job in current_jobs.iterrows():
            job_card = JobCard(job)
            job_card.render()

        st.caption(f"Page {page} of {total_pages} | Showing {start_idx + 1}-{min(end_idx, total_jobs)} of {total_jobs} jobs.")

    def _update_delete_ui(self, jobs):
        st.subheader("✏️ Update or Delete Application")
        st.dataframe(jobs)

        application_id = st.number_input("Enter Application ID to Update/Delete", min_value=1)

        if st.button("Load Application"):
            application = jobs[jobs["id"] == application_id]
            if not application.empty:
                st.write(application)
                self._render_update_delete_form(application, application_id)

    def _render_update_delete_form(self, application, application_id):
        with st.form("update_form"):
            current_status = application["status"].to_numpy()[0]
            current_follow_up = pd.to_datetime(application["follow_up_date"].to_numpy()[0])
            interview_date_val = application["interview_date"].to_numpy()[0]
            current_notes = application["notes"].to_numpy()[0]

            new_status = st.selectbox(
                "Update Status",
                ["Applied", "Interview Scheduled", "Offer Received", "Rejected", "Ghosted"],
                index=["Applied", "Interview Scheduled", "Offer Received", "Rejected", "Ghosted"].index(current_status),
            )
            new_follow_up_date = st.date_input("Update Follow-up Date", current_follow_up)
            new_interview_date = st.date_input(
                "Update Interview Date",
                pd.to_datetime(interview_date_val) if pd.notna(interview_date_val) else datetime.now(tz=timezone.utc),
            )
            new_notes = st.text_area("Update Notes", current_notes)

            if st.form_submit_button("Update Application"):
                self._update_application(application_id, new_status, new_follow_up_date, new_interview_date, new_notes)

            if st.form_submit_button("Delete Application"):
                self._delete_application(application_id)

    def _update_application(self, application_id, new_status, new_follow_up_date, new_interview_date, new_notes):
        updated_data = {
            "status": new_status,
            "follow_up_date": new_follow_up_date,
            "interview_date": new_interview_date,
            "notes": new_notes,
        }
        update_job_application(self.session, application_id, updated_data)
        st.success(f"✅ Application {application_id} updated!")

    def _delete_application(self, application_id):
        delete_job_application(self.session, application_id)
        st.success(f"🗑️ Application {application_id} deleted!")
        st.balloons()
