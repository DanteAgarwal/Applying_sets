"""
Fixed model.py - Phase 3 ready with proper SQLAlchemy conventions
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Boolean, Enum as SqlEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# ========== JOB MODEL ==========
class Job(Base):
    __tablename__ = "jobs"  # ✅ CORRECT: double underscores
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date_applied = Column(Date, nullable=False)
    company_name = Column(String, nullable=False)
    job_title = Column(String, nullable=False)
    location = Column(String)
    job_link = Column(String, unique=True)
    status = Column(String, default="Applied")
    follow_up_date = Column(Date)
    interview_date = Column(Date)
    recruiter_contact = Column(String)
    networking_contact = Column(String)
    notes = Column(Text)
    priority = Column(SqlEnum("Low", "Medium", "High", name="priority_enum"), default="Medium")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    contacts = relationship("Contact", back_populates="job", cascade="all, delete-orphan")

# ========== CONTACT MODEL (Phase 3) ==========
class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    contact_type = Column(SqlEnum("Recruiter", "HR", "Hiring Manager", "Networking", "Other", name="contact_type_enum"), default="Other")
    phone = Column(String)
    linkedin_url = Column(String)
    last_contacted = Column(DateTime)
    needs_followup = Column(Boolean, default=False)
    followup_date = Column(Date)
    replied = Column(Boolean, default=False)
    reply_date = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    job = relationship("Job", back_populates="contacts")

# ========== EMAIL TEMPLATE MODEL (Phase 3) ==========
class EmailTemplate(Base):
    __tablename__ = "email_templates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    is_followup = Column(Boolean, default=False)
    days_after_previous = Column(Integer, default=7)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

# ========== EMAIL LOG MODEL (Phase 3) ==========
class EmailLog(Base):
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(SqlEnum("sent", "failed", "bounced", name="email_status_enum"), default="sent")
    error_message = Column(Text)
    smtp_response = Column(String)

# ========== EMAIL ACCOUNT MODEL (Phase 3) ==========
class EmailAccount(Base):
    __tablename__ = "email_accounts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email_address = Column(String, nullable=False, unique=True)
    smtp_server = Column(String, default="smtp.gmail.com")
    smtp_port = Column(Integer, default=587)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))