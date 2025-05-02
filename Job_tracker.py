import streamlit as st
from database import init_db
from job_application import JobApplicationForm,  JobManager 
from analytics import analytics_ui

def main():
    conn = init_db()

    st.title("📊 Job Application Tracker")
    menu = ["Add Job Application", "View & Update Applications", "Analytics Dashboard"]
    choice = st.sidebar.selectbox("Select Option", menu)

    if choice == "Add Job Application":
        job_form = JobApplicationForm(conn)
        job_form.add_job_ui()
    elif choice == "View & Update Applications":
        job_manager = JobManager(conn)
        job_manager.view_update_ui()
    elif choice == "Analytics Dashboard":
        analytics_ui(conn)


if __name__ == "__main__":
    # local_css()
    main()