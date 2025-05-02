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
    def __init__(self, conn):
        self.conn = conn

    def add_job_ui(self):
        st.markdown("### ➕ Add New Job Application")  # noqa: RUF001
        st.info("Fill the form below to track your job application. You got this! 🚀")
        st.markdown("---")
        with st.form("job_form"):
            col1, col2 = st.columns(2)
            with col1:
                date_applied = st.date_input(
                    "📅 Date Applied",
                    datetime.now(tz=timezone.utc),
                    help="Select the date you applied for the job.",
                )
                company_name = st.text_input(
                    "🏢 Company Name",
                    placeholder="Eg. Google, Amazon...",
                    help="Enter the name of the company.",
                )
                job_title = st.text_input(
                    "💼 Job Title",
                    placeholder="Eg. Data Analyst, Backend Developer...",
                    help="Enter the job title.",
                )
                location = st.text_input(
                    "📍 Location",
                    placeholder="Eg. Remote, Bangalore",
                    help="Enter the location of the job.",
                )
                job_link = st.text_input(
                    "🔗 Job Posting Link",
                    placeholder="Paste URL",
                    help="Enter the URL of the job posting.",
                )
                priority = st.selectbox(
                    "⚡ Priority",
                    ["High", "Medium", "Low"],
                    help="Select the priority of this application.",
                )

            with col2:
                status = st.selectbox(
                    "📌 Application Status",
                    [
                        "Applied",
                        "Interview Scheduled",
                        "Offer Received",
                        "Rejected",
                        "Ghosted",
                    ],
                    help="Select the current status of the application.",
                )
                follow_up_date = st.date_input(
                    "📬 Follow-up Date",
                    datetime.now(tz=timezone.utc) + timedelta(days=7),
                    help="Select the follow-up date for this application.",
                )
                interview_date = st.date_input(
                    "🎤 Interview Date",
                    None,
                    help="Select the interview date if scheduled.",
                )
                recruiter_contact = st.text_input(
                    "👤 Recruiter Contact",
                    help="Enter the contact information of the recruiter.",
                )
                networking_contact = st.text_input(
                    "🧠 Networking Contact",
                    help="Enter the contact information of any networking contacts.",
                )
                notes = st.text_area(
                    "📝 Notes",
                    placeholder="Any additional notes...",
                    help="Enter any additional notes about the application.",
                )

            submit_button = st.form_submit_button("💾 Save Application")

            if submit_button:
                if not company_name or not job_title:
                    st.error("Company Name and Job Title are required fields.")
                else:
                    job_data = {
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
                    add_job_application(self.conn, job_data)
                    st.success(f"✅ Application for *{job_title}* at *{company_name}* saved!")
                    st.balloons()


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


# class JobManager:
#     def __init__(self, conn):
#         self.conn = conn

#     def view_update_ui(self):
#         st.markdown("## 📋 View, Filter & Manage Job Applications")

#         jobs = fetch_all_jobs(self.conn)

#         if jobs.empty:
#             st.warning("No applications found. Start adding now!")
#             return

#         # --- Filters ---
#         with st.expander("🔎 Filter & Search"):
#             col1, col2, col3 = st.columns(3)
#             with col1:
#                 search_text = st.text_input("🔍 Search Company or Title", "")
#             with col2:
#                 status_filter = st.selectbox(
#                     "📌 Filter by Status",
#                     [
#                         "All",
#                         "Applied",
#                         "Interview Scheduled",
#                         "Offer Received",
#                         "Rejected",
#                         "Ghosted",
#                     ],
#                 )
#             with col3:
#                 date_filter = st.date_input(
#                     "📅 Applications Since",
#                     datetime.now(tz=timezone.utc) - timedelta(days=30),
#                 )

#         # --- Apply Filters ---
#         filtered_jobs = jobs[
#             (jobs["company_name"].str.contains(search_text, case=False) | jobs["job_title"].str.contains(search_text, case=False))
#             & (jobs["status"] == status_filter if status_filter != "All" else True)
#             & (pd.to_datetime(jobs["date_applied"]).dt.date >= date_filter)
#         ]

#         # --- Display Jobs using reusable component ---
#         jobs_per_page = 3
#         total_jobs = len(filtered_jobs)
#         total_pages = (total_jobs + jobs_per_page - 1) // jobs_per_page

#         st.markdown("### 📄 Job Applications")
#         with st.expander("💡 Jobs Cards", expanded=True):
#             # --- Pagination Controls ---
#             if "page" not in st.session_state:
#                 st.session_state.page = 1

#             col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
#             with col1:
#                 if st.button("⬅️ Previous") and st.session_state.page > 1:
#                     st.session_state.page -= 1
#             with col4:
#                 if st.button("Next ➡️") and st.session_state.page < total_pages:
#                     st.session_state.page += 1

#             page = st.session_state.page
#             start_idx = (page - 1) * jobs_per_page
#             end_idx = start_idx + jobs_per_page

#             current_jobs = filtered_jobs.iloc[start_idx:end_idx]

#             for _, job in current_jobs.iterrows():
#                 job_card = JobCard(job)
#                 job_card.render()
#             st.caption(f"Page {page} of {total_pages} | Showing {start_idx + 1}-{min(end_idx, total_jobs)} of {total_jobs} jobs.")

#         # --- Update/Delete Section ---
#         st.subheader("✏️ Update or Delete Application")
#         st.dataframe(jobs)
#         application_id = st.number_input("Enter Application ID to Update/Delete", min_value=1)

#         if st.button("Load Application"):
#             application = jobs[jobs["id"] == application_id]
#             if not application.empty:
#                 st.write(application)
#                 with st.form("update_form"):
#                     new_status = st.selectbox(
#                         "Update Status",
#                         [
#                             "Applied",
#                             "Interview Scheduled",
#                             "Offer Received",
#                             "Rejected",
#                             "Ghosted",
#                         ],
#                         index=[
#                             "Applied",
#                             "Interview Scheduled",
#                             "Offer Received",
#                             "Rejected",
#                             "Ghosted",
#                         ].index(application["status"].to_numpy[0]),
#                     )
#                     new_follow_up_date = st.date_input(
#                         "Update Follow-up Date",
#                         pd.to_datetime(application["follow_up_date"].to_numpy[0]),
#                     )

#                     interview_date_val = application["interview_date"].to_numpy[0]
#                     new_interview_date = st.date_input(
#                         "Update Interview Date",
#                         (pd.to_datetime(interview_date_val) if pd.notna(interview_date_val) else datetime.now(tz=timezone.utc)),
#                     )
#                     new_notes = st.text_area("Update Notes", application["notes"].to_numpy[0])

#                     update_button = st.form_submit_button("Update Application")
#                     delete_button = st.form_submit_button("Delete Application")

#                     if update_button:
#                         updated_data = {
#                             "status": new_status,
#                             "follow_up_date": new_follow_up_date,
#                             "interview_date": new_interview_date,
#                             "notes": new_notes,
#                         }
#                         update_job_application(self.conn, application_id, updated_data)
#                         st.success(f"✅ Application {application_id} updated!")

#                     if delete_button:
#                         delete_job_application(self.conn, application_id)
#                         st.success(f"🗑️ Application {application_id} deleted!")


class JobManager:
    def __init__(self, conn):
        self.conn = conn

    def view_update_ui(self):
        st.markdown("## 📋 View, Filter & Manage Job Applications")
        jobs = fetch_all_jobs(self.conn)

        if jobs.empty:
            st.warning("No applications found. Start adding now!")
            return

        filtered_jobs = self._filter_jobs_ui(jobs)
        self._display_jobs_ui(filtered_jobs)
        self._update_delete_ui(jobs)

    # ----------------------------- FILTERING -----------------------------

    def _filter_jobs_ui(self, jobs):
        with st.expander("🔎 Filter & Search"):
            col1, col2, col3 = st.columns(3)
            with col1:
                search_text = st.text_input("🔍 Search Company or Title", "")
            with col2:
                status_filter = st.selectbox(
                    "📌 Filter by Status",
                    ["All", "Applied", "Interview Scheduled", "Offer Received", "Rejected", "Ghosted"],
                )
            with col3:
                date_filter = st.date_input(
                    "📅 Applications Since",
                    datetime.now(tz=timezone.utc) - timedelta(days=30),
                )

        return jobs[
            (jobs["company_name"].str.contains(search_text, case=False) | jobs["job_title"].str.contains(search_text, case=False))
            & ((jobs["status"] == status_filter) if status_filter != "All" else True)
            & (pd.to_datetime(jobs["date_applied"]).dt.date >= date_filter)
        ]

    # ----------------------------- JOB DISPLAY -----------------------------

    def _display_jobs_ui(self, filtered_jobs):
        st.markdown("### 📄 Job Applications")

        with st.expander("💡 Jobs Cards", expanded=True):
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

    # ----------------------------- UPDATE / DELETE -----------------------------

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
            current_status = application["status"].to_numpy[0]
            current_follow_up = pd.to_datetime(application["follow_up_date"].to_numpy[0])
            interview_date_val = application["interview_date"].to_numpy[0]
            current_notes = application["notes"].to_numpy[0]

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

            update_button = st.form_submit_button("Update Application")
            delete_button = st.form_submit_button("Delete Application")

            if update_button:
                updated_data = {
                    "status": new_status,
                    "follow_up_date": new_follow_up_date,
                    "interview_date": new_interview_date,
                    "notes": new_notes,
                }
                update_job_application(self.conn, application_id, updated_data)
                st.success(f"✅ Application {application_id} updated!")

            if delete_button:
                delete_job_application(self.conn, application_id)
                st.success(f"🗑️ Application {application_id} deleted!")
                st.balloons()
