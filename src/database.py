import logging
import sqlite3
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Database setup
# def init_db():
#     conn = sqlite3.connect("job_tracker.db", check_same_thread=False)
#     c = conn.cursor()
#     c.execute(
#         """CREATE TABLE IF NOT EXISTS jobs (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     date_applied DATE NOT NULL,
#                     company_name TEXT NOT NULL,
#                     job_title TEXT NOT NULL,
#                     location TEXT,
#                     job_link TEXT UNIQUE,
#                     status TEXT DEFAULT 'Applied',
#                     follow_up_date DATE,
#                     interview_date DATE,
#                     recruiter_contact TEXT,
#                     networking_contact TEXT,
#                     notes TEXT,
#                     priority TEXT CHECK(priority IN ('Low', 'Medium', 'High')) DEFAULT 'Medium',
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP|
#                     )"""
#     )
#     c.execute("CREATE INDEX IF NOT EXISTS idx_status ON jobs (status)")
#     c.execute("CREATE INDEX IF NOT EXISTS idx_priority ON jobs (priority)")
#     c.execute("CREATE INDEX IF NOT EXISTS idx_date_applied ON jobs (date_applied)")
#     conn.commit()
#     return conn
def init_db():
    conn = sqlite3.connect("job_tracker.db", check_same_thread=False)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_applied DATE NOT NULL,
            company_name TEXT NOT NULL,
            job_title TEXT NOT NULL,
            location TEXT,
            job_link TEXT UNIQUE,
            status TEXT DEFAULT 'Applied',
            follow_up_date DATE,
            interview_date DATE,
            recruiter_contact TEXT,
            networking_contact TEXT,
            notes TEXT,
            priority TEXT CHECK(priority IN ('Low', 'Medium', 'High')) DEFAULT 'Medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_status ON jobs (status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_priority ON jobs (priority)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_date_applied ON jobs (date_applied)")
    conn.commit()
    return conn


# Insert a new job application into the database
def add_job_application(conn, data):
    try:
        c = conn.cursor()
        c.execute(
            """INSERT INTO jobs (date_applied, company_name,
            job_title, location, job_link, status, follow_up_date,
            interview_date, recruiter_contact, networking_contact,
            notes, priority, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["date_applied"],
                data["company_name"],
                data["job_title"],
                data["location"],
                data["job_link"],
                data["status"],
                data["follow_up_date"],
                data["interview_date"],
                data["recruiter_contact"],
                data["networking_contact"],
                data["notes"],
                data["priority"],
                datetime.now(tz=timezone.utc),
                datetime.now(tz=timezone.utc),
            ),
        )
        conn.commit()
        logger.info("Job application added successfully.")
    except sqlite3.Error as e:
        logger.exception("An error occurred while adding job application")
        st.error(f"An error occurred: {e}")


# Fetch all job applications
def fetch_all_jobs(conn):
    try:
        return pd.read_sql("SELECT * FROM jobs", conn)
    except sqlite3.Error as e:
        logger.exception("Database error while fetching job applications")
        st.error(f"Database error: {e}")
        return pd.DataFrame()


# Update a job application by ID
def update_job_application(conn, application_id, updated_data):
    try:
        c = conn.cursor()
        c.execute(
            """UPDATE jobs SET status = ?,
            follow_up_date = ?, interview_date = ?, notes = ?, updated_at = ?
    WHERE id = ?""",
            (
                updated_data["status"],
                updated_data["follow_up_date"],
                updated_data["interview_date"],
                updated_data["notes"],
                datetime.now(tz=timezone.utc),
                application_id,
            ),
        )
        conn.commit()
        logger.info("Job application %s updated successfully.", application_id)
    except sqlite3.Error as e:
        logger.exception("Database error while updating job application")
        st.error(f"Database error: {e}")


# Delete a job application by ID
def delete_job_application(conn, application_id):
    try:
        c = conn.cursor()
        c.execute("DELETE FROM jobs WHERE id = ?", (application_id,))
        conn.commit()
        logger.info("Job application %s updated successfully.", application_id)
    except sqlite3.Error as e:
        logger.exception("Database error while deleting job application")
        st.error(f"Database error: {e}")
