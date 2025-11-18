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
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    specialty = Column(String)
    current_job = Column(String)
    status = Column(String, default="new")  # new, contacted, interested, not_interested, registered, max_contacts_reached
    contact_count = Column(Integer, default=0)  # Track how many times contacted
    last_contacted = Column(DateTime)  # Last contact date
    source = Column(String, default="manual")
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
    created_at = Column(DateTime, default=datetime.utcnow)

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    campaign_type = Column(String)  # email, sms, both
    target_specialty = Column(String)
    message_template = Column(Text)
    status = Column(String, default="draft")  # draft, running, completed, paused
    sent_count = Column(Integer, default=0)
    response_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create all tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()