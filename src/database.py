# import logging

# import pandas as pd
# import streamlit as st
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from src.model import Base, Job

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Create SQLite database engine
# engine = create_engine("sqlite:///job_tracker.db")

# # Create tables in the database
# Base.metadata.create_all(engine)

# # Create a session factory
# Session = sessionmaker(bind=engine)


# def init_db():
#     return Session()


# # Insert a new job application into the database
# def add_job_application(session, data):
#     try:
#         new_job = Job(
#             date_applied=data["date_applied"],
#             company_name=data["company_name"],
#             job_title=data["job_title"],
#             location=data["location"],
#             job_link=data["job_link"],
#             status=data["status"],
#             follow_up_date=data["follow_up_date"],
#             interview_date=data["interview_date"],
#             recruiter_contact=data["recruiter_contact"],
#             networking_contact=data["networking_contact"],
#             notes=data["notes"],
#             priority=data["priority"],
#         )
#         session.add(new_job)
#         session.commit()
#         logger.info("Job application added successfully.")
#     except Exception as e:
#         logger.exception("An error occurred while adding job application")
#         st.error(f"An error occurred: {e}")


# # Fetch all job applications
# def fetch_all_jobs(session):
#     try:
#         return pd.read_sql(session.query(Job).statement, session.bind)
#     except Exception as e:
#         logger.exception("Database error while fetching job applications")
#         st.error(f"Database error: {e}")
#         return pd.DataFrame()


# # Update a job application by ID
# def update_job_application(session, application_id, updated_data):
#     try:
#         job = session.query(Job).filter_by(id=application_id).one()
#         job.status = updated_data["status"]
#         job.follow_up_date = updated_data["follow_up_date"]
#         job.interview_date = updated_data["interview_date"]
#         job.notes = updated_data["notes"]
#         session.commit()
#         logger.info("Job application %s updated successfully.", application_id)
#     except Exception as e:
#         logger.exception("Database error while updating job application")
#         st.error(f"Database error: {e}")


# # Delete a job application by ID
# def delete_job_application(session, application_id):
#     try:
#         job = session.query(Job).filter_by(id=application_id).one()
#         session.delete(job)
#         session.commit()
#         logger.info("Job application %s deleted successfully.", application_id)
#     except Exception as e:
#         logger.exception("Database error while deleting job application")
#         st.error(f"Database error: {e}")

import logging

import pandas as pd
import streamlit as st
from sqlalchemy.orm import sessionmaker
from src.model import Job, engine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a session factory
Session = sessionmaker(bind=engine)


def init_db():
    return Session()


# Insert a new job application into the database
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


# Fetch all job applications
def fetch_all_jobs(session):
    try:
        return pd.read_sql(session.query(Job).statement, session.bind)
    except Exception as e:
        logger.exception("Database error while fetching job applications")
        st.error(f"Database error: {e}")
        return pd.DataFrame()


# Update a job application by ID
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


# Delete a job application by ID
def delete_job_application(session, application_id):
    try:
        job = session.query(Job).filter_by(id=application_id).one()
        session.delete(job)
        session.commit()
        logger.info("Job application %s deleted successfully.", application_id)
    except Exception as e:
        logger.exception("Database error while deleting job application")
        st.error(f"Database error: {e}")
