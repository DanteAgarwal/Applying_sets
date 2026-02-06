import streamlit as st
from src.database import init_db, fetch_all_jobs, fetch_all_contacts, add_job_application
from src.job_application import JobApplicationForm, JobManager
from src.outreach_ui import (
    email_setup_ui, 
    send_bulk_email_ui,
    import_export_ui
)
from src.contacts_manager import contacts_list_ui, add_contact_ui
from src.analytics import analytics_ui, response_tracking_ui
from src.email_engine import EmailEngine, get_active_email_account
from src.database import get_all_templates, get_followup_candidates
from datetime import datetime, timedelta, timezone
import pandas as pd
import time

# =====================================================
# SMART NAVIGATION SYSTEM (SINGLE SOURCE OF TRUTH)
# =====================================================

def initialize_app_state():
    """Initialize all session state variables with smart defaults"""
    if "page" not in st.session_state:
        st.session_state.page = "DASHBOARD"
    
    # Clear any stale quick actions
    if "quick_action" in st.session_state and st.session_state.quick_action:
        action = st.session_state.quick_action
        st.session_state.quick_action = None
        
        # Map quick actions to pages
        action_map = {
            "ADD_JOB": "JOBS",
            "ADD_CONTACT": "CONTACTS", 
            "SEND_MAIL": "OUTREACH",
            "FOLLOW_UP": "DASHBOARD"
        }
        
        if action in action_map:
            st.session_state.page = action_map[action]
            st.rerun()

def get_system_status(session):
    """Intelligent system health check"""
    status = {
        "email_configured": False,
        "has_contacts": False,
        "has_templates": False,
        "has_jobs": False,
        "needs_followup": 0
    }
    
    try:
        account = get_active_email_account(session)
        status["email_configured"] = account is not None
        
        contacts = fetch_all_contacts(session)
        status["has_contacts"] = len(contacts) > 0
        
        templates = get_all_templates(session)
        status["has_templates"] = len(templates) > 0
        
        jobs = fetch_all_jobs(session)
        status["has_jobs"] = len(jobs) > 0
        
        if status["has_contacts"]:
            engine = EmailEngine(session)
            candidates = engine.get_followup_candidates(days_threshold=7)
            status["needs_followup"] = len(candidates)
    except Exception as e:
        st.error(f"System check error: {str(e)}")
    
    return status

# =====================================================
# MILITARY-GRADE STYLING (PRESERVED & OPTIMIZED)
# =====================================================

def apply_military_grade_styles():
    """Ultra-minimalist metallic dark theme - maximum contrast, minimum clutter"""
    st.markdown("""
        <style>
        :root {
            --bg-main: #0b0f14;
            --bg-surface: #121822;
            --bg-card: #171f2a;
            --text-main: #d6d6dc;
            --text-secondary: #9aa3ad;
            --text-muted: #6b7280;
            --accent-gold: #d4af37;
            --accent-steel: #8faadc;
            --accent-jade: #5fd1b6;
            --danger: #d16d6d;
            --success: #6fcf97;
            --warning: #e0b15c;
        }
        
        .stApp {
            background: linear-gradient(180deg, var(--bg-main) 0%, var(--bg-surface) 50%, var(--bg-main) 100%);
            color: var(--text-main);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        .military-header {
            background: linear-gradient(90deg, var(--accent-gold), #ffffff, var(--accent-gold));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            margin: 0;
            padding: 1rem 0;
            border-bottom: 1px solid rgba(192, 192, 192, 0.2);
        }
        
        [data-testid="stMetricValue"] {
            color: var(--accent-gold) !important;
        }
        
        [data-testid="stSidebar"] {
            background: rgba(10, 10, 15, 0.95);
            backdrop-filter: blur(12px);
            border-right: 1px solid rgba(192, 192, 192, 0.1);
        }
        
        [data-testid="stSidebar"] .stRadio label {
            background: transparent;
            border: 1px solid transparent;
            border-radius: 10px;
            padding: 0.8rem 1rem;
            margin: 0.2rem 0;
            color: var(--text-secondary);
            font-weight: 600;
            transition: all 0.2s ease;
        }
        
        [data-testid="stSidebar"] .stRadio label:hover {
            background: rgba(192, 192, 192, 0.05);
            border-color: rgba(192, 192, 192, 0.2);
            color: var(--text-main);
            transform: translateX(3px);
        }
        
        [data-testid="stSidebar"] .stRadio label[aria-checked="true"] {
            background: rgba(108, 92, 231, 0.15);
            border-left: 3px solid var(--accent-gold);
            color: #ffffff;
        }
        
        .main .block-container {
            padding: 1.5rem 2rem;
            max-width: 1400px;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #1b2430, #131a22);
            color: var(--text-main);
            border: 1px solid rgba(212,175,55,.25);
            height: 38px;
            border-radius: 8px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.78rem;
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            border-color: var(--accent-gold);
            color: var(--accent-gold);
            background: linear-gradient(135deg, #2a2f3a, #1f2530);
            transform: translateY(-1px);
        }
        
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #c0c0c0 0%, #a0a0a0 100%);
            color: #0a0a0f;
            border: none;
            font-weight: 700;
        }
        
        [data-testid="stMetric"] {
            background: rgba(30, 35, 45, 0.6);
            border: 1px solid rgba(192, 192, 192, 0.1);
            border-radius: 10px;
            padding: 1.2rem 0.8rem;
        }
        
        [data-testid="stMetricLabel"] {
            color: #8a8a95 !important;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            font-size: 0.7rem !important;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            border-bottom: 1px solid rgba(192, 192, 192, 0.1);
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 8px 8px 0 0;
            padding: 0.7rem 1.4rem;
            color: var(--text-muted);
            border-bottom: 2px solid transparent;
        }
        
        .stTabs [aria-selected="true"] {
            color: #ffffff !important;
            border-bottom-color: var(--accent-gold);
            background: rgba(108, 92, 231, 0.1);
        }
        
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select {
            background: rgba(15, 20, 30, 0.7);
            border: 1px solid rgba(192, 192, 192, 0.12);
            border-radius: 8px;
            color: var(--text-main);
            padding: 0.75rem 1rem;
            font-size: 0.9rem;
        }
        
        #MainMenu, footer, header { visibility: hidden !important; }
        
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: rgba(10, 10, 15, 0.5); }
        ::-webkit-scrollbar-thumb { background: rgba(192, 192, 192, 0.25); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(192, 192, 192, 0.4); }
        
        /* Smart status badges */
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.7rem;
            border-radius: 16px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .status-ready { background: rgba(111,207,151,.2); color: var(--success); }
        .status-warning { background: rgba(224,177,92,.15); color: var(--warning); }
        .status-critical { background: rgba(209,109,109,.15); color: var(--danger); }
        
        /* Compact job rows */
        .action-row {
            display: flex;
            align-items: center;
            padding: 0.8rem 1rem;
            background: var(--bg-card);
            border-radius: 8px;
            margin-bottom: 0.6rem;
            transition: transform 0.2s ease;
        }
        .action-row:hover {
            transform: translateX(3px);
            border-left: 3px solid var(--accent-gold);
        }
        </style>
    """, unsafe_allow_html=True)

# =====================================================
# INTELLIGENT DASHBOARD (SELF-CONTAINED)
# =====================================================

def render_intelligent_dashboard(session):
    """Self-contained intelligent dashboard with prioritized actions"""
    status = get_system_status(session)
    
    # System readiness alerts
    alert_cols = st.columns(3)
    if not status["email_configured"]:
        with alert_cols[0]:
            st.warning("📧 Email not configured • Go to OUTREACH > SETUP")
    if not status["has_contacts"] and status["has_jobs"]:
        with alert_cols[1]:
            st.info("👤 No contacts • Link recruiters to jobs for follow-ups")
    if status["needs_followup"] > 0:
        with alert_cols[2]:
            st.error(f"⏰ {status['needs_followup']} follow-ups due • ACT NOW")
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # Metrics row
    jobs_df = fetch_all_jobs(session)
    contacts_df = fetch_all_contacts(session)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("TOTAL JOBS", len(jobs_df))
    with col2:
        active = len(jobs_df[jobs_df['status'].isin(['Applied', 'Interview Scheduled'])]) if not jobs_df.empty else 0
        st.metric("ACTIVE", active)
    with col3:
        interviews = len(jobs_df[jobs_df['status'] == 'Interview Scheduled']) if not jobs_df.empty else 0
        st.metric("INTERVIEWS", interviews)
    with col4:
        offers = len(jobs_df[jobs_df['status'] == 'Offer Received']) if not jobs_df.empty else 0
        st.metric("OFFERS", offers)
    
    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)
    
    # Smart quick actions - context-aware
    st.subheader("⚡ QUICK ACTIONS")
    cols = st.columns(4, gap="medium")
    
    actions = [
        ("➕ ADD JOB", "ADD_JOB", True),
        ("👤 ADD CONTACT", "ADD_CONTACT", True),
        ("📧 SEND EMAIL", "SEND_MAIL", status["email_configured"] and status["has_contacts"] and status["has_templates"]),
        ("🔄 FOLLOW-UPS", "FOLLOW_UP", status["needs_followup"] > 0)
    ]
    
    for idx, (label, action, enabled) in enumerate(actions):
        with cols[idx]:
            if st.button(label, key=f"qa_{action}", use_container_width=True, disabled=not enabled):
                st.session_state.quick_action = action
                st.rerun()
    
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # Priority actions section
    st.subheader("🎯 ACTION REQUIRED")
    
    # Get actionable items directly (no external dependency)
    engine = EmailEngine(session)
    try:
        items = engine.get_actionable_items()
    except AttributeError:
        # Fallback if get_actionable_items doesn't exist yet
        items = {
            "due_today": [],
            "recent_replies": [],
            "stale": []
        }
    
    # Show follow-ups due today
    if items.get("due_today"):
        st.error(f"⏰ {len(items['due_today'])} FOLLOW-UPS DUE TODAY")
        for idx, contact in enumerate(items["due_today"][:5]):
            job = session.query(Contact).get(contact.id).job if hasattr(contact, 'job') else None
            
            cols = st.columns([4, 2, 2, 1])
            with cols[0]:
                st.write(f"**{contact.name}** @ {contact.company_name}")
                if job:
                    st.caption(f"📎 {job.job_title}")
            with cols[1]:
                days = (datetime.now(timezone.utc) - contact.last_contacted).days if contact.last_contacted else 0
                st.caption(f"⏳ {days}d ago")
            with cols[2]:
                status_class = "warning" if days > 7 else "ready"
                st.markdown(f"<span class='status-badge status-{status_class}'>{days}d</span>", unsafe_allow_html=True)
            with cols[3]:
                if st.button("📨 ACT", key=f"act_{contact.id}_{idx}", use_container_width=True):
                    st.session_state.page = "OUTREACH"
                    st.session_state.quick_action = "SEND_MAIL"
                    st.rerun()
            
            if idx < len(items["due_today"]) - 1:
                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
    # Show stale contacts
    elif items.get("stale"):
        st.warning(f"⚠️ {len(items['stale'])} STALE CONTACTS (>14 days)")
        for idx, contact in enumerate(items["stale"][:3]):
            days = (datetime.now(timezone.utc) - contact.last_contacted).days if contact.last_contacted else 0
            st.markdown(f"• **{contact.name}** ({contact.company_name}) — {days} days no reply")
    
    else:
        st.success("✅ All caught up! No immediate actions required.")
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    # Recent activity
    st.subheader("◈ RECENT ACTIVITY")
    if not jobs_df.empty:
        recent = jobs_df.sort_values('date_applied', ascending=False).head(8)
        st.dataframe(
            recent[['date_applied', 'company_name', 'job_title', 'status']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "date_applied": st.column_config.DateColumn("DATE", format="YYYY-MM-DD"),
                "company_name": st.column_config.TextColumn("COMPANY"),
                "job_title": st.column_config.TextColumn("POSITION"),
                "status": st.column_config.TextColumn("STATUS"),
            }
        )
    else:
        st.info("📭 No jobs tracked yet. Add your first job application!")

# =====================================================
# INTELLIGENT HEADER WITH SYSTEM STATUS
# =====================================================

def render_intelligent_header(session):
    """Header with system status awareness"""
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.markdown('<h1 class="military-header">◈ JOBTRACK PRO</h1>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div style="text-align: right; color: var(--text-muted); font-size: 0.85rem; letter-spacing: 0.08em;">
                {datetime.now().strftime("%H:%M • %b %d")}
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        jobs_count = len(fetch_all_jobs(session))
        st.markdown(f"""
            <div style="text-align: right; color: #c0c0c0; font-weight: 700; font-size: 1.1rem;">
                {jobs_count} ACTIVE
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        status = get_system_status(session)
        if status["email_configured"]:
            badge_class = "ready" if status["needs_followup"] == 0 else "warning"
            badge_text = "✓ READY" if status["needs_followup"] == 0 else f"⚠️ {status['needs_followup']}"
        else:
            badge_class = "critical"
            badge_text = "SETUP"
        
        st.markdown(f"""
            <div style="text-align: right;">
                <span class='status-badge status-{badge_class}'>{badge_text}</span>
            </div>
        """, unsafe_allow_html=True)

# =====================================================
# SMART SIDEBAR NAVIGATION
# =====================================================

def render_smart_nav():
    """Context-aware navigation with visual feedback"""
    with st.sidebar:
        st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)
        st.markdown("### 🧭 NAVIGATION")
        
        pages = [
            ("⚡ DASHBOARD", "DASHBOARD"),
            ("💼 JOBS", "JOBS"),
            ("✉️ OUTREACH", "OUTREACH"),
            ("👤 CONTACTS", "CONTACTS"),
            ("📊 ANALYTICS", "ANALYTICS")
        ]
        
        # Get current page from session state
        current_page = st.session_state.page
        
        # Render radio with visual feedback
        selected = st.radio(
            "Go to",
            [p[0] for p in pages],
            index=[p[1] for p in pages].index(current_page) if current_page in [p[1] for p in pages] else 0,
            label_visibility="collapsed",
            key="nav_radio"
        )
        
        # Extract page key from display text
        page_key = dict(pages)[selected]
        return page_key

# =====================================================
# MAIN APPLICATION FLOW
# =====================================================

def main():
    """Intelligent main application with context-aware routing"""
    
    # Initialize database session (persistent across reruns)
    if 'db_session' not in st.session_state:
        st.session_state.db_session = init_db()
    session = st.session_state.db_session
    
    # Initialize app state (handles quick actions)
    initialize_app_state()
    
    # Apply military-grade styling
    apply_military_grade_styles()
    
    # Render intelligent header
    render_intelligent_header(session)
    
    # Render smart navigation
    nav_page = render_smart_nav()
    st.session_state.page = nav_page  # Single source of truth
    
    # Get current page
    page = st.session_state.page
    
    # Render page content with intelligent routing
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    
    if page == "DASHBOARD":
        render_intelligent_dashboard(session)
    
    elif page == "JOBS":
        tab_add, tab_view = st.tabs(["➕ ADD NEW", "📋 MANAGE"])
        with tab_add:
            # Show smart guidance
            status = get_system_status(session)
            if not status["has_jobs"]:
                st.info("💡 **First job?** Fill in company and title to get started. Add job link for easy access later.")
            
            with st.form("quick_job", clear_on_submit=True):
                cols = st.columns(2)
                with cols[0]:
                    company = st.text_input("COMPANY*", placeholder="Google, Microsoft, etc.", key="job_company")
                    title = st.text_input("JOB TITLE*", placeholder="Senior Engineer", key="job_title")
                    url = st.text_input("JOB LINK", placeholder="https://careers.company.com/...", key="job_url")
                with cols[1]:
                    status_sel = st.selectbox("STATUS", ["Applied", "Interview Scheduled", "Offer Received", "Rejected", "Ghosted"], key="job_status")
                    priority = st.select_slider("PRIORITY", ["Low", "Medium", "High"], value="Medium", key="job_priority")
                    date_applied = st.date_input("DATE APPLIED", value=datetime.now(timezone.utc).date(), key="job_date")
                
                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                
                if st.form_submit_button("◈ SAVE APPLICATION", use_container_width=True, type="primary"):
                    if company.strip() and title.strip():
                        add_job_application(session, {
                            "company_name": company,
                            "job_title": title,
                            "job_link": url,
                            "status": status_sel,
                            "priority": priority,
                            "date_applied": date_applied,
                            "follow_up_date": date_applied + timedelta(days=7),
                            "notes": "",
                            "location": "",
                            "interview_date": None,
                            "recruiter_contact": "",
                            "networking_contact": ""
                        })
                        st.success("✓ APPLICATION SAVED")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("⚠️ Company and Job Title are required")
        
        with tab_view:
            job_mgr = JobManager(session)
            job_mgr.view_update_ui()
    
    elif page == "OUTREACH":
        tabs = st.tabs(["⚙️ SETUP", "✉️ CAMPAIGN", "📊 TRACKING", "📥 IMPORT/EXPORT"])
        
        with tabs[0]:
            email_setup_ui(session)
        
        with tabs[1]:
            send_bulk_email_ui(session)  # Uses the smart version from outreach_ui
        
        with tabs[2]:
            response_tracking_ui(session)
        
        with tabs[3]:
            import_export_ui(session)
    
    elif page == "CONTACTS":
        tab_add, tab_list = st.tabs(["➕ ADD CONTACT", "📋 ALL CONTACTS"])
        
        with tab_add:
            status = get_system_status(session)
            if not status["has_contacts"]:
                st.info("💡 **Add your first contact** - Include name, email, and company. Link to a job later for context.")
            
            with st.form("add_contact_form", clear_on_submit=True):
                cols = st.columns(2)
                with cols[0]:
                    name = st.text_input("NAME*", placeholder="John Doe", key="contact_name")
                    email = st.text_input("EMAIL*", placeholder="john@company.com", key="contact_email")
                    company = st.text_input("COMPANY*", placeholder="Google", key="contact_company")
                with cols[1]:
                    contact_type = st.selectbox("TYPE", ["Recruiter", "HR", "Hiring Manager", "Networking", "Other"], key="contact_type")
                    phone = st.text_input("PHONE", placeholder="+1 234 567 8900", key="contact_phone")
                    linkedin = st.text_input("LINKEDIN", placeholder="linkedin.com/in/johndoe", key="contact_linkedin")
                
                # Optional job linking
                jobs = fetch_all_jobs(session)
                if not jobs.empty:
                    job_options = ["None"] + [f"{j['company_name']} - {j['job_title']}" for _, j in jobs.iterrows()]
                    job_idx = st.selectbox("LINK TO JOB (Optional)", job_options, key="contact_job_link")
                    job_id = jobs.iloc[job_options.index(job_idx)-1]["id"] if job_idx != "None" else None
                else:
                    job_id = None
                    st.caption("No jobs yet. Create a job application first to link contacts.")
                
                if st.form_submit_button("✓ SAVE CONTACT", use_container_width=True, type="primary"):
                    if name.strip() and email.strip() and company.strip():
                        from src.database import add_contact as db_add_contact
                        contact_data = {
                            "name": name,
                            "email": email,
                            "company_name": company,
                            "contact_type": contact_type,
                            "phone": phone,
                            "linkedin_url": linkedin,
                            "job_id": job_id
                        }
                        db_add_contact(session, contact_data)
                        st.success("✓ CONTACT SAVED")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("⚠️ Name, Email, and Company are required")
        
        with tab_list:
            contacts_list_ui(session)
    
    elif page == "ANALYTICS":
        tab_jobs, tab_email = st.tabs(["💼 JOB ANALYTICS", "📧 EMAIL METRICS"])
        
        with tab_jobs:
            analytics_ui(session)
        
        with tab_email:
            response_tracking_ui(session)
    
    # Footer with performance metrics
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption("✨ JobTrack Pro v3.1 • Military-Grade Job Tracking System")
    with col2:
        if 'load_time' not in st.session_state:
            st.session_state.load_time = time.time()
        elapsed = time.time() - st.session_state.load_time
        st.caption(f"⏱️ {elapsed:.2f}s")

if __name__ == "__main__":
    main()