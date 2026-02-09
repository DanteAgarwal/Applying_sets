"""
Enhanced Outreach System - Personalized Bulk Emails & Quality Focus
✅ Per-contact personalization in bulk | ✅ Dynamic variable injection | ✅ Enhanced template variables
"""
import streamlit as st
import pandas as pd
import re
import json
import base64
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
import time
from src.model import Contact, EmailTemplate, EmailAccount
from src.email_engine import EmailEngine, get_active_email_account, test_smtp_connection
from src.database import (
    add_email_template, get_all_templates, update_template, delete_template,
    fetch_all_contacts, import_contacts_csv
)
from src.calendar_integration import create_followup_event
from src.security import SimpleCredentialStore

# --- ENHANCED HELPER: TEMPLATE VARIABLE VALIDATION ---
ALLOWED_VARS = {
    # Core contact/job details
    "{name}", "{company}", "{job_title}", "{first_name}", "{your_name}", "{today}",
    # Enhanced personalization variables
    "{hr_name}",           # Specific HR/Recruiter name (e.g., Sarah)
    "{hr_first_name}",     # First name of HR/Recruiter (e.g., Sarah -> Sarah)
    "{hr_role}",           # Role of the contact (e.g., HR Manager, Technical Recruiter)
    "{phone}",             # Contact phone number
    "{linkedin}",          # LinkedIn profile URL
    # Contextual details for quality
    "{referral_source}",   # How you found the contact (e.g., LinkedIn, Referral, Job Post)
    "{mutual_connection}", # Name of mutual connection (if applicable)
    "{recent_news}",       # Brief mention of company news (optional)
    "{specific_skill}",    # Skill mentioned in job description you highlight
    "{personal_note}",     # A unique note for this specific email
}
VAR_PATTERN = re.compile(r"{[^}]+}")

def validate_template_variables(text):
    """Check if all variables in text are allowed"""
    found = set(VAR_PATTERN.findall(text))
    return found.issubset(ALLOWED_VARS), found - ALLOWED_VARS

def get_default_templates():
    """Centralized default templates definition with enhanced variables"""
    return [
        ("Cold Outreach", "Re: {job_title} at {company}",
         "Dear {hr_first_name},\n\nI hope this message finds you well. My name is {your_name}, and I recently came across the {job_title} position at {company} via {referral_source}. \n\nI am particularly drawn to {specific_skill} aspect of the role and believe my background aligns well. I have attached my resume for your review.\n\nThank you for your time and consideration.\n\nBest regards,\n{your_name}",
         False, 0),
        ("Follow-up #1 (3 days)", "Following up on {job_title} application",
         "Hi {hr_first_name},\n\nI hope you are having a great week. I wanted to follow up on my application for the {job_title} position at {company} that I submitted a few days ago. I remain very enthusiastic about the opportunity.\n\nI would appreciate any updates you might have on the process.\n\nThanks again for your time.\n\nBest regards,\n{your_name}",
         True, 3),
        ("Follow-up #2 (4 days)", "Checking in on {job_title} status",
         "Hello {hr_first_name},\n\nI hope this email finds you well. I am writing to gently follow up on the {job_title} role at {company}. It's been a week since my initial application, and I wanted to ensure my materials were received.\n\nI am still very interested in the position and would welcome the chance to discuss my qualifications further.\n\nThank you for your consideration.\n\nBest regards,\n{your_name}",
         True, 4)
    ]

# --- TAB 1: EMAIL SETUP (UNCHANGED) ---
def email_setup_ui(session):
    """Windows-safe email setup with explicit credential storage"""
    st.markdown("### ⚙️ EMAIL SETUP")
    account = get_active_email_account(session)
    if account:
        st.success(f"✅ **Active Account**: {account.email_address}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔌 Disconnect Account", use_container_width=True):
                account.is_active = False
                session.commit()
                # Delete credentials
                cred_store = SimpleCredentialStore()
                cred_store.delete(account.email_address)
                st.rerun()
        with col2:
            if st.button("🔐 Reconnect Account", use_container_width=True):
                st.session_state.show_reconnect = True

        if st.session_state.get("show_reconnect"):
            st.markdown("---")
            st.markdown("### 🔁 Reconnect Account")
            with st.form("reconnect_form"):
                password = st.text_input("🔑 App Password", type="password", placeholder="16-character App Password")
                if st.form_submit_button("✅ Reconnect", type="primary"):
                    if password.strip():
                        cred_store = SimpleCredentialStore()
                        cred_store.save(account.email_address, password.strip())
                        st.success("✅ Reconnected successfully!")
                        del st.session_state.show_reconnect
                        st.rerun()
                    else:
                        st.error("❌ Password required")
        st.markdown("---")

    with st.form("setup_form", clear_on_submit=True):
        st.markdown("#### Connect New Account")
        email = st.text_input("📧 Email Address*", placeholder="you@gmail.com")
        password = st.text_input("🔑 App Password*", type="password", placeholder="16-character Gmail App Password")
        smtp_server = st.text_input("🌐 SMTP Server", value="smtp.gmail.com")
        smtp_port = st.number_input("🔌 Port", value=587, min_value=1, max_value=65535)

        st.info("💡 **Gmail Users**: Enable 2FA → Generate App Password (16 chars) → Use here")

        if st.form_submit_button("✅ CONNECT ACCOUNT", type="primary", use_container_width=True):
            if not email.strip() or not password.strip():
                st.error("❌ Email and password are required")
                return

            with st.spinner("Testing connection..."):
                try:
                    # Test connection FIRST before saving
                    success, msg = test_smtp_connection(email.strip(), password.strip(), smtp_server, smtp_port)
                    if success:
                        # Save account metadata to DB
                        engine = EmailEngine(session)
                        engine.setup_account(email.strip(), password.strip(), smtp_server, smtp_port)

                        # Save credentials to Windows-safe store
                        cred_store = SimpleCredentialStore()
                        cred_store.save(email.strip(), password.strip())

                        st.success("✅ Connected successfully! Credentials saved securely.")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ Connection failed: {msg}")
                        st.info("🔧 Fix: For Gmail, use App Password (not your regular password)")
                except Exception as e:
                    st.error(f"❌ Setup error: {str(e)}")
                    st.info("💡 Windows users: If you see 'chmod' errors, this simplified credential store fixes it")

# --- TAB 2: TEMPLATES (ENHANCED VARIABLES) ---
def template_manager_ui(session):
    """Simple template management with enhanced variables"""
    st.markdown("### ✉️ EMAIL TEMPLATES")
    # ✅ FIX PROBLEM 1: Reload templates AFTER auto-create
    templates = get_all_templates(session)
    if not templates:
        with st.spinner("Creating default templates..."):
            for name, subj, body, is_fu, days in get_default_templates():
                add_email_template(session, name, subj, body, is_fu, days)
        templates = get_all_templates(session)  # RELOAD AFTER CREATION
        st.success("✅ 3-template sequence created!")
        st.info("💡 Sequence: Cold → 3 days → 4 days (total 7 days)")

    # Show templates list
    st.markdown("#### Your Templates")
    for t in sorted(templates, key=lambda x: (not x.is_followup, x.days_after_previous)):
        badge = "🥇 FIRST (3d)" if t.is_followup and t.days_after_previous == 3 else \
                "🥈 SECOND (4d)" if t.is_followup and t.days_after_previous == 4 else "📧 COLD"

        with st.expander(f"{badge} **{t.name}**", expanded=False):
            # ✅ FIX PROBLEM 5: SHOW SUBJECT + BODY PREVIEW
            st.markdown(f"**Subject:** `{t.subject}`")
            st.caption(f"Type: {'Follow-up' if t.is_followup else 'Cold'} • Delay: {t.days_after_previous} days")
            st.text_area("Body Preview", t.body[:150] + "...", height=100, disabled=True, key=f"body_prev_{t.id}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Edit", key=f"edit_{t.id}", use_container_width=True):
                    st.session_state.editing_template = t.id
                    st.rerun()
            with col2:
                if st.button("🗑️ Delete", key=f"del_{t.id}", use_container_width=True):
                    delete_template(session, t.id)
                    st.success(f"✅ Deleted '{t.name}'")
                    st.rerun()

    # Create new template section
    st.markdown("---")
    st.markdown("#### ➕ Create New Template")
    with st.form("new_template", clear_on_submit=True):
        name = st.text_input("Template Name*", placeholder="e.g., 'Networking Follow-up'")
        subject = st.text_input("Subject Line*", placeholder="Re: {job_title} at {company}")
        body = st.text_area("Email Body*", height=150,
                          placeholder="Dear {hr_first_name},\n\nUse variables: {name}, {company}, {job_title}, {hr_name}, {hr_role}, {specific_skill}, {referral_source}, {your_name}, {today}")
        is_fu = st.checkbox("🔄 This is a follow-up template")
        days = st.number_input("Days after previous email", value=3 if is_fu else 0, min_value=0, disabled=not is_fu)

        if st.form_submit_button("✅ CREATE TEMPLATE", type="primary", use_container_width=True):
            # ✅ FIX PROBLEM 6: DUPLICATE NAME CHECK
            if any(t.name.strip().lower() == name.strip().lower() for t in templates):
                st.error("❌ Template name already exists. Choose a different name.")
            elif not name.strip() or not subject.strip() or not body.strip():
                st.error("❌ All fields marked with * are required")
            else:
                # ✅ FIX PROBLEM 3: VARIABLE VALIDATION
                valid_subj, bad_subj = validate_template_variables(subject)
                valid_body, bad_body = validate_template_variables(body)
                bad_vars = bad_subj | bad_body

                if not (valid_subj and valid_body):
                    st.error(f"❌ Invalid variables: {', '.join(bad_vars)}\n✅ Allowed: {', '.join(ALLOWED_VARS)}")
                else:
                    add_email_template(session, name.strip(), subject.strip(), body.strip(), is_fu, days)
                    st.success(f"✅ Template '{name}' created!")
                    st.balloons()
                    st.rerun()

# --- TAB 3: SEND EMAILS (PERSONALIZED BULK FOCUS) ---
def send_bulk_email_ui(session):
    """Refactored send interface focusing on personalized bulk emails"""
    st.markdown("### 🚀 SEND PERSONALIZED BULK EMAILS")
    # ✅ AUTO-CREATE TEMPLATES IF NONE EXIST
    templates = get_all_templates(session)
    if not templates:
        with st.spinner("Creating default templates..."):
            for name, subj, body, is_fu, days in get_default_templates():
                add_email_template(session, name, subj, body, is_fu, days)
        templates = get_all_templates(session)
        st.info("✅ Default templates created. Select a template below to continue.")

    # Prerequisites check
    account = get_active_email_account(session)
    contacts = fetch_all_contacts(session)

    if not account:
        st.error("❌ **Email account not configured**")
        st.info("💡 Go to SETUP tab to connect your email first")
        if st.button("⚙️ Go to SETUP Tab", type="primary"):
            st.session_state.page = "OUTREACH"
            st.rerun()
        return

    # ✅ CRITICAL FIX: VERIFY CREDENTIALS EXIST BEFORE SENDING
    cred_store = SimpleCredentialStore()
    creds = cred_store.load(account.email_address)
    if not creds:
        st.error(f"❌ **Credentials missing for {account.email_address}**")
        st.warning("🔐 Your account is configured but credentials were not found.")
        st.info("""
        🔧 **Fix this in 2 steps:**
        1. Go to SETUP tab → Click "🔌 Disconnect Account"
        2. Reconnect with your App Password
        """)
        if st.button("⚙️ Go to SETUP Tab", type="primary"):
            st.session_state.page = "OUTREACH"
            st.rerun()
        return

    if contacts.empty:
        st.warning("📭 **No contacts available**")
        st.info("💡 Add contacts in CONTACTS tab or import from CSV")
        return

    # Show sequence status
    followups = [t for t in templates if t.is_followup]
    if len(followups) >= 2:
        st.success(f"✅ Complete sequence: Cold → {followups[0].days_after_previous}d → {followups[1].days_after_previous}d")
    else:
        st.warning("⚠️ Incomplete sequence - create 2 follow-up templates (3d + 4d) for auto-calendar")

    # Contact selection
    st.markdown("#### 👥 Select Recipients")
    contact_opts = contacts.apply(lambda x: f"{x['name']} • {x['company_name']}", axis=1).tolist()
    selected_indices = st.multiselect(
        "Search contacts ",
        options=range(len(contact_opts)),
        format_func=lambda x: contact_opts[x],
        placeholder="Type to search...",
        help="Select multiple contacts for bulk send. Personalization details will be applied to all."
    )

    if not selected_indices:
        st.info("👆 Please select at least one contact to proceed.")
        return

    selected_contact_ids = contacts.iloc[selected_indices]['id'].tolist()
    selected_contacts = [session.query(Contact).get(cid) for cid in selected_contact_ids]

    st.success(f"Selected **{len(selected_indices)}** contacts")

    # Template selection
    st.markdown("#### ✉️ Select Template")
    template_opts = [f"{'🔄 ' if t.is_followup else '📧 '} {t.name}" for t in templates]
    template_idx = st.selectbox("Template", range(len(template_opts)), format_func=lambda x: template_opts[x])
    selected_template = templates[template_idx]

    # COMPOSE SECTION - Collect DYNAMIC PERSONALIZATION VALUES for ALL selected contacts
    st.markdown("#### ✍️ Personalize for Selected Contacts")
    st.caption("Fill in details that apply to all selected contacts for this campaign.")

    # 1. Your Name
    stored_name = cred_store.load_profile()
    your_name_input = st.text_input("👤 Your Full Name*", value=stored_name or "", placeholder="e.g., 'Alex Johnson'")
    if your_name_input.strip() and your_name_input != stored_name:
        try:
            cred_store.save_profile(your_name_input.strip())
            stored_name = your_name_input.strip()
        except Exception:
            pass # Silently fail if profile saving fails

    # 2. Job Title (Context for the email)
    job_title_input = st.text_input("📌 Job Title*", value="", placeholder="e.g., 'Senior Software Engineer'")
    company_name_input = st.text_input("🏢 Campaign Company Name*", value="", placeholder="e.g., 'Google' (Overrides individual contact's company if provided)") # Allows overriding company for all

    # 3. Enhanced Personalization Details (Applied to ALL)
    col1, col2 = st.columns(2)
    with col1:
        # HR Role (Assumed same for all, or user can refine per contact later if needed)
        hr_role_input = st.text_input("💼 Common HR/Recruiter Role", value="", placeholder="e.g., 'Technical Recruiter'")
    with col2:
        # Referral Source (Common for campaign)
        referral_source_input = st.text_input("🔍 How did you find these contacts?", value="", placeholder="e.g., 'LinkedIn Post', 'Job Board'")

    # 4. Specific Skill Mentioned (Common highlight)
    specific_skill_input = st.text_input("🎯 Common Skill to Highlight", value="", placeholder="e.g., 'React expertise', 'Machine Learning background'")

    # 5. Recent News (Optional, common for campaign)
    recent_news_input = st.text_area("📢 Recent Company News (optional)", value="", placeholder="e.g., 'Congrats on the new product launch!'")

    # Optional resume attachment + default resume option
    st.markdown("#### 📎 Attach Resume (optional)")
    col_a, col_b = st.columns([3,1])
    with col_a:
        uploaded_resume = st.file_uploader("Attach resume (optional)", type=["pdf", "doc", "docx"], key="resume_upload")
    with col_b:
        use_default_resume = st.checkbox("Use default", value=False)

    # Show info about saved default resume
    default_resume = cred_store.load_default_resume()
    if default_resume:
        st.caption(f"Default resume: {default_resume[0]}")

    save_default = False
    if uploaded_resume:
        save_default = st.checkbox("Save uploaded file as default resume", value=False)

    # Rate limit control (seconds between sends)
    rate_limit_seconds = st.number_input("Send delay (seconds) between emails", value=3, min_value=0, max_value=3600, step=1, key="rate_limit_seconds")
    est_time = len(selected_indices) * rate_limit_seconds
    st.caption(f"Estimated time: ~{est_time} seconds ({len(selected_indices)} recipients × {rate_limit_seconds}s)")

    # Dry-run preview button (shows preview for first selected contact)
    if st.button("🔍 Dry run (preview first contact)", key="dry_run"):
        if not job_title_input or not your_name_input:
            st.error("❌ Please fill in required fields (Your Name, Job Title) for dry run")
        else:
            # Get the first selected contact for preview
            first_contact = selected_contacts[0]
            preview_context = {
                "{name}": first_contact.name or "Hiring Team",
                "{company}": company_name_input if company_name_input else first_contact.company_name,
                "{job_title}": job_title_input,
                "{first_name}": first_contact.name.split()[0] if first_contact.name else "there",
                "{your_name}": your_name_input,
                "{today}": datetime.now(timezone.utc).strftime("%B %d, %Y"),
                # Enhanced variables for this specific email
                "{hr_name}": first_contact.name, # Use contact's name as default HR name
                "{hr_first_name}": first_contact.name.split()[0] if first_contact.name else "there",
                "{hr_role}": hr_role_input or first_contact.contact_type or "hiring manager",
                "{phone}": first_contact.phone or "[phone not available]",
                "{linkedin}": first_contact.linkedin_url or "[LinkedIn not provided]",
                "{referral_source}": referral_source_input,
                "{mutual_connection}": "",
                "{recent_news}": recent_news_input,
                "{specific_skill}": specific_skill_input,
                "{personal_note}": f"This is a sample for {first_contact.name}. Actual emails will be personalized.",
            }

            preview_subject = selected_template.subject
            preview_body = selected_template.body

            for placeholder, value in preview_context.items():
                preview_subject = preview_subject.replace(placeholder, value)
                preview_body = preview_body.replace(placeholder, value)

            with st.expander(f"📧 Preview Email for {first_contact.name}", expanded=True):
                st.markdown(f"**From:** {your_name_input} <{account.email_address}>")
                st.markdown(f"**To:** {first_contact.name} <{first_contact.email}>")
                st.markdown(f"**Subject:** {preview_subject}")
                st.text_area("Body:", preview_body, height=250, disabled=True, key="preview_body")


    # Send button - Focuses on personalized bulk send
    st.markdown(" ")
    if st.button("🚀 SEND PERSONALIZED BULK EMAIL", type="primary", use_container_width=True, key="send_btn"):
        # Validation for required fields
        if not job_title_input.strip():
            st.error("❌ Job Title is required")
            return
        if not your_name_input.strip():
            st.error("❌ Your Name is required")
            return

        with st.spinner(f"Sending personalized emails to {len(selected_indices)} contacts..."):
            try:
                engine = EmailEngine(session)

                # Prepare attachments
                attachments = None
                if use_default_resume:
                    dr = cred_store.load_default_resume()
                    if dr:
                        attachments = [(dr[0], dr[1], dr[2])]
                if not attachments and uploaded_resume:
                    try:
                        content = uploaded_resume.read()
                    except Exception:
                        uploaded_resume.seek(0)
                        content = uploaded_resume.read()
                    attachments = [(uploaded_resume.name, content, getattr(uploaded_resume, "type", "application/octet-stream"))]

                # Save uploaded resume as default if user requested
                if uploaded_resume and save_default:
                    try:
                        content = content if 'content' in locals() else uploaded_resume.read()
                        cred_store.save_default_resume(uploaded_resume.name, content, getattr(uploaded_resume, "type", "application/octet-stream"))
                        st.info("Saved default resume")
                    except Exception:
                        st.warning("Could not save default resume")

                # Create a temporary Job-like object with user inputs (or None if not applicable)
                class TempJob:
                    def __init__(self, job_title, company_name):
                        self.job_title = job_title
                        self.company_name = company_name
                        self.id = None # Not linked to DB job necessarily

                temp_job = TempJob(job_title_input.strip(), company_name_input.strip()) if job_title_input.strip() else None

                # Define the DEFAULT personalization context for this BULK campaign
                default_personalization_context = {
                    "{hr_role}": hr_role_input.strip(),
                    "{referral_source}": referral_source_input.strip(),
                    "{mutual_connection}": "", # Placeholder for future enhancement
                    "{recent_news}": recent_news_input.strip(),
                    "{specific_skill}": specific_skill_input.strip(),
                    # Note: {hr_name} and {personal_note} will be defined per contact below
                }

                results = {"sent": 0, "failed": 0, "errors": []}

                # Loop through each selected contact and send personalized email
                for i, contact in enumerate(selected_contacts):
                    # Build personalization context for THIS SPECIFIC contact
                    # Start with the default context
                    personalization_context = default_personalization_context.copy()
                    # Add contact-specific details
                    personalization_context.update({
                        "{hr_name}": contact.name.strip(), # Use contact's actual name
                        "{hr_first_name}": contact.name.strip().split()[0], # Use contact's first name
                        # Add any other contact-specific logic here if needed
                        "{personal_note}": f"This email is tailored for {contact.name} at {contact.company_name}.", # Example unique note
                    })

                    # Determine company for this specific contact (override from UI or use contact's)
                    effective_company_name = company_name_input.strip() if company_name_input.strip() else contact.company_name

                    # Create a temporary job object for this specific contact iteration
                    temp_job_for_contact = TempJob(job_title_input.strip(), effective_company_name)

                    success, message, calendar_event = engine.send_personalized_email(
                        contact=contact,
                        template=selected_template,
                        job=temp_job_for_contact, # Use the contact-specific job object
                        attachments=attachments,
                        your_name=your_name_input.strip(),
                        personalization_context=personalization_context # Pass the contact-specific context
                    )

                    if success:
                        results["sent"] += 1
                        if calendar_event:
                            st.info(f"📅 Follow-up event created for {contact.name}: {calendar_event.summary}", icon="📅")
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"{contact.name} ({contact.email}): {message}")

                    # Rate limiting between sends
                    if i < len(selected_contacts) - 1:
                        time.sleep(rate_limit_seconds)

                # Show final results
                if results["sent"] > 0:
                    st.success(f"✅ **Successfully sent {results['sent']} emails!**")
                if results["failed"] > 0:
                    st.error(f"❌ **{results['failed']} emails failed.**")
                    with st.expander("📋 Error Details"):
                        for err in results["errors"]:
                            st.error(err)

                # AUTO-CALENDAR for cold emails (only if at least one was sent)
                if results["sent"] > 0 and not selected_template.is_followup and len(followups) >= 2:
                    st.markdown("---")
                    st.markdown("### 📅 AUTO-CALENDAR GENERATED ")

                    # Generate events for contacts that were successfully sent to
                    day3_events, day7_events = [], []
                    for contact in selected_contacts[:results["sent"]]: # Only generate for successfully sent ones
                        day3_events.append(create_followup_event(contact.name, contact.company_name, 3))
                        day7_events.append(create_followup_event(contact.name, contact.company_name, 7))

                    # Combine events helper
                    def combine_ics(events):
                        ics = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//JobTrack Pro//Calendar//EN\r\nCALSCALE:GREGORIAN\r\n"
                        for e in events:
                            e_ics = e.to_ics()
                            lines = e_ics.split("\r\n")
                            in_event = False
                            for line in lines:
                                if line.startswith("BEGIN:VEVENT"):
                                    in_event = True
                                if in_event:
                                    ics += line + "\r\n"
                                if line.startswith("END:VEVENT"):
                                    in_event = False
                        return ics + "END:VCALENDAR"

                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📥 Day 3 Reminders (.ics)",
                            combine_ics(day3_events),
                            f"day3_campaign_{datetime.now().strftime('%Y%m%d')}.ics",
                            "text/calendar",
                            use_container_width=True,
                            type="primary"
                        )
                    with col2:
                        st.download_button(
                            "📥 Day 7 Reminders (.ics)",
                            combine_ics(day7_events),
                            f"day7_campaign_{datetime.now().strftime('%Y%m%d')}.ics",
                            "text/calendar",
                            use_container_width=True,
                            type="primary"
                        )
                    st.info("💡 Import BOTH files to Google/Outlook/Apple Calendar for auto-reminders on Day 3 and Day 7")

            except Exception as e:
                st.error(f"❌ Send failed: {str(e)}")
                st.info("🔧 Check: Email configured? Templates exist? Contacts have valid emails?")

# --- TAB 4: IMPORT/EXPORT (MINIMAL - UNCHANGED) ---
def import_export_ui(session):
    """Simple, reliable import/export"""
    st.markdown("### 📥 IMPORT / EXPORT")
    tab1, tab2 = st.tabs(["📤 Import", "📥 Export"])

    with tab1:
        st.markdown("#### Import Contacts CSV")
        st.caption("Required columns: `name`, `email`, `company_name`")
        uploaded = st.file_uploader("Upload CSV file", type=["csv"], key="csv_upload")
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                st.write(f"Preview ({len(df)} rows):")
                st.dataframe(df.head(), use_container_width=True)

                if st.button("✅ Import Contacts", type="primary", use_container_width=True):
                    with st.spinner("Importing..."):
                        success, errors = import_contacts_csv(session, df)
                    if errors:
                        st.warning(f"✅ Imported {success} | ⚠️ {len(errors)} errors")
                    else:
                        st.success(f"✅ Successfully imported {success} contacts!")
                        st.balloons()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Tip: Save CSV as UTF-8 format")

    with tab2:
        st.markdown("#### Export Data")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📧 Export Contacts", use_container_width=True):
                df = fetch_all_contacts(session)
                st.download_button(
                    "📥 Download CSV",
                    df.to_csv(index=False),
                    "contacts.csv",
                    "text/csv",
                    use_container_width=True
                )
        with col2:
            if st.button("📨 Export Email Logs", use_container_width=True):
                from src.database import get_email_logs
                logs = get_email_logs(session, limit=10000)
                if logs:
                    df = pd.DataFrame([{
                        "Date": l.sent_at.strftime('%Y-%m-%d %H:%M'),
                        "Contact": session.query(Contact).get(l.contact_id).name if l.contact_id else "Unknown",
                        "Subject": l.subject,
                        "Status": l.status
                    } for l in logs])
                    st.download_button(
                        "📥 Download CSV",
                        df.to_csv(index=False),
                        "email_logs.csv",
                        "text/csv",
                        use_container_width=True
                    )
                else:
                    st.info("📭 No email logs yet")

# --- BACKWARD COMPATIBILITY (CRITICAL FOR YOUR MAIN APP) ---
def send_email_ui(session):
    """Alias for main app compatibility - now focuses on personalized bulk emails"""
    send_bulk_email_ui(session)