# from datetime import datetime

# from sqlalchemy import TIMESTAMP, Column, Date, Enum, Integer, String, Text, create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

# # Define base class
# Base = declarative_base()


# class Job(Base):
#     __tablename__ = "jobs"

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     date_applied = Column(Date, nullable=False)
#     company_name = Column(String, nullable=False)
#     job_title = Column(String, nullable=False)
#     location = Column(String)
#     job_link = Column(String, unique=True)
#     status = Column(String, default="Applied")
#     follow_up_date = Column(Date)
#     interview_date = Column(Date)
#     recruiter_contact = Column(String)
#     networking_contact = Column(String)
#     notes = Column(Text)
#     priority = Column(Enum("Low", "Medium", "High", name="priority_enum"), default="Medium")
#     created_at = Column(TIMESTAMP, default=datetime.utcnow)
#     updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)


# # Create SQLite database engine
# engine = create_engine("sqlite:///job_tracker.db")

# # Create tables in the database
# Base.metadata.create_all(engine)

# # Create a session factory
# Session = sessionmaker(bind=engine)

from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, Date, Enum, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define base class
Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"

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
    priority = Column(Enum("Low", "Medium", "High", name="priority_enum"), default="Medium")
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create SQLite database engine
engine = create_engine("sqlite:///job_tracker.db")

# Create tables in the database
Base.metadata.create_all(engine)

# Create a session factory
Session = sessionmaker(bind=engine)
