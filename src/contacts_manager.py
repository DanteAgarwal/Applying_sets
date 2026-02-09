"""
Contact management UI
"""
import streamlit as st
import pandas as pd

from src.database import (
    add_contact, fetch_all_contacts, get_email_logs, update_contact, delete_contact,
    get_contacts_by_job
)
from src.model import Contact, Job

def contacts_list_ui(session):
    """FR-5: Contacts List UI"""
    st.subheader("👥 All Contacts")
    
    contacts_df = fetch_all_contacts(session)
    
    if contacts_df.empty:
        st.info("No contacts yet. Add your first contact!")
        # Replace the st.page_link line with this:
        if st.button("➕ Add Contact", type="primary"):
            st.session_state.show_add_contact = True
            st.rerun()
        return
    
    # Search and filter
    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("🔍 Search", placeholder="Name, email, or company")
    with col2:
        contact_type = st.selectbox("Type", ["All"] + ["Recruiter", "HR", "Hiring Manager", "Networking", "Other"])
    with col3:
        sort_by = st.selectbox("Sort by", ["Name", "Company", "Last Contacted", "Created"])
    
    # Apply filters
    filtered_df = contacts_df.copy()
    if search:
        filtered_df = filtered_df[
            filtered_df["name"].str.contains(search, case=False) |
            filtered_df["email"].str.contains(search, case=False) |
            filtered_df["company_name"].str.contains(search, case=False)
        ]
    if contact_type != "All":
        filtered_df = filtered_df[filtered_df["contact_type"] == contact_type]
    
    # Sort
    sort_map = {
        "Name": "name",
        "Company": "company_name",
        "Last Contacted": "last_contacted",
        "Created": "created_at"
    }
    filtered_df = filtered_df.sort_values(sort_map[sort_by], ascending=True)
    
    # Display
    st.metric("Total Contacts", len(filtered_df))
    
    for _, row in filtered_df.iterrows():
        with st.expander(f"👤 {row['name']} - {row['company_name']}", expanded=False):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**Email:** {row['email']}")
                st.write(f"**Type:** {row['contact_type']}")
                if row['phone']:
                    st.write(f"**Phone:** {row['phone']}")
            
            with col2:
                st.write(f"**Last Contacted:** {row['last_contacted'] or 'Never'}")
                if row['linkedin_url']:
                    st.markdown(f"[LinkedIn]({row['linkedin_url']})")
                if row['job_id']:
                    job = session.query(Job).get(row['job_id'])
                    if job:
                        st.caption(f"📎 Job: {job.job_title}")
            
            with col3:
                if st.button("✏️ Edit", key=f"edit_{row['id']}"):
                    st.session_state.editing_contact = row['id']
                    st.rerun()
                if st.button("🗑️ Delete", key=f"del_{row['id']}"):
                    if st.checkbox(f"Confirm delete {row['name']}?"):
                        delete_contact(session, row['id'])
                        st.success("Deleted!")
                        st.rerun()
    
    # Edit modal
    if "editing_contact" in st.session_state:
        contact_id = st.session_state.editing_contact
        contact = session.query(Contact).get(contact_id)
        
        st.markdown("---")
        st.subheader(f"✏️ Edit Contact: {contact.name}")
        
        with st.form("edit_contact"):
            name = st.text_input("Name", contact.name)
            email = st.text_input("Email", contact.email)
            company = st.text_input("Company", contact.company_name)
            contact_type = st.selectbox("Type", ["Recruiter", "HR", "Hiring Manager", "Networking", "Other"], 
                                       index=["Recruiter", "HR", "Hiring Manager", "Networking", "Other"].index(contact.contact_type))
            phone = st.text_input("Phone", contact.phone or "")
            linkedin = st.text_input("LinkedIn URL", contact.linkedin_url or "")
            
            if st.form_submit_button("💾 Save"):
                update_contact(session, contact_id, {
                    "name": name,
                    "email": email,
                    "company_name": company,
                    "contact_type": contact_type,
                    "phone": phone,
                    "linkedin_url": linkedin
                })
                st.success("Updated!")
                del st.session_state.editing_contact
                st.rerun()
            
            if st.form_submit_button("❌ Cancel"):
                del st.session_state.editing_contact
                st.rerun()

def add_contact_ui(session):
    """FR-2: Quick Contact Add UI"""
    if st.button("← Back to Contacts List"):
        if "show_add_contact" in st.session_state:
            del st.session_state.show_add_contact
        st.rerun()
    
    st.subheader("➕ Add New Contact")
    
    with st.form("add_contact"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("👤 Name*", placeholder="John Doe")
            email = st.text_input("📧 Email*", placeholder="john@company.com")
            company = st.text_input("🏢 Company*", placeholder="Google, Amazon...")
        
        with col2:
            contact_type = st.selectbox("Type", ["Recruiter", "HR", "Hiring Manager", "Networking", "Other"])
            phone = st.text_input("📱 Phone", placeholder="+1 234 567 8900")
            linkedin = st.text_input("🔗 LinkedIn URL", placeholder="https://linkedin.com/in/johndoe")
        
        # Optional job link
        jobs = session.query(Job).all()
        if jobs:
            job_options = [f"{j.company_name} - {j.job_title}" for j in jobs]
            job_idx = st.selectbox("📎 Link to Job (Optional)", ["None"] + job_options)
            job_id = jobs[job_options.index(job_idx)].id if job_idx != "None" else None
        else:
            job_id = None
            st.caption("No jobs yet. Create a job application first to link contacts.")
        
        if st.form_submit_button("💾 Save Contact", type="primary"):
            if not name or not email or not company:
                st.error("Name, email, and company are required")
            else:
                contact_data = {
                    "name": name,
                    "email": email,
                    "company_name": company,
                    "contact_type": contact_type,
                    "phone": phone,
                    "linkedin_url": linkedin,
                    "job_id": job_id
                }
                contact_id = add_contact(session, contact_data)
                st.success(f"✅ Contact '{name}' added!")
                st.balloons()

def contact_detail_ui(session, contact_id):
    """Contact detail view with email history"""
    contact = session.query(Contact).get(contact_id)
    if not contact:
        st.error("Contact not found")
        return
    
    st.subheader(f"👤 {contact.name}")
    
    col1, col2, col3 = st.columns(3)
    col1.write(f"**Email:** {contact.email}")
    col2.write(f"**Company:** {contact.company_name}")
    col3.write(f"**Type:** {contact.contact_type}")
    
    if contact.phone:
        st.write(f"📱 {contact.phone}")
    if contact.linkedin_url:
        st.markdown(f"🔗 [LinkedIn]({contact.linkedin_url})")
    
    if contact.job_id:
        job = session.query(Job).get(contact.job_id)
        st.caption(f"📎 Linked to job: {job.job_title} at {job.company_name}")
    
    # Email history
    st.markdown("---")
    st.subheader("📧 Email History")
    
    logs = get_email_logs(session, contact.id, limit=20)
    if not logs:
        st.info("No emails sent to this contact yet")
    else:
        for log in logs:
            with st.expander(f"{log.sent_at.strftime('%Y-%m-%d %H:%M')} - {log.subject}", expanded=False):
                st.write(log.body)
                st.caption(f"Status: {log.status}")