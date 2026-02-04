"""
Fixed database.py - Contains ALL required CRUD functions for Jobs + Contacts + Templates
"""
import datetime
import logging
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.model import Base, Job, Contact, EmailTemplate, EmailLog, EmailAccount

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ CREATE ENGINE HERE (best practice)
engine = create_engine("sqlite:///job_tracker.db", echo=False)

# Create all tables
Base.metadata.create_all(engine)

# Create session factory
Session = sessionmaker(bind=engine)

def init_db():
    return Session()

# ========== JOB CRUD ==========
def add_job_application(session, data):
    try:
        new_job = Job(
            date_applied=data["date_applied"],
            company_name=data["company_name"],
            job_title=data["job_title"],
            location=data["location"],
            job_link=data["job_link"],
            status=data["status"],
            follow_up_date=data["follow_up_date"],
            interview_date=data["interview_date"],
            recruiter_contact=data["recruiter_contact"],
            networking_contact=data["networking_contact"],
            notes=data["notes"],
            priority=data["priority"],
        )
        session.add(new_job)
        session.commit()
        logger.info("Job application added successfully.")
    except Exception as e:
        logger.exception("An error occurred while adding job application")
        st.error(f"An error occurred: {e}")
        session.rollback()

def fetch_all_jobs(session):
    try:
        return pd.read_sql(session.query(Job).statement, session.bind)
    except Exception as e:
        logger.exception("Database error while fetching job applications")
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def update_job_application(session, application_id, updated_data):
    try:
        job = session.query(Job).filter_by(id=application_id).one()
        job.status = updated_data["status"]
        job.follow_up_date = updated_data["follow_up_date"]
        job.interview_date = updated_data["interview_date"]
        job.notes = updated_data["notes"]
        session.commit()
        logger.info("Job application %s updated successfully.", application_id)
    except Exception as e:
        logger.exception("Database error while updating job application")
        st.error(f"Database error: {e}")
        session.rollback()

def delete_job_application(session, application_id):
    try:
        job = session.query(Job).filter_by(id=application_id).one()
        session.delete(job)
        session.commit()
        logger.info("Job application %s deleted successfully.", application_id)
    except Exception as e:
        logger.exception("Database error while deleting job application")
        st.error(f"Database error: {e}")
        session.rollback()

# ========== CONTACT CRUD (Phase 3) ==========
def add_contact(session, data):
    try:
        contact = Contact(
            name=data["name"],
            email=data["email"],
            company_name=data["company_name"],
            job_id=data.get("job_id"),
            contact_type=data.get("contact_type", "Other"),
            phone=data.get("phone"),
            linkedin_url=data.get("linkedin_url")
        )
        session.add(contact)
        session.commit()
        logger.info(f"Contact {data['name']} added successfully")
        return contact.id
    except Exception as e:
        logger.exception("Error adding contact")
        st.error(f"Error adding contact: {e}")
        session.rollback()
        raise

def fetch_all_contacts(session):
    try:
        return pd.read_sql(session.query(Contact).statement, session.bind)
    except Exception as e:
        logger.exception("Error fetching contacts")
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def update_contact(session, contact_id, data):
    try:
        contact = session.query(Contact).get(contact_id)
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")
        
        for key, value in data.items():
            if hasattr(contact, key):
                setattr(contact, key, value)
        
        session.commit()
        logger.info(f"Contact {contact_id} updated")
    except Exception as e:
        logger.exception("Error updating contact")
        st.error(f"Error updating contact: {e}")
        session.rollback()
        raise

def delete_contact(session, contact_id):
    try:
        contact = session.query(Contact).get(contact_id)
        if contact:
            session.delete(contact)
            session.commit()
            logger.info(f"Contact {contact_id} deleted")
    except Exception as e:
        logger.exception("Error deleting contact")
        st.error(f"Error deleting contact: {e}")
        session.rollback()
        raise

# ========== EMAIL TEMPLATE CRUD (Phase 3) ==========
def add_email_template(session, name, subject, body, is_followup=False, days_after_previous=7):
    try:
        template = EmailTemplate(
            name=name,
            subject=subject,
            body=body,
            is_followup=is_followup,
            days_after_previous=days_after_previous
        )
        session.add(template)
        session.commit()
        logger.info(f"Template '{name}' added")
        return template.id
    except Exception as e:
        logger.exception("Error adding template")
        st.error(f"Error adding template: {e}")
        session.rollback()
        raise

def get_all_templates(session):
    return session.query(EmailTemplate).all()

def get_template_by_id(session, template_id):
    return session.query(EmailTemplate).get(template_id)

# ========== ADD THESE FUNCTIONS TO YOUR EXISTING database.py ==========

from src.model import Contact, EmailTemplate, EmailLog, EmailAccount

# ========== CONTACT CRUD ==========
def add_contact(session, data):
    """Add new contact"""
    try:
        contact = Contact(
            name=data["name"],
            email=data["email"],
            company_name=data["company_name"],
            job_id=data.get("job_id"),
            contact_type=data.get("contact_type", "Other"),
            phone=data.get("phone"),
            linkedin_url=data.get("linkedin_url")
        )
        session.add(contact)
        session.commit()
        logger.info(f"Contact {data['name']} added successfully")
        return contact.id
    except Exception as e:
        logger.exception("Error adding contact")
        session.rollback()
        raise e

def fetch_all_contacts(session):
    """Fetch all contacts as DataFrame"""
    try:
        return pd.read_sql(session.query(Contact).statement, session.bind)
    except Exception as e:
        logger.exception("Error fetching contacts")
        return pd.DataFrame()

def update_contact(session, contact_id, data):
    """Update contact"""
    try:
        contact = session.query(Contact).get(contact_id)
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")
        
        for key, value in data.items():
            if hasattr(contact, key):
                setattr(contact, key, value)
        
        session.commit()
        logger.info(f"Contact {contact_id} updated")
    except Exception as e:
        logger.exception("Error updating contact")
        session.rollback()
        raise e

def delete_contact(session, contact_id):
    """Delete contact"""
    try:
        contact = session.query(Contact).get(contact_id)
        if contact:
            session.delete(contact)
            session.commit()
            logger.info(f"Contact {contact_id} deleted")
    except Exception as e:
        logger.exception("Error deleting contact")
        session.rollback()
        raise e

def get_contacts_by_job(session, job_id):
    """Get all contacts linked to a job"""
    return session.query(Contact).filter_by(job_id=job_id).all()

# ========== EMAIL TEMPLATE CRUD ==========
def add_email_template(session, name, subject, body, is_followup=False, days_after_previous=7):
    """Add email template"""
    try:
        template = EmailTemplate(
            name=name,
            subject=subject,
            body=body,
            is_followup=is_followup,
            days_after_previous=days_after_previous
        )
        session.add(template)
        session.commit()
        logger.info(f"Template '{name}' added")
        return template.id
    except Exception as e:
        logger.exception("Error adding template")
        session.rollback()
        raise e

def get_all_templates(session):
    """Get all email templates"""
    return session.query(EmailTemplate).all()

def get_template_by_id(session, template_id):
    """Get template by ID"""
    return session.query(EmailTemplate).get(template_id)

def update_template(session, template_id, data):
    """Update template"""
    try:
        template = session.query(EmailTemplate).get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        for key, value in data.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        session.commit()
        logger.info(f"Template {template_id} updated")
    except Exception as e:
        logger.exception("Error updating template")
        session.rollback()
        raise e

def delete_template(session, template_id):
    """Delete template"""
    try:
        template = session.query(EmailTemplate).get(template_id)
        if template:
            session.delete(template)
            session.commit()
            logger.info(f"Template {template_id} deleted")
    except Exception as e:
        logger.exception("Error deleting template")
        session.rollback()
        raise e

# ========== EMAIL LOG QUERIES ==========
def get_email_logs(session, contact_id=None, limit=50):
    """Get email logs, optionally filtered by contact"""
    query = session.query(EmailLog).order_by(EmailLog.sent_at.desc())
    if contact_id:
        query = query.filter_by(contact_id=contact_id)
    return query.limit(limit).all()

def get_followup_candidates(session, days_threshold=7):
    """Get contacts needing follow-up (FR-13)"""
    from datetime import datetime, timedelta, timezone
    
    threshold_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
    
    return session.query(Contact).filter(
        Contact.last_contacted <= threshold_date,
        Contact.last_contacted.isnot(None)
    ).all()

# ========== CSV IMPORT ==========
def import_contacts_csv(session, df):
    """Import contacts from CSV (FR-18)"""
    success_count = 0
    errors = []
    
    required_cols = ["name", "email", "company_name"]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"CSV must contain columns: {required_cols}")
    
    for _, row in df.iterrows():
        try:
            contact = Contact(
                name=row["name"],
                email=row["email"],
                company_name=row["company_name"],
                contact_type=row.get("contact_type", "Other"),
                phone=row.get("phone"),
                linkedin_url=row.get("linkedin_url")
            )
            session.add(contact)
            success_count += 1
        except Exception as e:
            errors.append(f"Row {success_count}: {str(e)}")
    
    session.commit()
    return success_count, errors

def import_jobs_csv(session, df):
    """Import jobs from CSV (FR-19)"""
    success_count = 0
    errors = []
    
    required_cols = ["company_name", "job_title", "date_applied"]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"CSV must contain columns: {required_cols}")
    
    for _, row in df.iterrows():
        try:
            job = Job(
                company_name=row["company_name"],
                job_title=row["job_title"],
                date_applied=datetime.strptime(row["date_applied"], "%Y-%m-%d").date(),
                status=row.get("status", "Applied"),
                location=row.get("location"),
                job_link=row.get("job_link"),
                notes=row.get("notes"),
                priority=row.get("priority", "Medium")
            )
            session.add(job)
            success_count += 1
        except Exception as e:
            errors.append(f"Row {success_count}: {str(e)}")
    
    session.commit()
    return success_count, errors