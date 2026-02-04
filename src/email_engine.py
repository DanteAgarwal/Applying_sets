"""
SMTP Email Engine with rate limiting, logging, and calendar integration (Phase 3)
"""
import smtplib
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
import streamlit as st

from src.model import Contact, EmailTemplate, EmailLog, EmailAccount, Job
from src.security import CredentialManager
from src.database import init_db
from src.calendar_integration import create_followup_event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailEngine:
    def __init__(self, session, credential_manager=None):
        self.session = session
        self.credential_manager = credential_manager or CredentialManager()
        self.smtp_connection = None
        self.current_account = None
        self.rate_limit_delay = 5  # seconds between emails to avoid spam flags
        self.daily_limit = 50  # Gmail SMTP limit is ~100/day for new accounts
    
    def setup_account(self, email_address: str, app_password: str, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        """Configure email account and test connection"""
        try:
            # Save credentials securely
            self.credential_manager.save_credentials(email_address, app_password)
            
            # Save account metadata to DB
            account = self.session.query(EmailAccount).filter_by(email_address=email_address).first()
            if not account:
                account = EmailAccount(
                    email_address=email_address,
                    smtp_server=smtp_server,
                    smtp_port=smtp_port,
                    is_active=True
                )
                self.session.add(account)
            else:
                account.smtp_server = smtp_server
                account.smtp_port = smtp_port
                account.is_active = True
            
            self.session.commit()
            
            # Test connection
            creds = self.credential_manager.load_credentials(email_address)
            if not creds:
                raise Exception("Failed to load credentials")
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(creds["email"], creds["password"])
            server.quit()
            
            logger.info(f"Email account {email_address} configured successfully")
            return True, "Account configured successfully!"
        
        except Exception as e:
            logger.error(f"Failed to setup email account: {e}")
            return False, f"Setup failed: {str(e)}"
    
    def connect_smtp(self, email_address: str):
        """Establish SMTP connection"""
        try:
            account = self.session.query(EmailAccount).filter_by(
                email_address=email_address,
                is_active=True
            ).first()
            
            if not account:
                raise Exception(f"No active account found for {email_address}")
            
            creds = self.credential_manager.load_credentials(email_address)
            if not creds:
                raise Exception("Credentials not found")
            
            self.smtp_connection = smtplib.SMTP(account.smtp_server, account.smtp_port)
            self.smtp_connection.starttls()
            self.smtp_connection.login(creds["email"], creds["password"])
            self.current_account = account
            
            logger.info(f"Connected to SMTP server: {account.smtp_server}")
            return True
        
        except Exception as e:
            logger.error(f"SMTP connection failed: {e}")
            return False
    
    def disconnect_smtp(self):
        """Close SMTP connection"""
        if self.smtp_connection:
            try:
                self.smtp_connection.quit()
                self.smtp_connection = None
                self.current_account = None
                logger.info("SMTP connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
    
    def format_template(self, template: EmailTemplate, contact: Contact, job: Optional[Job] = None) -> Tuple[str, str]:
        """Replace template variables with actual data"""
        # Build context dictionary
        context = {
            "{name}": contact.name or "Hiring Team",
            "{company}": contact.company_name or (job.company_name if job else ""),
            "{job_title}": job.job_title if job else "",
            "{first_name}": contact.name.split()[0] if contact.name else "there",
            "{your_name}": "Your Name",  # TODO: Make this configurable in settings
            "{today}": datetime.now(timezone.utc).strftime("%B %d, %Y")
        }
        
        # Replace variables in subject and body
        subject = template.subject
        body = template.body
        
        for placeholder, value in context.items():
            subject = subject.replace(placeholder, value)
            body = body.replace(placeholder, value)
        
        return subject, body
    
    def send_email(self, contact: Contact, template: EmailTemplate, job: Optional[Job] = None) -> Tuple[bool, str, Optional[object]]:
        """
        Send single email and auto-schedule follow-up calendar event
        
        Returns:
            Tuple of (success: bool, message: str, calendar_event: Optional[CalendarEvent])
        """
        try:
            # Format email content
            subject, body = self.format_template(template, contact, job)
            
            # Create MIME message
            msg = MIMEMultipart("alternative")
            msg["From"] = formataddr(("Job Tracker", self.current_account.email_address))
            msg["To"] = contact.email
            msg["Subject"] = subject
            
            # Attach plain text version
            msg.attach(MIMEText(body, "plain"))
            
            # Send email
            if not self.smtp_connection:
                if not self.connect_smtp(self.current_account.email_address):
                    raise Exception("SMTP connection failed")
            
            self.smtp_connection.send_message(msg)
            
            # Log successful send
            email_log = EmailLog(
                contact_id=contact.id,
                template_id=template.id,
                job_id=job.id if job else None,
                subject=subject,
                body=body,
                status="sent",
                smtp_response="250 OK"
            )
            self.session.add(email_log)
            
            # Update contact - Phase 3 enhancements
            contact.last_contacted = datetime.now(timezone.utc)
            contact.needs_followup = False
            contact.replied = False  # Reset reply status when sending new email
            
            # Auto-schedule follow-up date based on template
            if template.is_followup and template.days_after_previous:
                contact.followup_date = datetime.now(timezone.utc).date() + timedelta(days=template.days_after_previous)
                contact.needs_followup = True
            
            self.session.commit()
            
            logger.info(f"Email sent to {contact.email}")
            
            # ✅ PHASE 3: Auto-create calendar event for follow-up
            calendar_event = None
            if template.is_followup or template.days_after_previous > 0:
                followup_days = template.days_after_previous if template.is_followup else 7
                calendar_event = create_followup_event(
                    contact.name,
                    contact.company_name,
                    days_until=followup_days
                )
            
            return True, "Email sent successfully!", calendar_event
        
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            
            # Log failed attempt
            email_log = EmailLog(
                contact_id=contact.id,
                template_id=template.id,
                job_id=job.id if job else None,
                subject=subject if 'subject' in locals() else template.subject,
                body=body if 'body' in locals() else template.body,
                status="failed",
                error_message=str(e)
            )
            self.session.add(email_log)
            self.session.commit()
            
            return False, f"Failed to send: {str(e)}", None
    
    def send_bulk_emails(self, contact_ids: List[int], template_id: int, job_id: Optional[int] = None):
        """Send emails to multiple contacts sequentially with rate limiting"""
        template = self.session.query(EmailTemplate).get(template_id)
        if not template:
            return False, "Template not found"
        
        job = self.session.query(Job).get(job_id) if job_id else None
        
        results = {"sent": 0, "failed": 0, "errors": []}
        
        for contact_id in contact_ids:
            contact = self.session.query(Contact).get(contact_id)
            if not contact:
                results["failed"] += 1
                results["errors"].append(f"Contact {contact_id} not found")
                continue
            
            success, message, _ = self.send_email(contact, template, job)
            
            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"{contact.email}: {message}")
            
            # Rate limiting - wait between sends
            if contact_id != contact_ids[-1]:  # Don't wait after last email
                time.sleep(self.rate_limit_delay)
        
        self.disconnect_smtp()
        
        summary = f"Sent: {results['sent']}, Failed: {results['failed']}"
        if results["errors"]:
            summary += f"\n\nErrors:\n" + "\n".join(results["errors"][:5])  # Show first 5 errors
        
        return True, summary
    
    def get_followup_candidates(self, days_threshold: int = 7):
        """Get contacts needing follow-up based on FR-13 rule"""
        threshold_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
        
        candidates = self.session.query(Contact).filter(
            Contact.last_contacted <= threshold_date,
            Contact.last_contacted.isnot(None),
            Contact.needs_followup == False,  # noqa: E712
            Contact.replied == False
        ).all()
        
        # Mark them as needing followup
        for contact in candidates:
            contact.needs_followup = True
        
        self.session.commit()
        
        return candidates
    
    def mark_as_replied(self, contact_id: int, reply_notes: str = "") -> bool:
        """
        Mark contact as replied (removes from follow-up list)
        
        Args:
            contact_id: ID of the contact who replied
            reply_notes: Optional notes about the reply
        
        Returns:
            True if successful, False otherwise
        """
        try:
            contact = self.session.query(Contact).get(contact_id)
            if not contact:
                logger.error(f"Contact {contact_id} not found")
                return False
            
            # Update contact status
            contact.replied = True
            contact.reply_date = datetime.now(timezone.utc)
            contact.needs_followup = False
            
            # Update job notes if linked to a job
            if contact.job_id:
                job = self.session.query(Job).get(contact.job_id)
                if job and reply_notes:
                    timestamp = datetime.now().strftime('%Y-%m-%d')
                    job.notes = (job.notes or "") + f"\n\n✅ REPLY {timestamp}: {reply_notes}"
                    self.session.commit()
            
            self.session.commit()
            logger.info(f"Contact {contact_id} marked as replied")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark contact as replied: {e}")
            self.session.rollback()
            return False
    
    def get_actionable_items(self):
        """
        Get ONLY actionable items for low-friction dashboard (Phase 3)
        
        Returns:
            dict with keys: 'due_today', 'recent_replies', 'stale'
        """
        today = datetime.now(timezone.utc).date()
        
        # ✅ FOLLOW-UPS DUE TODAY (Highest priority)
        due_today = self.session.query(Contact).filter(
            Contact.followup_date == today,
            Contact.replied == False,
            Contact.needs_followup == True
        ).all()
        
        # ✅ RECENT REPLIES (Celebrate wins - last 7 days)
        recent_replies = self.session.query(Contact).filter(
            Contact.reply_date >= datetime.now(timezone.utc) - timedelta(days=7),
            Contact.replied == True
        ).all()
        
        # ✅ STALE CONTACTS (>14 days no reply, not marked as replied)
        stale = self.session.query(Contact).filter(
            Contact.last_contacted <= datetime.now(timezone.utc) - timedelta(days=14),
            Contact.replied == False,
            Contact.needs_followup == True
        ).all()
        
        return {
            "due_today": due_today,
            "recent_replies": recent_replies,
            "stale": stale
        }
    
    def get_email_stats(self):
        """Get email sending statistics"""
        total_sent = self.session.query(EmailLog).filter_by(status="sent").count()
        total_failed = self.session.query(EmailLog).filter_by(status="failed").count()
        today_sent = self.session.query(EmailLog).filter(
            EmailLog.status == "sent",
            EmailLog.sent_at >= datetime.now(timezone.utc).date()
        ).count()
        
        # Get reply stats
        total_replied = self.session.query(Contact).filter_by(replied=True).count()
        
        return {
            "total_sent": total_sent,
            "total_failed": total_failed,
            "total_replied": total_replied,
            "today_sent": today_sent,
            "success_rate": f"{(total_sent/(total_sent+total_failed)*100):.1f}%" if (total_sent+total_failed) > 0 else "0%",
            "reply_rate": f"{(total_replied/total_sent*100):.1f}%" if total_sent > 0 else "0%"
        }

# Convenience functions for Streamlit UI
def get_active_email_account(session):
    """Get the currently active email account"""
    return session.query(EmailAccount).filter_by(is_active=True).first()

def test_smtp_connection(email_address, app_password, smtp_server="smtp.gmail.com", smtp_port=587):
    """Test SMTP credentials without saving"""
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_address, app_password)
        server.quit()
        return True, "Connection successful!"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"