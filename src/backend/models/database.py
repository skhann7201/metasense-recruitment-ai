from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///./metasense_recruitment.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    # Personal Information
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    home_phone = Column(String)
    mobile_phone = Column(String)
    
    # Professional Information
    profession = Column(String)
    specialty = Column(String)
    current_job = Column(String)
    
    # Location Information
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    
    # Status Tracking
    status = Column(String, default="new")  # new, contacted, engaged, placed, unsubscribed
    contact_count = Column(Integer, default=0)
    last_contacted = Column(DateTime)
    
    # Recruiting-Specific Fields
    source = Column(String, default="organic")  # organic, referral, linkedin, indeed, etc.
    consent_given = Column(Boolean, default=True)
    consent_date = Column(DateTime, default=datetime.utcnow)
    last_contacted_by = Column(String)  # Recruiter name
    preferred_contact_method = Column(String, default="email")
    notes = Column(Text)  # Recruiter notes
    priority_level = Column(String, default="medium")  # high, medium, low
    
    # Subscription Management
    subscribed = Column(Boolean, default=True)
    unsubscribe_token = Column(String, unique=True)
    unsubscribed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, index=True)
    channel = Column(String)  # email, sms
    message_type = Column(String)  # outbound, inbound
    content = Column(Text)
    message_id = Column(String)
    status = Column(String, default="sent")  # sent, delivered, read, failed
    thread_id = Column(String)  # For email threading
    parent_id = Column(Integer)  # For reply chains
    created_at = Column(DateTime, default=datetime.utcnow)

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    campaign_type = Column(String)  # email, sms, both
    target_specialty = Column(String)
    recruiter_name = Column(String)  # Which recruiter is running this campaign
    message_template = Column(Text)
    status = Column(String, default="draft")  # draft, running, completed, paused
    sent_count = Column(Integer, default=0)
    response_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class PendingResponse(Base):
    __tablename__ = "pending_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, index=True)
    channel = Column(String)  # email, sms
    incoming_message = Column(Text)  # Original message from candidate
    generated_content = Column(Text)  # AI-generated response
    edited_content = Column(Text, nullable=True)  # Human-edited version (if modified)
    status = Column(String, default="pending")  # pending, approved, rejected, sent
    subject = Column(String, nullable=True)  # For email responses
    recipient_email = Column(String, nullable=True)  # For email
    recipient_phone = Column(String, nullable=True)  # For SMS
    reviewed_by = Column(String, nullable=True)  # Recruiter who reviewed
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)

# Create all tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()