import streamlit as st
from src.model import Contact
from src.database import init_db, fetch_all_jobs, fetch_all_contacts, add_job_application
from src.job_application import JobApplicationForm, JobManager
from src.outreach_ui import (
    email_setup_ui, 
    template_manager_ui,
    send_email_ui,
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
    
    # Clear stale quick action
    if "quick_action" in st.session_state and st.session_state.quick_action:
        st.session_state.quick_action = None

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
    """Premium dark theme with enhanced visual hierarchy and polish"""
    st.markdown("""
        <style>
        :root {
            --bg-main: #08090d;
            --bg-surface: #0f1419;
            --bg-card: #151b28;
            --bg-card-hover: #1a212f;
            --text-main: #e5e7eb;
            --text-secondary: #a0aac0;
            --text-muted: #78828f;
            --accent-gold: #daa520;
            --accent-blue: #3b82f6;
            --accent-teal: #0dd9c6;
            --danger: #ef4444;
            --success: #10b981;
            --warning: #f59e0b;
            --border-light: rgba(255, 255, 255, 0.08);
            --border-medium: rgba(255, 255, 255, 0.12);
        }
        
        * { box-sizing: border-box; }
        
        .stApp {
            background: linear-gradient(135deg, var(--bg-main) 0%, var(--bg-surface) 50%, var(--bg-main) 100%);
            color: var(--text-main);
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        .military-header {
            background: linear-gradient(90deg, var(--accent-gold) 0%, #ffffff 50%, var(--accent-gold) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.2rem;
            font-weight: 900;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            margin: 0 !important;
            padding: 1.2rem 0 !important;
            border-bottom: 2px solid var(--border-light);
        }
        
        h2 {
            color: var(--text-main) !important;
            font-weight: 700 !important;
            font-size: 1.3rem !important;
            margin-top: 1.5rem !important;
            margin-bottom: 0.8rem !important;
            letter-spacing: 0.02em;
        }
        
        h3 {
            color: var(--text-secondary) !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 1rem !important;
        }
        
        p, span, label {
            color: var(--text-main) !important;
        }
        
        [data-testid="stMetricValue"] {
            color: var(--accent-gold) !important;
            font-weight: 700 !important;
            font-size: 2.5rem !important;
        }
        
        [data-testid="stMetricLabel"] {
            color: var(--text-secondary) !important;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-size: 0.65rem !important;
            font-weight: 700 !important;
        }
        
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(21, 27, 40, 0.8) 0%, rgba(21, 27, 40, 0.4) 100%);
            border: 1px solid var(--border-light);
            border-radius: 12px;
            padding: 1.5rem !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        [data-testid="stMetric"]:hover {
            background: linear-gradient(135deg, rgba(21, 27, 40, 1) 0%, rgba(25, 32, 45, 0.8) 100%);
            border-color: var(--accent-gold);
            box-shadow: 0 8px 12px rgba(218, 165, 32, 0.15);
            transform: translateY(-2px);
        }
        
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(8, 9, 13, 0.95) 0%, rgba(15, 20, 25, 0.95) 100%);
            backdrop-filter: blur(20px);
            border-right: 1px solid var(--border-light);
        }
        
        [data-testid="stSidebar"] .stRadio label {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid transparent;
            border-radius: 10px;
            padding: 0.9rem 1.1rem;
            margin: 0.3rem 0;
            color: var(--text-secondary);
            font-weight: 600;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        [data-testid="stSidebar"] .stRadio label:hover {
            background: rgba(255, 255, 255, 0.06);
            border-color: var(--accent-gold);
            color: var(--text-main);
            transform: translateX(4px);
        }
        
        [data-testid="stSidebar"] .stRadio label[aria-checked="true"] {
            background: linear-gradient(135deg, rgba(218, 165, 32, 0.15) 0%, rgba(59, 130, 246, 0.1) 100%);
            border: 1px solid var(--accent-gold);
            border-left: 3px solid var(--accent-gold);
            color: #ffffff;
            box-shadow: 0 0 12px rgba(218, 165, 32, 0.1);
        }
        
        .main .block-container {
            padding: 2rem 2.5rem;
            max-width: 1500px;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(13, 217, 198, 0.1) 100%);
            color: var(--text-main);
            border: 1.5px solid var(--accent-blue);
            height: 48px;
            border-radius: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 0.75rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
            padding: 0 1rem !important;
            white-space: normal;
            word-wrap: break-word;
            overflow-wrap: break-word;
            min-height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            line-height: 1.3;
        }
        
        .stButton > button:hover {
            border-color: var(--accent-teal);
            color: var(--accent-teal);
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(13, 217, 198, 0.2) 100%);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(13, 217, 198, 0.2);
        }
        
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, var(--accent-gold) 0%, #e8ca5d 100%);
            color: #05050a;
            border: none;
            font-weight: 700;
            box-shadow: 0 4px 14px rgba(218, 165, 32, 0.25);
        }
        
        .stButton > button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(218, 165, 32, 0.35);
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 2px solid var(--border-light);
            padding-bottom: 0;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.02);
            border-radius: 10px 10px 0 0;
            padding: 0.8rem 1.6rem;
            color: var(--text-secondary);
            border: 1px solid transparent;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--border-light);
        }
        
        .stTabs [aria-selected="true"] {
            color: var(--accent-gold) !important;
            border: 1px solid var(--accent-gold);
            border-bottom: 2px solid var(--accent-gold);
            background: linear-gradient(135deg, rgba(218, 165, 32, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%);
            font-weight: 700;
        }
        
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stTextArea > div > div > textarea {
            background: linear-gradient(135deg, rgba(15, 20, 30, 0.8) 0%, rgba(21, 27, 40, 0.8) 100%);
            border: 1.5px solid var(--border-light);
            border-radius: 10px;
            color: var(--text-main);
            padding: 0.85rem 1.1rem;
            font-size: 0.95rem;
            transition: all 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus,
        .stTextArea > div > div > textarea:focus {
            background: linear-gradient(135deg, rgba(21, 27, 40, 1) 0%, rgba(25, 32, 45, 1) 100%);
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        .stCheckbox > label {
            color: var(--text-main) !important;
            font-weight: 500;
        }
        
        #MainMenu, footer, header { visibility: hidden !important; }
        
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: rgba(10, 10, 15, 0.5); }
        ::-webkit-scrollbar-thumb { 
            background: linear-gradient(180deg, var(--accent-gold), var(--accent-blue));
            border-radius: 4px;
            border: 2px solid var(--bg-main);
        }
        ::-webkit-scrollbar-thumb:hover { 
            background: linear-gradient(180deg, var(--accent-teal), var(--accent-gold));
        }
        
        /* Premium card styling */
        .card-container {
            background: linear-gradient(135deg, rgba(21, 27, 40, 0.6) 0%, rgba(21, 27, 40, 0.3) 100%);
            border: 1px solid var(--border-light);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
        }
        
        .card-container:hover {
            background: linear-gradient(135deg, rgba(21, 27, 40, 0.8) 0%, rgba(25, 32, 45, 0.5) 100%);
            border-color: var(--accent-gold);
            box-shadow: 0 8px 16px rgba(218, 165, 32, 0.15);
        }
        
        /* Status badges */
        .status-badge {
            display: inline-block;
            padding: 0.35rem 0.85rem;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            backdrop-filter: blur(8px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        .status-ready { 
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.25), rgba(16, 185, 129, 0.1));
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .status-warning { 
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.25), rgba(245, 158, 11, 0.1));
            color: var(--warning);
            border: 1px solid rgba(245, 158, 11, 0.3);
        }
        .status-critical { 
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.25), rgba(239, 68, 68, 0.1));
            color: var(--danger);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        
        /* Action row */
        .action-row {
            display: flex;
            align-items: center;
            padding: 1rem 1.2rem;
            background: linear-gradient(135deg, rgba(21, 27, 40, 0.5), rgba(25, 32, 45, 0.3));
            border: 1px solid var(--border-light);
            border-radius: 10px;
            margin-bottom: 0.8rem;
            transition: all 0.3s ease;
        }
        .action-row:hover {
            transform: translateX(4px);
            border-left: 3px solid var(--accent-gold);
            border-color: var(--accent-gold);
            background: linear-gradient(135deg, rgba(21, 27, 40, 0.8), rgba(25, 32, 45, 0.5));
            box-shadow: 0 4px 12px rgba(218, 165, 32, 0.1);
        }
        
        /* Table styling */
        [data-testid="stDataframe"] {
            background: transparent;
        }
        
        .dataframe {
            background: linear-gradient(135deg, rgba(21, 27, 40, 0.4), rgba(21, 27, 40, 0.2)) !important;
            border-radius: 10px !important;
            border: 1px solid var(--border-light) !important;
        }
        
        .dataframe th {
            background: linear-gradient(135deg, rgba(218, 165, 32, 0.15), rgba(59, 130, 246, 0.1)) !important;
            color: var(--accent-gold) !important;
            font-weight: 700 !important;
        }
        
        .dataframe td {
            color: var(--text-main) !important;
        }
        
        /* Form styling */
        [data-testid="stForm"] {
            background: linear-gradient(135deg, rgba(21, 27, 40, 0.5), rgba(21, 27, 40, 0.2));
            border: 1px solid var(--border-light);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

# =====================================================
# INTELLIGENT DASHBOARD (SELF-CONTAINED)
# =====================================================

def render_intelligent_dashboard(session):
    """Self-contained intelligent dashboard with prioritized actions"""
    status = get_system_status(session)
    
    # System readiness alerts with better styling
    st.markdown("### 🎯 SYSTEM STATUS", help="Real-time status of your job tracking setup")
    alert_cols = st.columns(3, gap="medium")
    
    if not status["email_configured"]:
        with alert_cols[0]:
            st.warning("📧 **Email Not Configured**\nGo to OUTREACH > SETUP", icon="⚠️")
    if not status["has_contacts"] and status["has_jobs"]:
        with alert_cols[1]:
            st.info("👤 **No Contacts Yet**\nLink recruiters for follow-ups", icon="ℹ️")
    if status["needs_followup"] > 0:
        with alert_cols[2]:
            st.error(f"⏰ **{status['needs_followup']} FOLLOW-UPS DUE!**\nAction required immediately", icon="🚨")
    
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # Metrics row with enhanced styling
    jobs_df = fetch_all_jobs(session)
    contacts_df = fetch_all_contacts(session)
    
    st.markdown("### 📊 KEY METRICS", help="Your job application tracking summary")
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    
    with col1:
        total = len(jobs_df)
        st.metric("💼 TOTAL JOBS", total, f"+{total if total > 0 else 0}")
    with col2:
        active = len(jobs_df[jobs_df['status'].isin(['Applied', 'Interview Scheduled'])]) if not jobs_df.empty else 0
        st.metric("🔥 ACTIVE", active, delta="In Pipeline" if active > 0 else "Prepare more")
    with col3:
        interviews = len(jobs_df[jobs_df['status'] == 'Interview Scheduled']) if not jobs_df.empty else 0
        st.metric("📞 INTERVIEWS", interviews, f"Scheduled" if interviews > 0 else "None yet")
    with col4:
        offers = len(jobs_df[jobs_df['status'] == 'Offer Received']) if not jobs_df.empty else 0
        st.metric("🎉 OFFERS", offers, f"Congratulations!" if offers > 0 else "Keep going")
    
    st.markdown("<div style='height: 1.8rem;'></div>", unsafe_allow_html=True)
    
    # # Smart quick actions
    # st.markdown("### ⚡ QUICK ACTIONS", help="One-click shortcuts to common tasks")
    # cols = st.columns(4, gap="large")
    
    # actions = [
    #     ("➕\nADD JOB", "ADD_JOB", True),
    #     ("👤\nADD CONTACT", "ADD_CONTACT", True),
    #     ("📧\nSEND EMAIL", "SEND_MAIL", status["email_configured"] and status["has_contacts"] and status["has_templates"]),
    #     ("🔄\nFOLLOW-UPS", "FOLLOW_UP", status["needs_followup"] > 0)
    # ]
    
    # for idx, (label, action, enabled) in enumerate(actions):
    #     with cols[idx]:
    #         if st.button(label, key=f"qa_{action}", use_container_width=True, disabled=not enabled):
    #             st.session_state.quick_action = action
    #             st.session_state.page = {"ADD_JOB": "JOBS", "ADD_CONTACT": "CONTACTS", "SEND_MAIL": "OUTREACH", "FOLLOW_UP": "DASHBOARD"}[action]
    #             st.rerun()
    
    # st.markdown("<div style='height: 1.8rem;'></div>", unsafe_allow_html=True)
    
    # Priority actions section
    st.markdown("### 🎯 ACTION REQUIRED", help="Items that need your attention today")
    
    # Get actionable items
    engine = EmailEngine(session)
    try:
        items = engine.get_actionable_items()
    except AttributeError:
        items = {"due_today": [], "recent_replies": [], "stale": []}
    
    # Show follow-ups due today with enhanced styling
    if items.get("due_today"):
        st.markdown(f"#### ⏰ **{len(items['due_today'])} FOLLOW-UPS DUE TODAY**")
        for idx, contact in enumerate(items["due_today"][:5]):
            with st.container(border=True):
                cols = st.columns([3, 1, 1, 1], gap="medium")
                with cols[0]:
                    st.markdown(f"**{contact.name}** 🎯 {contact.company_name}")
                    if hasattr(contact, 'job') and contact.job:
                        st.caption(f"📎 Position: {contact.job.job_title}")
                with cols[1]:
                    days = (datetime.now(timezone.utc) - contact.last_contacted).days if contact.last_contacted else 0
                    st.metric("Days Ago", days)
                with cols[2]:
                    status_class = "critical" if days > 14 else "warning" if days > 7 else "ready"
                    st.markdown(f"<span class='status-badge status-{status_class}'>{'URGENT' if days > 14 else 'PENDING'}</span>", unsafe_allow_html=True)
                with cols[3]:
                    if st.button("📨 SEND", key=f"act_{contact.id}_{idx}", use_container_width=True):
                        st.session_state.page = "OUTREACH"
                        st.session_state.quick_action = "SEND_MAIL"
                        st.rerun()
    
    # Show stale contacts
    elif items.get("stale"):
        st.markdown(f"#### ⚠️ **{len(items['stale'])} STALE CONTACTS (>14 days)**")
        for idx, contact in enumerate(items["stale"][:3]):
            days = (datetime.now(timezone.utc) - contact.last_contacted).days if contact.last_contacted else 0
            with st.container(border=True):
                st.markdown(f"• **{contact.name}** • {contact.company_name} • {days} days")
    else:
        st.success("✅ **All Caught Up!** No immediate actions required.", icon="🎉")
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    # Recent activity
    st.markdown("### 📋 RECENT APPLICATIONS", help="Your last 8 job applications")
    if not jobs_df.empty:
        recent = jobs_df.sort_values('date_applied', ascending=False).head(8)
        
        # Create a nice table view
        st.dataframe(
            recent[['date_applied', 'company_name', 'job_title', 'status']].rename(columns={
                'date_applied': '📅 Date',
                'company_name': '🏢 Company',
                'job_title': '💼 Position',
                'status': '📊 Status'
            }),
            use_container_width=True,
            hide_index=True,
            column_config={
                "📅 Date": st.column_config.DateColumn(format="MMM DD, YYYY"),
                "🏢 Company": st.column_config.TextColumn(width="medium"),
                "💼 Position": st.column_config.TextColumn(width="medium"),
                "📊 Status": st.column_config.TextColumn(width="small"),
            }
        )
    else:
        st.info("📭 **No applications yet.** Click 'ADD JOB' above to get started!")

# =====================================================
# INTELLIGENT HEADER WITH SYSTEM STATUS
# =====================================================

def render_intelligent_header(session):
    """Header with system status awareness and enhanced styling"""
    col1, col2, col3, col4 = st.columns([2.5, 1.2, 1.2, 1.1], gap="large")
    
    with col1:
        st.markdown('<h1 class="military-header">Applying Sets</h1>', unsafe_allow_html=True)
    
    with col2:
        current_time = datetime.now().strftime("%H:%M")
        current_date = datetime.now().strftime("%b %d")
        st.markdown(f"""
            <div style="text-align: right; margin-top: 1.2rem;">
                <div style="color: var(--text-secondary); font-size: 0.8rem; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.3rem;">
                    TIME
                </div>
                <div style="color: var(--accent-gold); font-weight: 700; font-size: 1.1rem;">
                    {current_time}
                </div>
                <div style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.2rem;">
                    {current_date}
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        jobs_count = len(fetch_all_jobs(session))
        st.markdown(f"""
            <div style="text-align: right; margin-top: 1.2rem;">
                <div style="color: var(--text-secondary); font-size: 0.8rem; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.3rem;">
                    ACTIVE
                </div>
                <div style="color: var(--accent-teal); font-weight: 700; font-size: 1.8rem;">
                    {jobs_count}
                </div>
                <div style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.2rem;">
                    JOB APPS
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        status = get_system_status(session)
        if status["email_configured"]:
            badge_class = "ready" if status["needs_followup"] == 0 else "warning"
            badge_text = "✓ READY" if status["needs_followup"] == 0 else f"⚠️ {status['needs_followup']}"
            badge_color = "#10b981" if badge_class == "ready" else "#f59e0b"
        else:
            badge_class = "critical"
            badge_text = "⚙️ SETUP"
            badge_color = "#ef4444"
        
        st.markdown(f"""
            <div style="text-align: right; margin-top: 1.2rem;">
                <div style="color: var(--text-secondary); font-size: 0.8rem; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.3rem;">
                    STATUS
                </div>
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
        tab_add, tab_view = st.tabs(["➕ ADD NEW JOB", "📋 MANAGE JOBS"])
        with tab_add:
            # Show smart guidance
            status = get_system_status(session)
            if not status["has_jobs"]:
                st.info("💡 **Getting Started?** Fill in company and title to create your first job application. Optional: Add job link for easy reference.", icon="ℹ️")
            
            st.markdown("### NEW JOB APPLICATION")
            with st.form("quick_job", clear_on_submit=True):
                cols = st.columns(2, gap="medium")
                with cols[0]:
                    company = st.text_input("🏢 Company Name*", placeholder="Google, Microsoft, Apple...", key="job_company")
                    title = st.text_input("💼 Job Title*", placeholder="Senior Software Engineer...", key="job_title")
                    url = st.text_input("🔗 Job Link", placeholder="https://careers.company.com/job/...", key="job_url", help="Direct link to job posting")
                with cols[1]:
                    status_sel = st.selectbox("📊 Status", ["Applied", "Interview Scheduled", "Offer Received", "Rejected", "Ghosted"], key="job_status")
                    priority = st.select_slider("⭐ Priority", ["Low", "Medium", "High"], value="Medium", key="job_priority")
                    date_applied = st.date_input("📅 Date Applied", value=datetime.now(timezone.utc).date(), key="job_date")
                
                st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns([1, 1, 3])
                with col3:
                    if st.form_submit_button("✓ SAVE APPLICATION", use_container_width=True, type="primary"):
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
                            st.success("✓ **Job Application Saved!**", icon="✅")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("⚠️ Company and Job Title are required", icon="❌")
        
        with tab_view:
            job_mgr = JobManager(session)
            job_mgr.view_update_ui()
    
    elif page == "OUTREACH":
        tabs = st.tabs(["🚀 CAMPAIGN", "⚙️ SETUP", "✉️ TEMPLATES", "📊 TRACKING", "📥 IMPORT/EXPORT"])
        
        with tabs[0]:
            send_email_ui(session)  # Uses the smart version from outreach_ui
        
        with tabs[1]:
            email_setup_ui(session)
        
        with tabs[2]:
            template_manager_ui(session)
        
        with tabs[3]:
            response_tracking_ui(session)
        
        with tabs[4]:
            import_export_ui(session)
    
    elif page == "CONTACTS":
        tab_add, tab_list = st.tabs(["➕ ADD CONTACT", "📋 ALL CONTACTS"])
        
        with tab_add:
            status = get_system_status(session)
            if not status["has_contacts"]:
                st.info("💡 **First Contact?** Include name, email, and company. Link to a job later for context.", icon="ℹ️")
            
            st.markdown("### NEW CONTACT")
            with st.form("add_contact_form", clear_on_submit=True):
                cols = st.columns(2, gap="medium")
                with cols[0]:
                    name = st.text_input("👤 Full Name*", placeholder="John Smith", key="contact_name")
                    email = st.text_input("📧 Email*", placeholder="john.smith@company.com", key="contact_email")
                    company = st.text_input("🏢 Company*", placeholder="Google", key="contact_company")
                with cols[1]:
                    contact_type = st.selectbox("🔗 Contact Type", ["Recruiter", "HR", "Hiring Manager", "Networking", "Other"], key="contact_type")
                    phone = st.text_input("📞 Phone", placeholder="+1 (555) 123-4567", key="contact_phone")
                    linkedin = st.text_input("💼 LinkedIn URL", placeholder="linkedin.com/in/johnsmith/", key="contact_linkedin")
                
                # Optional job linking
                jobs = fetch_all_jobs(session)
                if not jobs.empty:
                    job_options = ["✖️ None"] + [f"🔗 {j['company_name']} - {j['job_title']}" for _, j in jobs.iterrows()]
                    job_idx = st.selectbox("📎 Link to Job (Optional)", job_options, key="contact_job_link", help="Associate this contact with a specific job application")
                    job_id = jobs.iloc[job_options.index(job_idx)-1]["id"] if job_idx != "✖️ None" else None
                else:
                    job_id = None
                    st.caption("📝 **Tip:** Create a job application first to link contacts directly.", help="This helps organize your outreach better")
                
                st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns([1, 1, 3])
                with col3:
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
                            st.success("✓ **Contact Saved!**", icon="✅")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("⚠️ Name, Email, and Company are required", icon="❌")
        
        with tab_list:
            contacts_list_ui(session)
    
    elif page == "ANALYTICS":
        tabs = st.tabs(["💼 JOB ANALYTICS", "📧 EMAIL METRICS"])
        
        with tabs[0]:
            st.markdown("### INTERVIEW & OFFER TRACKING")
            analytics_ui(session)
        
        with tabs[1]:
            st.markdown("### EMAIL PERFORMANCE")
            response_tracking_ui(session)
    
    # Footer with performance metrics
    st.markdown("<div style='height: 2.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    
    footer_col1, footer_col2, footer_col3 = st.columns([2, 1, 1])
    with footer_col1:
        st.caption("✨ **JobTrack Pro v3.2** • Military-Grade Job Tracking System • Built for Success")
    with footer_col2:
        status = get_system_status(session)
        if status["email_configured"]:
            st.caption("✅ System Ready" if status["needs_followup"] == 0 else f"⚠️ {status['needs_followup']} Actions")
    with footer_col3:
        if 'load_time' not in st.session_state:
            st.session_state.load_time = time.time()
        elapsed = time.time() - st.session_state.load_time
        st.caption(f"⏱️ Loaded in {elapsed:.2f}s")

if __name__ == "__main__":
    main()