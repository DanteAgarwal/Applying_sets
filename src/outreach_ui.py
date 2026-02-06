"""
Smart Outreach UI - Rule-based, efficient, and user-friendly
Features: Contextual guidance, smart defaults, validation rules, progress tracking
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import time

from src.model import Contact, EmailTemplate, Job
from src.email_engine import EmailEngine, get_active_email_account, test_smtp_connection
from src.database import (
    add_contact, fetch_all_contacts, update_contact, delete_contact,
    add_email_template, get_all_templates, update_template, delete_template,
    get_email_logs, get_followup_candidates, import_contacts_csv, import_jobs_csv
)
from src.security import CredentialManager

# =====================================================
# SMART VALIDATION RULES
# =====================================================

def validate_email_setup(email, password, smtp_server, smtp_port):
    """Rule-based validation for email setup"""
    rules = [
        (bool(email.strip()), "Email address is required"),
        (bool(password.strip()), "App password is required"),
        ("@" in email and "." in email.split("@")[-1], "Invalid email format"),
        (smtp_port in [465, 587, 25], f"Uncommon SMTP port: {smtp_port}. Standard ports are 465 (SSL) or 587 (TLS)"),
        (len(password) >= 16, "App passwords are typically 16+ characters")
    ]
    return all(rule[0] for rule in rules), [msg for valid, msg in rules if not valid]

def validate_campaign(selected_contacts, template, account):
    """Rule-based validation before sending"""
    rules = [
        (account is not None, "⚠️ Email account not configured. Go to SETUP tab first."),
        (len(selected_contacts) > 0, "⚠️ No contacts selected. Select at least one recipient."),
        (template is not None, "⚠️ No template selected. Choose an email template."),
        (len(selected_contacts) <= 50, f"⚠️ Too many contacts ({len(selected_contacts)}). Max 50 per campaign to avoid spam flags."),
        (all(c.get('email') for c in selected_contacts), "⚠️ Some contacts missing email addresses. Clean your contact list first.")
    ]
    return all(rule[0] for rule in rules), [msg for valid, msg in rules if not valid]

def get_smart_template_suggestion(contact, templates):
    """Rule-based template selection"""
    if not contact.last_contacted:
        return next((t for t in templates if "cold" in t.name.lower()), templates[0])
    
    days_since = (datetime.now(timezone.utc) - contact.last_contacted).days
    if days_since >= 14:
        return next((t for t in templates if "follow" in t.name.lower() and "2" in t.name.lower()), 
                   next((t for t in templates if t.is_followup), templates[0]))
    elif days_since >= 7:
        return next((t for t in templates if "follow" in t.name.lower() and "1" in t.name.lower()), 
                   next((t for t in templates if t.is_followup), templates[0]))
    return templates[0]

# =====================================================
# PROVIDER AUTO-CONFIG
# =====================================================

SMTP_CONFIGS = {
    "Gmail": {"server": "smtp.gmail.com", "port": 587, "help": "Use App Password (16 chars) from Google Account settings"},
    "Outlook/Hotmail": {"server": "smtp-mail.outlook.com", "port": 587, "help": "Use your Microsoft account password"},
    "Yahoo": {"server": "smtp.mail.yahoo.com", "port": 587, "help": "Use App Password from Yahoo Account Security"},
    "Custom": {"server": "", "port": 587, "help": "Enter your SMTP server details"}
}

def email_setup_ui(session):
    """Smart email setup with provider presets and validation"""
    st.subheader("📧 Email Account Setup")
    
    # Current account status
    account = get_active_email_account(session)
    if account:
        st.success(f"✅ **Active**: {account.email_address} | {account.smtp_server}:{account.smtp_port}")
        if st.button("🔌 Disconnect Account", key="disconnect_email"):
            account.is_active = False
            session.commit()
            st.rerun()
        st.markdown("---")
    
    # Smart setup form
    st.markdown("### 🔧 Configure Email Account")
    
    col1, col2 = st.columns(2)
    with col1:
        provider = st.selectbox("📧 Email Provider", list(SMTP_CONFIGS.keys()), key="smtp_provider")
    with col2:
        email = st.text_input("✉️ Email Address", placeholder="you@gmail.com", key="setup_email")
    
    # Auto-fill SMTP settings based on provider
    config = SMTP_CONFIGS[provider]
    smtp_server = st.text_input("🌐 SMTP Server", value=config["server"], key="smtp_server")
    smtp_port = st.number_input("🔌 SMTP Port", value=config["port"], min_value=1, max_value=65535, key="smtp_port")
    
    st.info(f"💡 **{provider} Tip**: {config['help']}")
    
    app_password = st.text_input("🔑 App Password", type="password", 
                                placeholder="16-character App Password" if provider == "Gmail" else "Your email password",
                                key="app_password")
    
    # Validation and actions
    col1, col2, col3 = st.columns(3)
    with col1:
        test_btn = st.button("🧪 Test Connection", use_container_width=True, type="secondary")
    with col2:
        save_btn = st.button("💾 Save & Activate", use_container_width=True, type="primary")
    with col3:
        st.caption(f"Last tested: {account.updated_at.strftime('%H:%M')}" if account else "Not tested")
    
    if test_btn or save_btn:
        is_valid, errors = validate_email_setup(email, app_password, smtp_server, smtp_port)
        
        if not is_valid:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            with st.spinner("Testing connection..."):
                success, message = test_smtp_connection(email, app_password, smtp_server, smtp_port)
            
            if success:
                st.success(f"✅ {message}")
                if save_btn:
                    engine = EmailEngine(session)
                    success, msg = engine.setup_account(email, app_password, smtp_server, smtp_port)
                    if success:
                        st.balloons()
                        st.success("🎉 Account activated! You can now send emails.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Setup failed: {msg}")
            else:
                st.error(f"❌ Connection failed: {message}")
                st.info("💡 Common fixes:\n- For Gmail: Enable 2FA and generate an App Password\n- Check firewall settings\n- Verify SMTP server/port")

# =====================================================
# TEMPLATE MANAGEMENT WITH SMART PREVIEWS
# =====================================================

def template_manager_ui(session):
    """Smart template management with validation and previews"""
    st.subheader("✉️ Email Templates")
    
    # Auto-create defaults if none exist
    templates = get_all_templates(session)
    if not templates:
        with st.spinner("Creating smart default templates..."):
            # [Template creation code - kept concise]
            default_templates = [
                ("Cold Outreach", "Interest in {job_title} at {company}", """Dear {name},\n\nI'm excited about the {job_title} role at {company}. With my experience in [relevant skill], I believe I'd be a strong fit.\n\n[Your value proposition]\n\nBest regards,\n{your_name}""", False, 0),
                ("Follow-up #1", "Following up: {job_title} at {company}", """Hi {name},\n\nI wanted to follow up on my application for the {job_title} position. I remain very interested in this opportunity at {company}.\n\n[Add specific detail about role/company]\n\nThank you for your time!\n\nBest regards,\n{your_name}""", True, 7),
                ("Follow-up #2", "Re: {job_title} Opportunity", """Hi {name},\n\nI hope you're having a productive week. I'm still very interested in the {job_title} role and would welcome the chance to discuss how I can contribute to {company}.\n\n[Add new insight or question]\n\nBest regards,\n{your_name}""", True, 7)
            ]
            for name, subj, body, is_fu, days in default_templates:
                add_email_template(session, name, subj, body, is_fu, days)
            st.success("✅ Smart defaults created! Optimized for response rates.")
            st.rerun()
    
    # Template stats
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Templates", len(templates))
    col2.metric("Follow-up Templates", sum(1 for t in templates if t.is_followup))
    col3.metric("Avg. Length", f"{sum(len(t.body) for t in templates)//len(templates)} chars")
    
    # Template table with actions
    if templates:
        st.markdown("### 📋 Your Templates")
        for idx, template in enumerate(templates):
            with st.expander(f"{'🔄' if template.is_followup else '📧'} **{template.name}** | {template.subject[:40]}...", expanded=False):
                # Template details
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.caption(f"{'Follow-up' if template.is_followup else 'Cold'} • {template.days_after_previous}d delay • Created {template.created_at.strftime('%b %d')}")
                with col2:
                    if st.button("👁️ Preview", key=f"preview_{template.id}"):
                        st.session_state[f"show_preview_{template.id}"] = True
                with col3:
                    if st.button("🗑️ Delete", key=f"del_temp_{template.id}"):
                        st.session_state.confirm_delete = template.id
                
                # Preview modal
                if st.session_state.get(f"show_preview_{template.id}"):
                    st.markdown("### 📧 Preview with Sample Data")
                    sample = {
                        'name': 'Alex Rivera',
                        'company_name': 'InnovateX',
                        'job_title': 'Senior Product Manager'
                    }
                    engine = EmailEngine(session)
                    contact_obj = type('obj', (object,), {
                        'name': sample['name'],
                        'company_name': sample['company_name'],
                        'email': 'alex@innovatex.com'
                    })()
                    job_obj = type('obj', (object,), {
                        'job_title': sample['job_title'],
                        'company_name': sample['company_name']
                    })()
                    subj, body = engine.format_template(template, contact_obj, job_obj)
                    
                    st.text_input("Subject", subj, disabled=True)
                    st.text_area("Body", body, height=200, disabled=True)
                    if st.button("CloseOperation", key=f"close_prev_{template.id}"):
                        st.session_state[f"show_preview_{template.id}"] = False
                        st.rerun()
                
                # Delete confirmation
                if st.session_state.get("confirm_delete") == template.id:
                    st.warning("⚠️ **Confirm deletion?** This cannot be undone.")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Yes, Delete", key=f"confirm_del_{template.id}"):
                            delete_template(session, template.id)
                            st.success(f"Deleted '{template.name}'")
                            del st.session_state.confirm_delete
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_del_{template.id}"):
                            del st.session_state.confirm_delete
                            st.rerun()
    
    # Create new template
    with st.expander("➕ Create New Template", expanded=False):
        with st.form("new_template", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Template Name*", placeholder="e.g., 'Networking Follow-up'")
                subject = st.text_input("Subject Line*", placeholder="Re: {job_title} at {company}")
                is_followup = st.checkbox("🔄 This is a follow-up template")
            with col2:
                days_after = st.number_input("Days After Previous Contact", 
                                            value=7 if is_followup else 0, 
                                            min_value=0,
                                            disabled=not is_followup)
                priority = st.select_slider("Priority", 
                                          options=["Low", "Medium", "High"],
                                          value="Medium")
            
            body = st.text_area("Email Body*", 
                               placeholder="Dear {name},\n\nI'm writing about...",
                               height=200,
                               help="Use variables: {name}, {company}, {job_title}, {first_name}, {your_name}, {today}")
            
            # Smart validation
            submitted = st.form_submit_button("✅ Create Template", type="primary", use_container_width=True)
            if submitted:
                if not name.strip() or not subject.strip() or not body.strip():
                    st.error("❌ All fields marked with * are required")
                elif len(body) < 50:
                    st.warning("⚠️ Email body is very short. Consider adding more personalization.")
                    if st.button("✅ Create Anyway"):
                        add_email_template(session, name, subject, body, is_followup, days_after)
                        st.success(f"✅ Template '{name}' created!")
                        st.rerun()
                else:
                    add_email_template(session, name, subject, body, is_followup, days_after)
                    st.success(f"✅ Template '{name}' created!")
                    st.balloons()
                    st.rerun()

# =====================================================
# SMART BULK SEND (Handles Single + Bulk)
# =====================================================

def send_bulk_email_ui(session):
    """Unified smart send interface with validation and progress tracking"""
    st.subheader("🚀 Smart Email Campaign")
    
    # Prerequisites check
    account = get_active_email_account(session)
    contacts_df = fetch_all_contacts(session)
    templates = get_all_templates(session)
    
    # Rule-based guidance
    if not account:
        st.error("❌ **Email account not configured**")
        st.info("💡 Go to SETUP tab to configure your email account first")
        st.stop()
    
    if contacts_df.empty:
        st.warning("📭 **No contacts available**")
        st.info("💡 Add contacts first in CONTACTS section or import from CSV")
        if st.button("➕ Add Contact Now"):
            st.session_state.page = "CONTACTS"
            st.rerun()
        st.stop()
    
    if not templates:
        st.error("❌ **No email templates available**")
        st.info("💡 Create templates in TEMPLATES tab first")
        if st.button("➕ Create Template Now"):
            st.session_state.page = "OUTREACH"
            st.session_state.outreach_subpage = "TEMPLATES"
            st.rerun()
        st.stop()
    
    # Smart contact selection
    st.markdown("### 👥 Select Recipients")
    
    # Auto-suggest candidates
    engine = EmailEngine(session)
    candidates = engine.get_followup_candidates(days_threshold=7)
    if candidates:
        st.success(f"🤖 **Smart Suggestion**: {len(candidates)} contacts need follow-up (last contacted 7+ days ago)")
        default_ids = [c.id for c in candidates[:10]]  # Auto-select top 10
    else:
        st.info("💡 No automatic suggestions. Select contacts manually below.")
        default_ids = []
    
    # Contact selector with search
    contact_options = contacts_df.apply(
        lambda x: f"{x['name']} • {x['company_name']} • {x['email']}", 
        axis=1
    ).tolist()
    
    selected_indices = st.multiselect(
        "Search and select contacts",
        options=range(len(contact_options)),
        default=[i for i, cid in enumerate(contacts_df['id']) if cid in default_ids],
        format_func=lambda x: contact_options[x],
        placeholder="Type to search contacts..."
    )
    
    selected_contacts = contacts_df.iloc[selected_indices].to_dict('records') if selected_indices else []
    
    # Template selection with smart suggestion
    st.markdown("### ✉️ Select Template")
    col1, col2 = st.columns(2)
    
    with col1:
        template_names = [f"{'🔄 ' if t.is_followup else '📧 '} {t.name}" for t in templates]
        selected_idx = st.selectbox(
            "Template",
            range(len(templates)),
            format_func=lambda x: template_names[x],
            index=0 if not candidates else 1  # Default to follow-up if candidates exist
        )
        selected_template = templates[selected_idx]
    
    with col2:
        st.caption("💡 **Smart Tip**")
        if candidates and selected_template.is_followup:
            st.success("✅ Perfect! Follow-up template selected for stale contacts")
        elif not candidates and not selected_template.is_followup:
            st.info("✅ Good choice for new outreach")
        elif candidates and not selected_template.is_followup:
            st.warning("⚠️ Consider using a follow-up template for these contacts")
        elif not candidates and selected_template.is_followup:
            st.warning("⚠️ This is a follow-up template. Use for existing contacts only")
    
    # Campaign settings with safety limits
    st.markdown("### ⚙️ Campaign Settings")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rate_limit = st.slider(
            "⏱️ Seconds between emails", 
            min_value=5, 
            max_value=60, 
            value=15,
            help="Prevents spam flags. Gmail recommends 10-15s between emails"
        )
    
    with col2:
        daily_cap = st.number_input(
            "📧 Daily send limit", 
            min_value=10, 
            max_value=100, 
            value=min(50, len(selected_contacts)),
            help="Stay under Gmail's 100/day limit for new accounts"
        )
    
    with col3:
        st.metric("Total Recipients", len(selected_contacts))
        if len(selected_contacts) > daily_cap:
            st.warning(f"⚠️ Exceeds daily limit! Only first {daily_cap} will send")
    
    # Validation before sending
    is_valid, errors = validate_campaign(selected_contacts, selected_template, account)
    if not is_valid:
        for error in errors:
            st.error(error)
        st.stop()
    
    # Campaign summary
    st.markdown("### 📊 Campaign Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Recipients", len(selected_contacts))
    col2.metric("Template", selected_template.name)
    col3.metric("Rate Limit", f"{rate_limit}s")
    col4.metric("Est. Duration", f"{len(selected_contacts) * rate_limit // 60} min")
    
    # Send button with confirmation
    st.markdown("")
    if st.button("🚀 LAUNCH CAMPAIGN", type="primary", use_container_width=True, key="launch_campaign"):
        if len(selected_contacts) > 20:
            st.warning(f"⚠️ **Large campaign detected** ({len(selected_contacts)} emails)")
            st.info("💡 Pro tip: For best deliverability, send campaigns in batches of 20")
            if not st.checkbox("✅ I understand the risks and want to proceed"):
                st.stop()
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        results_container = st.empty()
        
        results = {"sent": 0, "failed": 0, "errors": []}
        contact_ids = [c['id'] for c in selected_contacts[:daily_cap]]  # Respect daily cap
        
        # Initialize email engine
        engine = EmailEngine(session)
        engine.rate_limit_delay = rate_limit
        engine.daily_limit = daily_cap
        
        # Send emails with progress updates
        for i, contact_id in enumerate(contact_ids):
            progress = (i + 1) / len(contact_ids)
            progress_bar.progress(progress)
            
            contact = session.query(Contact).get(contact_id)
            job = session.query(Job).get(contact.job_id) if contact.job_id else None
            
            status_text.text(f"📤 Sending to {contact.name} ({i+1}/{len(contact_ids)})...")
            
            success, message, _ = engine.send_email(contact, selected_template, job)
            
            if success:
                results["sent"] += 1
                # Update contact status
                contact.needs_followup = False
                if selected_template.is_followup and selected_template.days_after_previous:
                    contact.followup_date = datetime.now(timezone.utc).date() + timedelta(days=selected_template.days_after_previous)
                session.commit()
            else:
                results["failed"] += 1
                results["errors"].append(f"{contact.name} ({contact.email}): {message}")
            
            # Rate limiting
            if i < len(contact_ids) - 1:
                time.sleep(rate_limit / 10)  # Small sleep for progress smoothness
        
        # Finalize
        progress_bar.progress(1.0)
        status_text.text("✅ Campaign completed!")
        
        # Results display
        with results_container.container():
            st.success(f"✅ **Campaign Complete!** Sent: {results['sent']} | Failed: {results['failed']}")
            
            if results["errors"]:
                with st.expander(f"⚠️ {len(results['errors'])} Failed Emails"):
                    for error in results["errors"][:10]:  # Show first 10
                        st.text(error)
                    if len(results["errors"]) > 10:
                        st.caption(f"... and {len(results['errors']) - 10} more")
            
            # Success actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📧 View Email Logs", use_container_width=True):
                    st.session_state.page = "ANALYTICS"
                    st.rerun()
            with col2:
                if st.button("🔄 New Campaign", use_container_width=True):
                    st.rerun()
            with col3:
                st.download_button(
                    "📥 Export Report",
                    data=f"Campaign Report\nSent: {results['sent']}\nFailed: {results['failed']}\n\nErrors:\n" + "\n".join(results["errors"]),
                    file_name=f"campaign_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    use_container_width=True
                )
        
        # Auto-close SMTP
        engine.disconnect_smtp()

# =====================================================
# IMPORT/EXPORT WITH VALIDATION
# =====================================================

def import_export_ui(session):
    """Smart import/export with validation and templates"""
    st.subheader("📥 Import / Export Data")
    
    tab1, tab2, tab3 = st.tabs(["📤 Import Contacts", "📤 Import Jobs", "📥 Export Data"])
    
    with tab1:
        st.markdown("### Import Contacts from CSV")
        st.info("✅ **Required columns**: `name`, `email`, `company_name`")
        st.caption("	Optional: `contact_type`, `phone`, `linkedin_url`")
        
        # Sample CSV download
        sample_df = pd.DataFrame({
            "name": ["John Doe", "Jane Smith"],
            "email": ["john@company.com", "jane@startup.io"],
            "company_name": ["TechCorp", "InnovateX"],
            "contact_type": ["Recruiter", "Hiring Manager"],
            "phone": ["+1234567890", ""],
            "linkedin_url": ["https://linkedin.com/in/johndoe", ""]
        })
        
        st.download_button(
            "📥 Download Sample CSV Template",
            sample_df.to_csv(index=False),
            file_name="contacts_template.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"], key="contacts_csv_upload")
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.write(f"Preview ({len(df)} rows):")
                st.dataframe(df.head(), use_container_width=True)
                
                # Validation
                required_cols = ["name", "email", "company_name"]
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                    st.stop()
                
                if df['email'].isnull().any() or (df['email'] == '').any():
                    st.warning("⚠️ Some emails are missing. These rows will be skipped.")
                
                if st.button("✅ Import Contacts", type="primary", use_container_width=True):
                    with st.spinner(f"Importing {len(df)} contacts..."):
                        success_count, errors = import_contacts_csv(session, df)
                    
                    if errors:
                        st.warning(f"✅ Imported {success_count} contacts | ⚠️ {len(errors)} errors")
                        with st.expander("View Errors"):
                            for err in errors[:10]:
                                st.text(err)
                            if len(errors) > 10:
                                st.caption(f"... and {len(errors)-10} more")
                    else:
                        st.success(f"✅ Successfully imported {success_count} contacts!")
                        st.balloons()
            except Exception as e:
                st.error(f"❌ Error reading CSV: {str(e)}")
                st.info("💡 Tip: Open CSV in Excel/Sheets and re-save as UTF-8 CSV")
    
    with tab2:
        # Similar structure for jobs import (concise)
        st.markdown("### Import Jobs from CSV")
        st.info("✅ **Required columns**: `company_name`, `job_title`, `date_applied` (YYYY-MM-DD)")
        st.caption("	Optional: `status`, `priority`, `job_link`, `notes`")
        
        sample_jobs = pd.DataFrame({
            "company_name": ["Google", "Microsoft"],
            "job_title": ["Senior Engineer", "Product Manager"],
            "date_applied": ["2024-01-15", "2024-02-01"],
            "status": ["Applied", "Interview Scheduled"],
            "priority": ["High", "Medium"]
        })
        
        st.download_button(
            "📥 Download Sample Jobs CSV",
            sample_jobs.to_csv(index=False),
            file_name="jobs_template.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"], key="jobs_csv_upload")
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.dataframe(df.head(), use_container_width=True)
                
                required_cols = ["company_name", "job_title", "date_applied"]
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    st.error(f"❌ Missing columns: {', '.join(missing_cols)}")
                elif st.button("✅ Import Jobs", type="primary", use_container_width=True):
                    with st.spinner(f"Importing {len(df)} jobs..."):
                        success_count, errors = import_jobs_csv(session, df)
                    if errors:
                        st.warning(f"✅ Imported {success_count} | ⚠️ {len(errors)} errors")
                    else:
                        st.success(f"✅ Imported {success_count} jobs!")
                        st.balloons()
            except Exception as e:
                st.error(f"❌ CSV error: {str(e)}")
    
    with tab3:
        st.markdown("### Export Your Data")
        st.info("💡 All exports include full data with timestamps")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📧 Export Contacts", use_container_width=True):
                df = fetch_all_contacts(session)
                st.download_button(
                    "📥 Download CSV",
                    df.to_csv(index=False),
                    file_name=f"contacts_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col2:
            if st.button("💼 Export Jobs", use_container_width=True):
                from src.database import fetch_all_jobs
                df = fetch_all_jobs(session)
                st.download_button(
                    "📥 Download CSV",
                    df.to_csv(index=False),
                    file_name=f"jobs_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col3:
            if st.button("📨 Export Email Logs", use_container_width=True):
                logs = get_email_logs(session, limit=10000)
                df = pd.DataFrame([{
                    "sent_at": l.sent_at,
                    "contact": session.query(Contact).get(l.contact_id).name if l.contact_id else "Unknown",
                    "subject": l.subject,
                    "status": l.status,
                    "error": l.error_message or ""
                } for l in logs])
                st.download_button(
                    "📥 Download CSV",
                    df.to_csv(index=False),
                    file_name=f"email_logs_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )