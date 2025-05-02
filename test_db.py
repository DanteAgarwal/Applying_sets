import sqlite3
from datetime import datetime, timedelta
from random import choice, randint

# Database setup
conn = sqlite3.connect("job_tracker.db", check_same_thread=False)
c = conn.cursor()

# Creating table if it doesn't exist
c.execute(
    """CREATE TABLE IF NOT EXISTS jobs (
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
    priority TEXT
)"""
)
conn.commit()

# Sample data for testing
companies = [
    "Google",
    "Microsoft",
    "Amazon",
    "Apple",
    "Facebook",
    "Twitter",
    "Adobe",
    "Salesforce",
    "Tesla",
    "Nvidia",
    "Oracle",
    "LinkedIn",
    "Spotify",
    "Zoom",
    "Slack",
    "Dropbox",
    "Airbnb",
    "Uber",
    "Snapchat",
    "TikTok",
    "Snap",
    "Pinterest",
    "Spotify",
    "Reddit",
    "GitHub",
    "Square",
]

job_titles = [
    "Software Engineer",
    "Data Analyst",
    "Product Manager",
    "UX/UI Designer",
    "Backend Developer",
    "Frontend Developer",
    "Data Scientist",
    "Security Analyst",
    "Cloud Engineer",
    "HR Manager",
    "Marketing Specialist",
    "Sales Executive",
    "Business Analyst",
    "Operations Manager",
    "Graphic Designer",
    "Full Stack Developer",
    "Mobile Developer",
    "Project Manager",
    "Software Architect",
    "DevOps Engineer",
    "Content Strategist",
    "Legal Counsel",
    "Financial Analyst",
    "QA Engineer",
    "Digital Marketing Specialist",
    "IT Support Specialist",
]

locations = [
    "New York, NY",
    "San Francisco, CA",
    "Austin, TX",
    "Seattle, WA",
    "Los Angeles, CA",
    "Chicago, IL",
    "Boston, MA",
    "Dallas, TX",
    "Miami, FL",
    "Denver, CO",
    "Washington, D.C.",
    "Phoenix, AZ",
    "Atlanta, GA",
    "Houston, TX",
    "Salt Lake City, UT",
]

statuses = ["Applied", "Interview Scheduled", "Offer Received", "Rejected", "Ghosted"]

priorities = ["High", "Medium", "Low"]

# Generate fake job applications (25 records)
for _ in range(25):
    date_applied = datetime.today() - timedelta(days=randint(1, 60))
    company_name = choice(companies)
    job_title = choice(job_titles)
    location = choice(locations)
    job_link = f"https://{company_name.lower().replace(' ', '')}.com/jobs/{randint(1000, 9999)}"
    status = choice(statuses)
    follow_up_date = date_applied + timedelta(days=randint(5, 10))
    interview_date = (
        date_applied + timedelta(days=randint(10, 30))
        if status == "Interview Scheduled"
        else None
    )
    recruiter_contact = (
        f"recruiter{randint(100, 999)}@{company_name.lower().replace(' ', '')}.com"
    )
    networking_contact = f"contact{randint(100, 999)}@linkedin.com"
    notes = (
        "Follow up soon"
        if status == "Applied"
        else "In the process of scheduling interview"
    )
    c.execute(
        """INSERT INTO jobs (date_applied, company_name, job_title, location, job_link, status, follow_up_date,
        interview_date, recruiter_contact, networking_contact, notes, priority) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            date_applied.strftime("%Y-%m-%d"),
            company_name,
            job_title,
            location,
            job_link,
            status,
            follow_up_date.strftime("%Y-%m-%d"),
            interview_date.strftime("%Y-%m-%d") if interview_date else None,
            recruiter_contact,
            networking_contact,
            notes,
            choice(priorities),
        ),
    )

conn.commit()
print("25 fake job applications added successfully!")

conn.close()
