# src/job_application.py

import re
from datetime import datetime, timedelta, timezone
import pandas as pd
import streamlit as st

from src.database import (
    add_job_application,
    fetch_all_jobs,
    update_job_application,
    delete_job_application,
)

# =====================================================
# STATE KEYS
# =====================================================

CARDS_PAGE = "jobs_cards_page"
EDIT_ID = "edit_job_id"
VIEW_MODE = "jobs_view_mode"   # cards | kanban

STATUSES = [
    "Applied",
    "Interview Scheduled",
    "Offer Received",
    "Rejected",
    "Ghosted"
]

# =====================================================
# UTILS
# =====================================================

def is_valid_url(url: str) -> bool:
    return bool(re.match(r"^https?://.+", url))

def safe_contains(series, text):
    return series.fillna("").str.contains(text, case=False, regex=False)

# =====================================================
# ADD JOB FORM
# =====================================================

class JobApplicationForm:
    def __init__(self, session):
        self.session = session

    def render(self):
        st.subheader("➕ Add Job")

        with st.form("add_job", clear_on_submit=True):
            c1, c2 = st.columns(2)

            with c1:
                company = st.text_input("Company")
                title = st.text_input("Job Title")
                location = st.text_input("Location")
                link = st.text_input("Job Link")
                priority = st.selectbox("Priority", ["Low","Medium","High"])

            with c2:
                status = st.selectbox("Status", STATUSES)
                applied = st.date_input("Date Applied", value=datetime.now(timezone.utc).date())
                follow = st.date_input("Follow-up", value=applied + timedelta(days=7))
                notes = st.text_area("Notes")

            if st.form_submit_button("Save"):
                if not company.strip() or not title.strip():
                    st.error("Company & Title required")
                    return

                if link and not is_valid_url(link):
                    st.error("Invalid URL")
                    return

                add_job_application(self.session, {
                    "company_name": company,
                    "job_title": title,
                    "location": location,
                    "job_link": link,
                    "status": status,
                    "priority": priority,
                    "date_applied": applied,
                    "follow_up_date": follow,
                    "interview_date": None,
                    "notes": notes,
                    "recruiter_contact": "",
                    "networking_contact": ""
                })

                st.success("✓ Saved")
                st.rerun()

# =====================================================
# JOB CARD (FIXED: Added session parameter for delete)
# =====================================================

def render_job_card(job, session):
    with st.container(border=True):
        left, right = st.columns([4, 1])

        with left:
            st.markdown(f"### {job['job_title']}")
            st.caption(f"{job['company_name']} — {job['location'] or 'Remote'}")
            st.write(f"**{job['status']} | {job['priority']}**")
            st.caption(f"Applied: {job['date_applied']} | Follow-up: {job['follow_up_date']}")

            if job.get("job_link"):
                st.markdown(f"[🔗 Open Link]({job['job_link']})")

            if job.get("notes"):
                st.caption(job["notes"][:100] + "..." if len(job["notes"]) > 100 else job["notes"])

        with right:
            if st.button("✏️", key=f"edit_{job['id']}", width='stretch'):
                st.session_state[EDIT_ID] = job["id"]
                st.rerun()

            if st.button("🗑️", key=f"del_{job['id']}", width='stretch'):
                delete_job_application(session, job["id"])
                st.rerun()

# =====================================================
# EDIT PANEL
# =====================================================

def render_edit_panel(session, jobs_df):
    job_id = st.session_state.get(EDIT_ID)
    if not job_id:
        return

    row = jobs_df[jobs_df["id"] == job_id]
    if row.empty:
        st.session_state[EDIT_ID] = None
        st.rerun()
        return

    job = row.iloc[0]

    st.divider()
    st.subheader(f"✏️ Edit: {job['job_title']} @ {job['company_name']}")

    with st.form("edit_job"):
        status = st.selectbox(
            "Status",
            STATUSES,
            index=STATUSES.index(job["status"])
        )

        priority = st.selectbox(
            "Priority",
            ["Low", "Medium", "High"],
            index=["Low", "Medium", "High"].index(job["priority"])
        )

        follow = st.date_input(
            "Follow-up Date",
            value=pd.to_datetime(job["follow_up_date"]).date()
        )

        notes = st.text_area("Notes", value=job["notes"])

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("✓ Update", width='stretch'):
                update_job_application(session, job_id, {
                    "status": status,
                    "priority": priority,
                    "follow_up_date": follow,
                    "notes": notes
                })
                st.session_state[EDIT_ID] = None
                st.success("✓ Updated")
                st.rerun()
        with col2:
            if st.form_submit_button("✗ Cancel", width='stretch'):
                st.session_state[EDIT_ID] = None
                st.rerun()

# =====================================================
# KANBAN BOARD (FIXED: Proper status handling & no infinite loops)
# =====================================================


def render_kanban(session, df):
    """Intelligent Kanban board with horizontal scroll, smart cards, and workflow automation"""
    
    # Smart status flow mapping (context-aware next steps)
    STATUS_FLOW = {
        "Applied": ["Interview Scheduled", "Ghosted"],
        "Interview Scheduled": ["Offer Received", "Rejected"],
        "Offer Received": ["Rejected"],  # For declined offers
        "Rejected": ["Applied"],  # Rare but possible (re-apply)
        "Ghosted": ["Applied"]    # Re-engage later
    }
    
    # Priority color mapping
    PRIORITY_COLORS = {
        "High": "#ff6b6b",
        "Medium": "#ffa502",
        "Low": "#4ecdc4"
    }
    
    # Add intelligent Kanban CSS
    st.markdown("""
        <style>
        .kanban-board {
            display: flex;
            overflow-x: auto;
            padding: 10px 0;
            gap: 20px;
            margin-bottom: 2rem;
            scrollbar-width: thin;
            scrollbar-color: rgba(192, 192, 192, 0.3) transparent;
        }
        .kanban-board::-webkit-scrollbar {
            height: 8px;
        }
        .kanban-board::-webkit-scrollbar-track {
            background: rgba(10, 10, 15, 0.3);
            border-radius: 4px;
        }
        .kanban-board::-webkit-scrollbar-thumb {
            background: rgba(192, 192, 192, 0.4);
            border-radius: 4px;
        }
        .kanban-column {
            min-width: 320px;
            background: rgba(23, 31, 42, 0.7);
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            display: flex;
            flex-direction: column;
            max-height: 75vh;
            border: 1px solid rgba(192, 192, 192, 0.1);
        }
        .kanban-header {
            padding: 10px 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            text-align: center;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 0.95rem;
        }
        .status-applied { background: rgba(143,170,220,0.15); color: var(--accent-steel); border-left: 3px solid var(--accent-steel); }
        .status-interview { background: rgba(224,177,92,0.15); color: var(--warning); border-left: 3px solid var(--warning); }
        .status-offer { background: rgba(111,207,151,0.15); color: var(--success); border-left: 3px solid var(--success); }
        .status-rejected { background: rgba(209,109,109,0.15); color: var(--danger); border-left: 3px solid var(--danger); }
        .status-ghosted { background: rgba(154,163,173,0.12); color: var(--text-muted); border-left: 3px solid #9aa3ad; }
        
        .kanban-cards {
            flex: 1;
            overflow-y: auto;
            padding-right: 5px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .kanban-cards::-webkit-scrollbar {
            width: 6px;
        }
        .kanban-cards::-webkit-scrollbar-track {
            background: rgba(10, 10, 15, 0.2);
            border-radius: 3px;
        }
        .kanban-cards::-webkit-scrollbar-thumb {
            background: rgba(192, 192, 192, 0.3);
            border-radius: 3px;
        }
        
        .kanban-card {
            background: rgba(30, 38, 50, 0.9);
            border-radius: 10px;
            padding: 14px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            border-left: 3px solid var(--accent-gold);
            transition: all 0.2s ease;
            position: relative;
        }
        .kanban-card:hover {
            transform: translateX(3px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            border-left-color: var(--accent-jade);
        }
        .kanban-card-title {
            font-weight: 600;
            font-size: 1.05rem;
            margin-bottom: 4px;
            display: -webkit-box;
            -webkit-line-clamp: 1;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .kanban-card-company {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 8px;
            display: -webkit-box;
            -webkit-line-clamp: 1;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .kanban-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 8px;
            font-size: 0.8rem;
        }
        .priority-badge {
            padding: 2px 8px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .followup-badge {
            background: rgba(224,177,92,0.2);
            color: var(--warning);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        .overdue {
            background: rgba(209,109,109,0.25) !important;
            color: var(--danger) !important;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(209, 109, 109, 0.4); }
            70% { box-shadow: 0 0 0 8px rgba(209, 109, 109, 0); }
            100% { box-shadow: 0 0 0 0 rgba(209, 109, 109, 0); }
        }
        .kanban-actions {
            display: flex;
            gap: 6px;
            margin-top: 10px;
            justify-content: space-between;
        }
        .kanban-action-btn {
            flex: 1;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            text-align: center;
            transition: all 0.2s;
        }
        .kanban-action-btn:hover {
            transform: translateY(-1px);
        }
        .move-btn {
            background: rgba(108, 92, 231, 0.2);
            color: #8257e5;
            border: 1px solid rgba(108, 92, 231, 0.3);
        }
        .move-btn:hover {
            background: rgba(108, 92, 231, 0.3);
        }
        .edit-btn {
            background: rgba(94, 235, 235, 0.15);
            color: #4cc9f0;
            border: 1px solid rgba(94, 235, 235, 0.3);
        }
        .edit-btn:hover {
            background: rgba(94, 235, 235, 0.25);
        }
        .empty-state {
            text-align: center;
            padding: 25px 15px;
            color: var(--text-muted);
            font-style: italic;
            font-size: 0.9rem;
        }
        .add-to-column {
            background: rgba(111, 207, 151, 0.1);
            border: 1px dashed var(--success);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            margin-top: 10px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .add-to-column:hover {
            background: rgba(111, 207, 151, 0.2);
            transform: translateY(-2px);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Render Kanban board container
    st.markdown('<div class="kanban-board">', unsafe_allow_html=True)
    
    for status in STATUSES:
        subset = df[df["status"] == status].copy().sort_values(
            by=["priority", "follow_up_date"], 
            key=lambda x: x.map({"High": 0, "Medium": 1, "Low": 2}) if x.name == "priority" else x,
            ascending=[True, True]
        )
        
        # Column header with smart count
        status_class = status.lower().replace(" ", "-")
        count_badge = f" ({len(subset)})" if len(subset) > 0 else ""
        
        st.markdown(f"""
            <div class="kanban-column">
                <div class="kanban-header status-{status_class}">
                    {status.upper()}{count_badge}
                </div>
                <div class="kanban-cards">
        """, unsafe_allow_html=True)
        
        # Empty state with smart suggestion
        if subset.empty:
            if status == "Applied":
                hint = "Add jobs to track your applications"
            elif status == "Interview Scheduled":
                hint = "Move promising applications here"
            elif status == "Offer Received":
                hint = "🎉 Celebrate your successes!"
            else:
                hint = "Update status when needed"
            
            st.markdown(f"""
                <div class="empty-state">
                    <div style="font-size: 2.5rem; margin-bottom: 10px;">----------</div>
                    <div>{hint}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            # Render each job card
            for _, job in subset.iterrows():
                # Priority badge
                priority_color = PRIORITY_COLORS.get(job['priority'], "#6c757d")
                priority_badge = f"<span class='priority-badge' style='background:{priority_color}20; color:{priority_color}'>{job['priority']}</span>"
                
                # Follow-up badge with smart warning
                followup_date = pd.to_datetime(job['follow_up_date']).date() if job['follow_up_date'] else None
                today = datetime.now(timezone.utc).date()
                followup_badge = ""
                
                if followup_date:
                    days_until = (followup_date - today).days
                    if days_until <= 0:
                        followup_badge = f"<span class='followup-badge overdue'>OVERDUE</span>"
                    elif days_until <= 2:
                        followup_badge = f"<span class='followup-badge'>Due in {days_until}d</span>"
                    else:
                        followup_badge = f"<span class='followup-badge'>{followup_date.strftime('%b %d')}</span>"
                
                # Render compact job card
                st.markdown(f"""
                    <div class="kanban-card">
                        <div class="kanban-card-title">{job['job_title']}</div>
                        <div class="kanban-card-company">{job['company_name']}</div>
                        <div class="kanban-meta">
                            {priority_badge}
                            {followup_badge}
                        </div>
                """, unsafe_allow_html=True)
                
                # Action buttons - context-aware
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Edit", key=f"kedit_{job['id']}", width='stretch'):
                        st.session_state[EDIT_ID] = job["id"]
                        st.rerun()
                
                with col2:
                    # Smart move buttons based on status flow
                    next_statuses = STATUS_FLOW.get(status, [])
                    if next_statuses:
                        next_status = next_statuses[0]  # Primary next step
                        if st.button(f"→ {next_status.split()[0]}", key=f"move_{job['id']}_{next_status}", width='stretch'):
                            update_job_application(session, job["id"], {"status": next_status})
                            st.rerun()
                    else:
                        if st.button("🗑️ Delete", key=f"kdel_{job['id']}", width='stretch'):
                            delete_job_application(session, job["id"])
                            st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)  # Close kanban-card
        
        # Add job to column button (smart placement)
        if status == "Applied":
            st.markdown("""
                <div class="add-to-column" onclick="window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'add_to_applied'}, '*')">
                    ➕ Add New Application
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)  # Close kanban-cards and kanban-column
    
    st.markdown("</div>", unsafe_allow_html=True)  # Close kanban-board
    
    # Handle add job action
    if st.session_state.get('add_to_column') == 'applied':
        st.session_state[VIEW_MODE] = "cards"
        st.session_state[CARDS_PAGE] = 1
        st.rerun()

# =====================================================
# JOB MANAGER (ENHANCED WITH KANBAN INTEGRATION)
# =====================================================

class JobManager:
    def __init__(self, session):
        self.session = session

    def view_update_ui(self):
        st.subheader("📋 Jobs Management")
        
        jobs = fetch_all_jobs(self.session)
        st.caption(f"Total tracked: {len(jobs)} jobs • Last updated: {datetime.now().strftime('%H:%M')}")
        
        if jobs.empty:
            st.info("📭 No jobs tracked yet. Add your first job application to get started!")
            if st.button("➕ Add Job Now", type="primary"):
                st.session_state.page = "JOBS"
                st.rerun()
            return

        # View mode toggle with smart default
        if VIEW_MODE not in st.session_state:
            # Default to Kanban if >3 jobs, else Cards
            st.session_state[VIEW_MODE] = "kanban" if len(jobs) > 3 else "cards"
        
        col1, col2 = st.columns([3, 1])
        with col1:
            mode = st.radio(
                "View Mode",
                ["kanban", "cards"],
                horizontal=True,
                index=0 if st.session_state[VIEW_MODE] == "kanban" else 1,
                label_visibility="collapsed"
            )
        with col2:
            st.caption("💡 Tip: Use Kanban for workflow, Cards for details")
        
        st.session_state[VIEW_MODE] = mode
        
        # Filters with smart defaults
        with st.expander("🔍 Filters", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                status_f = st.selectbox("Status", ["All"] + STATUSES, 
                                      index=0 if mode == "kanban" else 1)
            with col2:
                priority_f = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
            with col3:
                since = st.date_input(
                    "Since",
                    value=datetime.now(timezone.utc).date() - timedelta(days=365),
                    min_value=datetime(2000, 1, 1).date()
                )
            
            search = st.text_input("Search", placeholder="Company, title, or notes...")
        
        # Apply filters
        df = jobs.copy()
        if search:
            df = df[
                safe_contains(df["company_name"], search) |
                safe_contains(df["job_title"], search) |
                safe_contains(df["notes"], search)
            ]
        if status_f != "All":
            df = df[df["status"] == status_f]
        if priority_f != "All":
            df = df[df["priority"] == priority_f]
        try:
            df["date_applied_naive"] = pd.to_datetime(df["date_applied"]).dt.date
            df = df[df["date_applied_naive"] >= since]
            df.drop(columns=["date_applied_naive"], inplace=True)
        except:
            pass
        
        st.caption(f"Showing {len(df)} of {len(jobs)} jobs")
        
        if df.empty:
            st.warning("📭 No jobs match filters. Try adjusting or resetting filters.")
            if st.button("↺ Reset Filters"):
                st.rerun()
            return
        
        # Render selected view
        if mode == "kanban":
            render_kanban(self.session, df)
        else:
            # Card view pagination
            if CARDS_PAGE not in st.session_state:
                st.session_state[CARDS_PAGE] = 1
            
            per_page = 6
            total_pages = max(1, (len(df) + per_page - 1) // per_page)
            page = st.session_state[CARDS_PAGE]
            
            # Pagination controls
            pg_col1, pg_col2, pg_col3 = st.columns([1, 2, 1])
            with pg_col1:
                if st.button("⬅ Prev", disabled=(page == 1)):
                    st.session_state[CARDS_PAGE] -= 1
                    st.rerun()
            with pg_col2:
                st.caption(f"Page {page} of {total_pages} • {len(df)} jobs")
            with pg_col3:
                if st.button("Next ➡", disabled=(page == total_pages)):
                    st.session_state[CARDS_PAGE] += 1
                    st.rerun()
            
            # Display cards
            start = (page - 1) * per_page
            page_df = df.iloc[start:start + per_page]
            
            for _, job in page_df.iterrows():
                render_job_card(job, self.session)
                st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        
        # Edit panel (works for both views)
        render_edit_panel(self.session, jobs)