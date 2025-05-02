
import sqlite3
import streamlit as st
import pandas as pd
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect("job_tracker.db", check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_applied TEXT,
                    company_name TEXT,
                    job_title TEXT,
                    location TEXT,
                    job_link TEXT,
                    status TEXT,
                    follow_up_date TEXT,
                    interview_date TEXT,
                    recruiter_contact TEXT,
                    networking_contact TEXT,
                    notes TEXT,
                    priority TEXT,
                    created_at TEXT,
                    updated_at TEXT)''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_status ON jobs (status)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_priority ON jobs (priority)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_date_applied ON jobs (date_applied)')
    conn.commit()
    return conn

# Insert a new job application into the database
def add_job_application(conn, data):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO jobs (date_applied, company_name, job_title, location, job_link, status, follow_up_date, interview_date, recruiter_contact, networking_contact, notes, priority, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (data['date_applied'], data['company_name'], data['job_title'], data['location'], data['job_link'], data['status'], data['follow_up_date'], data['interview_date'], data['recruiter_contact'], data['networking_contact'], data['notes'], data['priority'], datetime.now(), datetime.now()))
        conn.commit()
        logger.info("Job application added successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        st.error(f"Database error: {e}")

# Fetch all job applications
def fetch_all_jobs(conn):
    try:
        return pd.read_sql("SELECT * FROM jobs", conn)
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        st.error(f"Database error: {e}")
        return pd.DataFrame()

# Update a job application by ID
def update_job_application(conn, application_id, updated_data):
    try:
        c = conn.cursor()
        c.execute("UPDATE jobs SET status = ?, follow_up_date = ?, interview_date = ?, notes = ?, updated_at = ? WHERE id = ?",
                  (updated_data['status'], updated_data['follow_up_date'], updated_data['interview_date'], updated_data['notes'], datetime.now(), application_id))
        conn.commit()
        logger.info(f"Job application {application_id} updated successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        st.error(f"Database error: {e}")

# Delete a job application by ID
def delete_job_application(conn, application_id):
    try:
        c = conn.cursor()
        c.execute("DELETE FROM jobs WHERE id = ?", (application_id,))
        conn.commit()
        logger.info(f"Job application {application_id} deleted successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        st.error(f"Database error: {e}")