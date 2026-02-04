import streamlit as st
from src.database import init_db
from src.job_application import JobApplicationForm, JobManager
from src.outreach_ui import (
    email_setup_ui, template_manager_ui, 
    send_single_email_ui, send_bulk_email_ui,
    smart_dashboard_ui, import_export_ui
)
from src.contacts_manager import contacts_list_ui, add_contact_ui
from src.analytics import analytics_ui, response_tracking_ui

def main():
    session = init_db()
    
    st.set_page_config(
        page_title="JobTrack Pro",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown('<h1 style="color:#1f77b4;">🚀 JobTrack Pro</h1>', unsafe_allow_html=True)
    st.caption("Track applications • Send outreach • Never miss a follow-up")
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio("Go to", [
        "🎯 Dashboard", 
        "💼 Jobs", 
        "📧 Outreach", 
        "👥 Contacts", 
        "📈 Analytics"
    ])
    
    # Main content
    if page == "🎯 Dashboard":
        smart_dashboard_ui(session)  # Phase 3 smart dashboard
    
    elif page == "💼 Jobs":
        tab1, tab2 = st.tabs(["➕ Add Job", "📋 Manage Jobs"])
        with tab1:
            if "show_add_job" in st.session_state and st.session_state.show_add_job:
                job_form = JobApplicationForm(session)
                job_form.add_job_ui()
                if st.button("← Back to Jobs List"):
                    del st.session_state.show_add_job
                    st.rerun()
            else:
                st.info("Click 'Add Job' in dashboard to get started")
        with tab2:
            job_manager = JobManager(session)
            job_manager.view_update_ui()
    
    elif page == "📧 Outreach":
        outreach_page = st.sidebar.radio("Outreach Tools", [
            "⚙️ Setup", 
            "✉️ Templates", 
            "📨 Send Single", 
            "📤 Bulk Send",
            "📥 Import/Export"
        ], label_visibility="collapsed")
        
        if outreach_page == "⚙️ Setup":
            email_setup_ui(session)
        elif outreach_page == "✉️ Templates":
            template_manager_ui(session)
        elif outreach_page == "📨 Send Single":
            send_single_email_ui(session)
        elif outreach_page == "📤 Bulk Send":
            send_bulk_email_ui(session)
        elif outreach_page == "📥 Import/Export":
            import_export_ui(session)
    
    elif page == "👥 Contacts":
        tab1, tab2 = st.tabs(["➕ Add Contact", "📋 All Contacts"])
        with tab1:
            add_contact_ui(session)
        with tab2:
            contacts_list_ui(session)
    
    elif page == "📈 Analytics":
        tab1, tab2 = st.tabs(["📊 Job Analytics", "📈 Response Tracking"])
        with tab1:
            analytics_ui(session)
        with tab2:
            response_tracking_ui(session)
    
    session.close()

if __name__ == "__main__":
    main()