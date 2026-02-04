"""
Email outreach UI components for Streamlit
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone

from src.calendar_integration import calendar_download_button
from src.model import Contact, EmailTemplate, Job
from src.email_engine import EmailEngine, get_active_email_account, test_smtp_connection
from src.database import (
    add_contact, fetch_all_contacts, update_contact, delete_contact,
    add_email_template, get_all_templates, update_template, delete_template,
    get_email_logs, get_followup_candidates, import_contacts_csv, import_jobs_csv
)
from src.security import CredentialManager

def email_setup_ui(session):
    """FR-8: Email Account Setup UI"""
    st.subheader("📧 Email Account Setup")
    
    # Show current account if exists
    current_account = get_active_email_account(session)
    if current_account:
        st.success(f"✅ Active account: {current_account.email_address}")
        st.caption(f"SMTP: {current_account.smtp_server}:{current_account.smtp_port}")
        
        if st.button("Disconnect Account"):
            current_account.is_active = False
            session.commit()
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 🔧 Configure New Account")
    st.info("""
    **Gmail Users**: You need an [App Password](https://myaccount.google.com/apppasswords)
    - Enable 2FA on your Google account
    - Generate an App Password (select "Mail" and your device)
    - Use that 16-character password here
    """)
    
    with st.form("email_setup"):
        email = st.text_input("📧 Email Address")
        app_password = st.text_input("🔑 App Password", type="password")
        smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
        smtp_port = st.number_input("SMTP Port", value=587, min_value=1, max_value=65535)
        
        col1, col2 = st.columns(2)
        with col1:
            test_only = st.form_submit_button("🧪 Test Connection Only")
        with col2:
            save_setup = st.form_submit_button("💾 Save & Connect")
        
        if test_only or save_setup:
            if not email or not app_password:
                st.error("Email and password are required")
            else:
                success, message = test_smtp_connection(email, app_password, smtp_server, smtp_port)
                
                if success:
                    st.success(message)
                    if save_setup:
                        engine = EmailEngine(session)
                        success, msg = engine.setup_account(email, app_password, smtp_server, smtp_port)
                        if success:
                            st.success(msg)
                            st.balloons()
                        else:
                            st.error(msg)
                else:
                    st.error(message)

def template_manager_ui(session):
    """FR-9: Email Template Management UI"""
    st.subheader("✉️ Email Templates")
    
    # Create default templates if none exist
    if len(get_all_templates(session)) == 0:
        with st.spinner("Creating default templates..."):
            add_email_template(
                session,
                "Cold Outreach",
                "Interest in {job_title} Position at {company}",
                """Dear {name},

I hope this email finds you well. I'm writing to express my interest in the {job_title} position at {company}.

[Your introduction and why you're interested...]

I've attached my resume for your review and would welcome the opportunity to discuss how my background aligns with your needs.

Thank you for your time and consideration.

Best regards,
{your_name}"""
            )
            add_email_template(
                session,
                "Follow-up #1",
                "Following up - {job_title} Opportunity at {company}",
                """Dear {name},

I hope you're doing well. I wanted to follow up on my previous email regarding the {job_title} position at {company}.

I remain very interested in this opportunity and would appreciate any updates on the hiring process.

Thank you for your time.

Best regards,
{your_name}""",
                is_followup=True,
                days_after_previous=7
            )
            add_email_template(
                session,
                "Follow-up #2",
                "Second follow-up - {job_title} Position",
                """Dear {name},

I hope this message finds you well. I'm following up again regarding my application for the {job_title} role at {company}.

I understand you're busy, but I wanted to reiterate my strong interest in this position and {company} as a whole.

Please let me know if there's any additional information I can provide.

Best regards,
{your_name}""",
                is_followup=True,
                days_after_previous=7
            )
            st.success("✅ Default templates created!")
            st.rerun()
    
    # Display templates
    templates = get_all_templates(session)
    
    for template in templates:
        with st.expander(f"{'🔄' if template.is_followup else '📧'} {template.name}", expanded=False):
            with st.form(f"template_{template.id}"):
                name = st.text_input("Template Name", template.name, key=f"name_{template.id}")
                subject = st.text_input("Subject Line", template.subject, key=f"subj_{template.id}")
                body = st.text_area("Email Body", template.body, height=300, key=f"body_{template.id}")
                is_followup = st.checkbox("Is Follow-up Template?", template.is_followup, key=f"fu_{template.id}")
                days_after = st.number_input("Days After Previous Contact", 
                                            value=template.days_after_previous, 
                                            min_value=1, 
                                            key=f"days_{template.id}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    save_btn = st.form_submit_button("💾 Save")
                with col2:
                    preview_btn = st.form_submit_button("👁️ Preview")
                with col3:
                    delete_btn = st.form_submit_button("🗑️ Delete")
                
                if save_btn:
                    update_template(session, template.id, {
                        "name": name,
                        "subject": subject,
                        "body": body,
                        "is_followup": is_followup,
                        "days_after_previous": days_after
                    })
                    st.success("Template updated!")
                    st.rerun()
                
                if preview_btn:
                    st.info("Preview with sample data:")
                    sample_contact = type('obj', (object,), {
                        'name': 'John Doe',
                        'company_name': 'TechCorp',
                        'email': 'john@techcorp.com'
                    })()
                    sample_job = type('obj', (object,), {
                        'job_title': 'Senior Developer',
                        'company_name': 'TechCorp'
                    })()
                    
                    from src.email_engine import EmailEngine
                    engine = EmailEngine(session)
                    subj, body_txt = engine.format_template(template, sample_contact, sample_job)
                    
                    st.markdown(f"**Subject:** {subj}")
                    st.text_area("Body Preview", body_txt, height=200)
                
                if delete_btn:
                    if st.warning("⚠️ Delete this template?"):
                        delete_template(session, template.id)
                        st.success("Template deleted!")
                        st.rerun()
    
    # Add new template
    with st.expander("➕ Create New Template"):
        with st.form("new_template"):
            name = st.text_input("Template Name")
            subject = st.text_input("Subject Line")
            body = st.text_area("Email Body", height=300)
            is_followup = st.checkbox("Is Follow-up Template?")
            days_after = st.number_input("Days After Previous Contact", value=7, min_value=1)
            
            if st.form_submit_button("Create Template"):
                if name and subject and body:
                    add_email_template(session, name, subject, body, is_followup, days_after)
                    st.success(f"Template '{name}' created!")
                    st.rerun()
                else:
                    st.error("All fields are required")

def send_single_email_ui(session):
    """FR-10: Send Single Email UI"""
    st.subheader("📨 Send Single Email")
    
    # Check if email account is configured
    account = get_active_email_account(session)
    if not account:
        st.warning("📧 No email account configured. Please set up your email account first.")
        if st.button("Go to Email Setup"):
            st.session_state.page = "Email Setup"
            st.rerun()
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 👤 Select Contact")
        contacts = fetch_all_contacts(session)
        if contacts.empty:
            st.warning("No contacts found. Add contacts first!")
            return
        
        contact_options = contacts.apply(lambda x: f"{x['name']} - {x['email']} ({x['company_name']})", axis=1).tolist()
        contact_idx = st.selectbox("Choose Contact", range(len(contact_options)), 
                                  format_func=lambda x: contact_options[x])
        selected_contact = contacts.iloc[contact_idx]
    
    with col2:
        st.markdown("### ✉️ Select Template")
        templates = get_all_templates(session)
        if not templates:
            st.warning("No templates found. Create templates first!")
            return
        
        template_names = [t.name for t in templates]
        template_idx = st.selectbox("Choose Template", range(len(template_names)), 
                                   format_func=lambda x: template_names[x])
        selected_template = templates[template_idx]
    
    # Preview email
    st.markdown("---")
    st.markdown("### 📧 Email Preview")
    
    contact_obj = session.query(Contact).get(selected_contact["id"])
    job = session.query(Job).get(contact_obj.job_id) if contact_obj.job_id else None
    
    engine = EmailEngine(session)
    subject, body = engine.format_template(selected_template, contact_obj, job)
    
    st.text_input("To", f"{contact_obj.name} <{contact_obj.email}>", disabled=True)
    st.text_input("Subject", subject, disabled=True)
    st.text_area("Body", body, height=300, disabled=True)
    
    # Send button
    st.markdown("---")
    if st.button("🚀 Send Email", type="primary", use_container_width=True):
        with st.spinner("Sending email..."):
            engine = EmailEngine(session)
            engine.connect_smtp(account.email_address)
            success, message = engine.send_email(contact_obj, selected_template, job)
            engine.disconnect_smtp()
            
            if success:
                st.success(message)
                st.balloons()
                # Show log entry
                logs = get_email_logs(session, contact_obj.id, limit=1)
                if logs:
                    st.info(f"📧 Logged: {logs[0].sent_at.strftime('%Y-%m-%d %H:%M')}")
            else:
                st.error(message)

def send_bulk_email_ui(session):
    """FR-11: Bulk Email Send UI"""
    st.subheader("📤 Bulk Email Campaign")
    
    account = get_active_email_account(session)
    if not account:
        st.warning("📧 No email account configured.")
        return
    
    # Select contacts
    st.markdown("### 👥 Select Contacts")
    contacts_df = fetch_all_contacts(session)
    if contacts_df.empty:
        st.warning("No contacts available.")
        return
    
    # Multi-select contacts
    contact_options = contacts_df.apply(
        lambda x: f"{x['name']} - {x['email']} ({x['company_name']})", 
        axis=1
    ).tolist()
    
    selected_indices = st.multiselect(
        "Choose contacts (max 20)",
        range(min(20, len(contact_options))),
        format_func=lambda x: contact_options[x]
    )
    
    if len(selected_indices) > 20:
        st.error("Maximum 20 contacts per bulk send")
        selected_indices = selected_indices[:20]
    
    st.caption(f"Selected: {len(selected_indices)} contacts")
    
    # Select template
    st.markdown("### ✉️ Select Template")
    templates = get_all_templates(session)
    if not templates:
        st.warning("No templates found.")
        return
    
    template_names = [t.name for t in templates]
    template_idx = st.selectbox("Template", range(len(template_names)), 
                               format_func=lambda x: template_names[x])
    selected_template = templates[template_idx]
    
    # Campaign settings
    st.markdown("### ⚙️ Campaign Settings")
    col1, col2 = st.columns(2)
    with col1:
        rate_limit = st.slider("Seconds between emails", 5, 60, 10)
    with col2:
        daily_limit = st.number_input("Daily send limit", 10, 100, 50)
    
    st.info(f"""
    **Campaign Summary:**
    - Recipients: {len(selected_indices)}
    - Template: {selected_template.name}
    - Rate limit: {rate_limit}s between emails
    - Estimated time: {len(selected_indices) * rate_limit // 60} minutes
    """)
    
    # Send button with confirmation
    if st.button("🚀 Start Campaign", type="primary"):
        if not selected_indices:
            st.error("Please select at least one contact")
        else:
            if st.checkbox("⚠️ I confirm I want to send to all selected contacts"):
                contact_ids = contacts_df.iloc[selected_indices]["id"].tolist()
                
                with st.spinner("Sending campaign..."):
                    engine = EmailEngine(session)
                    engine.rate_limit_delay = rate_limit
                    engine.daily_limit = daily_limit
                    
                    success, result = engine.send_bulk_emails(contact_ids, selected_template.id)
                    
                    if success:
                        st.success("Campaign completed!")
                        st.code(result)
                    else:
                        st.error(result)

def followup_dashboard_ui(session):
    """FR-14 & FR-15: Follow-up Dashboard"""
    st.subheader("🔄 Follow-up Dashboard")
    
    # Get follow-up candidates (FR-13)
    candidates = get_followup_candidates(session, days_threshold=7)
    
    if not candidates:
        st.success("✅ No contacts need follow-up right now!")
        st.caption("Contacts will appear here when it's been 7+ days since last contact")
    else:
        st.warning(f"⚠️ {len(candidates)} contacts need follow-up")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            show_all = st.checkbox("Show all contacts", value=True)
        with col2:
            sort_by = st.selectbox("Sort by", ["Days since contact", "Company", "Name"])
        
        # Display candidates
        for contact in candidates:
            days_since = (datetime.now(timezone.utc) - contact.last_contacted).days
            
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**{contact.name}**")
                    st.caption(f"{contact.email}")
                
                with col2:
                    st.caption(contact.company_name)
                    if contact.job_id:
                        job = session.query(Job).get(contact.job_id)
                        if job:
                            st.caption(f"📎 {job.job_title}")
                
                with col3:
                    st.warning(f"⏳ {days_since} days ago")
                
                with col4:
                    if st.button("📨 Send", key=f"followup_{contact.id}"):
                        # Auto-select follow-up template
                        templates = get_all_templates(session)
                        followup_templates = [t for t in templates if t.is_followup]
                        
                        if not followup_templates:
                            st.error("No follow-up template found. Create one first!")
                        else:
                            template = followup_templates[0]  # Use first follow-up template
                            
                            account = get_active_email_account(session)
                            if not account:
                                st.error("Email account not configured")
                            else:
                                with st.spinner("Sending..."):
                                    engine = EmailEngine(session)
                                    engine.connect_smtp(account.email_address)
                                    success, message = engine.send_email(contact, template, 
                                                                        session.query(Job).get(contact.job_id) if contact.job_id else None)
                                    engine.disconnect_smtp()
                                    
                                    if success:
                                        st.success("✅ Sent!")
                                        st.rerun()
                                    else:
                                        st.error(message)
                
                st.divider()
        
        st.info(f"💡 **Tip**: Configure a follow-up template with variables like {{name}}, {{company}} for personalized emails")

def import_export_ui(session):
    """FR-18 & FR-19: CSV Import/Export UI"""
    st.subheader("📥 Import / Export Data")
    
    tab1, tab2, tab3 = st.tabs(["Import Contacts", "Import Jobs", "Export Data"])
    
    with tab1:
        st.markdown("### Import Contacts from CSV")
        st.info("CSV must have columns: `name`, `email`, `company_name`")
        st.caption("Optional columns: `contact_type`, `phone`, `linkedin_url`")
        
        uploaded_file = st.file_uploader("Choose CSV file", type=["csv"], key="contacts_csv")
        
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.write("Preview:")
            st.dataframe(df.head())
            
            if st.button("📤 Import Contacts"):
                with st.spinner("Importing..."):
                    success_count, errors = import_contacts_csv(session, df)
                    
                    if errors:
                        st.warning(f"Imported {success_count}, Errors: {len(errors)}")
                        with st.expander("View Errors"):
                            for err in errors[:10]:
                                st.text(err)
                    else:
                        st.success(f"✅ Successfully imported {success_count} contacts!")
                        st.balloons()
    
    with tab2:
        st.markdown("### Import Jobs from CSV")
        st.info("CSV must have columns: `company_name`, `job_title`, `date_applied`")
        st.caption("Date format: YYYY-MM-DD")
        
        uploaded_file = st.file_uploader("Choose CSV file", type=["csv"], key="jobs_csv")
        
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.write("Preview:")
            st.dataframe(df.head())
            
            if st.button("📤 Import Jobs"):
                with st.spinner("Importing..."):
                    success_count, errors = import_jobs_csv(session, df)
                    
                    if errors:
                        st.warning(f"Imported {success_count}, Errors: {len(errors)}")
                        with st.expander("View Errors"):
                            for err in errors[:10]:
                                st.text(err)
                    else:
                        st.success(f"✅ Successfully imported {success_count} jobs!")
                        st.balloons()
    
    with tab3:
        st.markdown("### Export Data")
        
        export_type = st.selectbox("Export", ["All Contacts", "All Jobs", "Email Logs"])
        
        if st.button("📥 Download CSV"):
            if export_type == "All Contacts":
                df = fetch_all_contacts(session)
            elif export_type == "All Jobs":
                from src.database import fetch_all_jobs
                df = fetch_all_jobs(session)
            else:
                logs = get_email_logs(session, limit=1000)
                df = pd.DataFrame([{
                    "contact_id": l.contact_id,
                    "subject": l.subject,
                    "sent_at": l.sent_at,
                    "status": l.status
                } for l in logs])
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name=f"{export_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
def smart_dashboard_ui(session):
    """Phase 3: Action-focused dashboard showing ONLY what matters today"""
    st.subheader("🎯 Today's Action Plan")
    
    engine = EmailEngine(session)
    items = engine.get_actionable_items()
    
    # ✅ SECTION 1: FOLLOW-UPS DUE TODAY (Highest priority)
    if items["due_today"]:
        st.error(f"⏰ {len(items['due_today'])} FOLLOW-UPS DUE TODAY")
        for contact in items["due_today"]:
            job = session.query(Job).get(contact.job_id) if contact.job_id else None
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 3, 2])
                
                with col1:
                    st.markdown(f"**{contact.name}**")
                    st.caption(f"{contact.company_name}")
                    if job:
                        st.caption(f"📎 {job.job_title}")
                
                with col2:
                    st.markdown(f"📧 Last contacted: {(datetime.now(timezone.utc) - contact.last_contacted).days} days ago")
                    templates = get_all_templates(session)
                    followup_templates = [t for t in templates if t.is_followup]
                    if followup_templates:
                        template = followup_templates[0]
                        preview_subject, _ = engine.format_template(template, contact, job)
                        st.caption(f"✏️ Preview: {preview_subject}")
                
                with col3:
                    # ONE-CLICK FOLLOW-UP + CALENDAR
                    if st.button("📨 Send & Schedule", key=f"today_{contact.id}", type="primary"):
                        account = get_active_email_account(session)
                        if account and followup_templates:
                            engine.connect_smtp(account.email_address)
                            success, msg, event = engine.send_email(contact, followup_templates[0], job)
                            engine.disconnect_smtp()
                            
                            if success:
                                st.success("✅ Sent!")
                                # Auto-download calendar event
                                st.session_state.download_event = event
                                st.rerun()
                        else:
                            st.error("Configure email account or templates first")
        
        st.markdown("---")
    
    # ✅ SECTION 2: RECENT REPLIES (Celebrate wins)
    if items["recent_replies"]:
        st.success(f"🎉 {len(items['recent_replies'])} Recent Replies")
        for contact in items["recent_replies"][:3]:  # Show top 3
            days_ago = (datetime.now(timezone.utc) - contact.reply_date).days
            st.markdown(f"✅ **{contact.name}** ({contact.company_name}) replied {days_ago} days ago")
        if len(items["recent_replies"]) > 3:
            st.caption(f"... and {len(items['recent_replies']) - 3} more")
        st.markdown("---")
    
    # ✅ SECTION 3: STALE CONTACTS (Nudge to action)
    if items["stale"]:
        st.warning(f"⚠️ {len(items['stale'])} Stale Contacts (>14 days)")
        for contact in items["stale"][:3]:
            days = (datetime.now(timezone.utc) - contact.last_contacted).days
            st.markdown(f"⏳ **{contact.name}** - {days} days since last contact")
        st.markdown("---")
    
    # ✅ CALENDAR DOWNLOAD TRIGGER (from send action)
    if "download_event" in st.session_state and st.session_state.download_event:
        st.balloons()
        calendar_download_button(st.session_state.download_event, "✅ Download Calendar Reminder")
        del st.session_state.download_event
    
    # ✅ QUICK ADD SECTION
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Add Job", use_container_width=True):
            st.session_state.show_add_job = True
            st.rerun()
    
    with col2:
        if st.button("👤 Add Contact", use_container_width=True):
            st.session_state.show_add_contact = True
            st.rerun()
    
    with col3:
        if st.button("📧 Send Bulk", use_container_width=True):
            st.session_state.show_bulk_send = True
            st.rerun()