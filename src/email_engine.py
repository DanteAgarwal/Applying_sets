"""
Refactored Email Engine - Single Bulk Send Path & Clean Lifecycle
✅ Centralized SMTP lifecycle | ✅ Unified send path | ✅ Simplified credential handling
✅ Added send_personalized_email method for quality focus
"""
import smtplib
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple, Dict
import streamlit as st
from src.model import Contact, EmailTemplate, EmailLog, EmailAccount, Job
from src.calendar_integration import create_followup_event
from src.security import SimpleCredentialStore# Import the credential store from UI module

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailEngine:
    def __init__(self, session, credential_manager=None):
        self.session = session
        # ✅ FIX #3: Use SimpleCredentialStore directly
        self.credential_manager = credential_manager or SimpleCredentialStore()
        self.smtp_connection = None
        self.current_account = None
        self.rate_limit_delay = 5  # seconds between emails to avoid spam flags
        self.daily_limit = 50  # Gmail SMTP limit is ~100/day for new accounts

    def setup_account(self, email_address: str, app_password: str, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        """Configure email account and test connection"""
        try:
            # Save credentials securely
            self.credential_manager.save(email_address, app_password)

            # Save account metadata to DB
            account = self.session.query(EmailAccount).filter_by(email_address=email_address).first()
            if not account:
                account = EmailAccount(
                    email_address= email_address,
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
            creds = self.credential_manager.load(email_address)
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

            creds = self.credential_manager.load(email_address)
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

    def format_template(self, template: EmailTemplate, contact: Contact, job: Optional[Job] = None, your_name: str = "Your Name", personalization_context: Optional[Dict[str, str]] = None) -> Tuple[str, str]:
        """Replace template variables with actual data, including personalization context."""
        # Build base context dictionary
        context = {
            "{name}": contact.name or "Hiring Team",
            "{company}": contact.company_name or (job.company_name if job else ""),
            "{job_title}": job.job_title if job else "",
            "{first_name}": contact.name.split()[0] if contact.name else "there",
            "{your_name}": your_name,
            "{today}": datetime.now(timezone.utc).strftime("%B %d, %Y"),
            # Enhanced personalization variables from contact
            "{contact_role}": contact.contact_type or "hiring manager",
            "{phone}": contact.phone or "[phone not available]",
            "{linkedin}": contact.linkedin_url or "[LinkedIn not provided]"
        }

        # Add or overwrite with personalization context (specific to this email)
        if personalization_context:
            context.update(personalization_context)

        # Replace variables in subject and body
        subject = template.subject
        body = template.body

        for placeholder, value in context.items():
            subject = subject.replace(placeholder, value)
            body = body.replace(placeholder, value)

        return subject, body

    def send_email(self, contact: Contact, template: EmailTemplate, job: Optional[Job] = None, attachments: Optional[list] = None, your_name: str = "Your Name", max_retries: int = 3) -> Tuple[bool, str, Optional[object]]:
        """
        Send single email. ASSUMES SMTP CONNECTION IS ALREADY ACTIVE.
        Uses standard context only.

        Args:
            max_retries: Number of attempts (default 3) with exponential backoff (1s, 2s, 4s)

        Returns:
            Tuple of (success: bool, message: str, calendar_event: Optional[CalendarEvent])
        """
        # Use standard context (no personalization)
        return self._send_email_internal(contact, template, job, attachments, your_name, max_retries, personalization_context=None)

    def send_personalized_email(self, contact: Contact, template: EmailTemplate, job: Optional[Job] = None, attachments: Optional[list] = None, your_name: str = "Your Name", personalization_context: Optional[Dict[str, str]] = None, max_retries: int = 3) -> Tuple[bool, str, Optional[object]]:
        """
        Send single, highly personalized email. ASSUMES SMTP CONNECTION IS ALREADY ACTIVE.
        Uses both standard context AND personalization context.

        Args:
            personalization_context: Dict of additional variables specific to this email.
            max_retries: Number of attempts (default 3) with exponential backoff (1s, 2s, 4s)

        Returns:
            Tuple of (success: bool, message: str, calendar_event: Optional[CalendarEvent])
        """
        return self._send_email_internal(contact, template, job, attachments, your_name, max_retries, personalization_context=personalization_context)

    def _send_email_internal(self, contact: Contact, template: EmailTemplate, job: Optional[Job] = None, attachments: Optional[list] = None, your_name: str = "Your Name", max_retries: int = 3, personalization_context: Optional[Dict[str, str]] = None) -> Tuple[bool, str, Optional[object]]:
        """
        Internal helper to handle the actual sending logic, supporting both standard and personalized emails.
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                # Format email content with user-provided your_name and personalization context
                subject, body = self.format_template(template, contact, job, your_name, personalization_context)

                # Create MIME message (mixed to allow attachments)
                msg = MIMEMultipart("mixed")
                msg_alt = MIMEMultipart("alternative")
                msg["From"] = formataddr((f"{your_name}", self.current_account.email_address)) # Use your_name in From field
                msg["To"] = contact.email
                msg["Subject"] = subject

                # Attach plain text version inside alternative part
                msg_alt.attach(MIMEText(body, "plain"))
                msg.attach(msg_alt)

                # Handle attachments (list of tuples: (filename, bytes, mimetype))
                if attachments:
                    for att in attachments:
                        try:
                            filename, content, mimetype = att
                        except Exception:
                            continue

                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(content)
                        encoders.encode_base64(part)
                        part.add_header("Content-Disposition", f"attachment; filename=\"{filename}\"")
                        msg.attach(part)

                # ✅ FIX #2: ASSUME SMTP IS ALREADY CONNECTED
                if not self.smtp_connection:
                    # This should ideally never happen if called from send_bulk_emails correctly
                    raise Exception("SMTP connection not established. Call connect_smtp first.")

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
                last_error = str(e)
                logger.warning(f"Email send attempt {attempt + 1}/{max_retries} failed: {last_error}")

                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s between retries
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # All retries exhausted - log failure
                    email_log = EmailLog(
                        contact_id=contact.id,
                        template_id=template.id,
                        job_id=job.id if job else None,
                        subject=subject if 'subject' in locals() else template.subject,
                        body=body if 'body' in locals() else template.body,
                        status="failed",
                        error_message=f"Failed after {max_retries} attempts: {last_error}"
                    )
                    self.session.add(email_log)
                    self.session.commit()

                    return False, f"Failed after {max_retries} attempts: {last_error}", None

        # Fallback (shouldn't reach here)
        return False, f"Unexpected error: {last_error}", None
    def get_followup_candidates(self, days_threshold: int = 7):
        """
        Get contacts needing follow-up based on FR-13 rule
        """
        from datetime import datetime, timedelta, timezone
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

    def mark_as_replied(self, contact_id: int, notes: str = ""):
        """Mark a contact as replied and update their record"""
        contact = self.session.query(Contact).get(contact_id)
        if contact:
            contact.replied = True
            contact.needs_followup = False
            if notes:
                contact.notes = (contact.notes or "") + f"\n\nFollow-up Notes: {notes}"
            self.session.commit()
            return True
        return False

    def send_bulk_emails(self, contact_ids: List[int], template_id: int, job: Optional[object] = None, attachments: Optional[list] = None, your_name: str = "Your Name"):
        """
        Send emails to multiple contacts sequentially with rate limiting.
        Handles SMTP connection lifecycle internally.
        Note: This method now focuses on sending the *same* personalized email to multiple contacts,
              which might be less common with the new 'quality' focus. Consider deprecating or adapting.
        """
        template = self.session.query(EmailTemplate).get(template_id)
        if not template:
            return False, "Template not found"

        results = {"sent": 0, "failed": 0, "errors": []}

        # ✅ FIX #2: CONNECT ONCE AT START OF BULK OPERATION
        if not self.connect_smtp(self.current_account.email_address):
            return False, "Failed to establish SMTP connection."

        try:
            for i, contact_id in enumerate(contact_ids):
                contact = self.session.query(Contact).get(contact_id)
                if not contact:
                    results["failed"] += 1
                    results["errors"].append(f"Contact {contact_id} not found")
                    continue

                # The `job` object passed from UI is the temporary object, so we pass it directly
                # For bulk, we use the standard send_email method (no unique personalization per contact here)
                success, message, _ = self.send_email(contact, template, job, attachments, your_name)

                if success:
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"{contact.email}: {message}")

                # Rate limiting - wait between sends
                if i < len(contact_ids) - 1:
                    time.sleep(self.rate_limit_delay)

            # ✅ FIX #2: DISCONNECT ONCE AT END OF BULK OPERATION
            self.disconnect_smtp()

            summary = f"Sent: {results['sent']}, Failed: {results['failed']}"
            if results["errors"]:
                summary += f"\n\nErrors:\n" + "\n".join(results["errors"][:5])  # Show first 5 errors

            return True, summary

        except Exception as e:
            # Ensure disconnection even if an unexpected error occurs
            self.disconnect_smtp()
            return False, f"Unexpected error during bulk send: {str(e)}"


# --- Convenience functions for Streamlit UI ---
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