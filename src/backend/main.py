from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from datetime import datetime

# Database imports
from models.database import get_db, Candidate, Conversation, Campaign

app = FastAPI(
    title="MetaSense Recruitment API",
    description="AI-powered recruitment system for MetaSense Inc.",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Real Email/SMS Functions
def send_real_email(to_email: str, subject: str, body: str) -> bool:
    """Send actual email using your existing email code"""
    try:
        msg = MIMEMultipart()
        msg["From"] = os.getenv("IONOS_EMAIL")
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.ionos.com", 465) as server:
            server.login(os.getenv("IONOS_EMAIL"), os.getenv("IONOS_PASSWORD"))
            server.send_message(msg)
        
        print(f"✅ REAL EMAIL SENT to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Email failed to {to_email}: {e}")
        return False

def send_real_sms(to_phone: str, message: str) -> bool:
    """Send actual SMS using your existing Twilio code"""
    try:
        client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        
        message_obj = client.messages.create(
            body=message,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=to_phone
        )
        
        print(f"✅ REAL SMS SENT to {to_phone} (SID: {message_obj.sid})")
        return True
    except Exception as e:
        print(f"❌ SMS failed to {to_phone}: {e}")
        return False

# Health checks
@app.get("/")
async def root():
    return {"message": "MetaSense Recruitment API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

# ==================== CANDIDATE MANAGEMENT ====================

@app.get("/api/candidates/count")
async def get_candidates_count(db: Session = Depends(get_db)):
    count = db.query(Candidate).count()
    return {"total_candidates": count}

@app.get("/api/candidates")
async def get_candidates(db: Session = Depends(get_db)):
    candidates = db.query(Candidate).order_by(Candidate.created_at.desc()).all()
    return {
        "candidates": [
            {
                "id": c.id,
                "first_name": c.first_name,
                "last_name": c.last_name,
                "email": c.email,
                "phone": c.phone,
                "specialty": c.specialty,
                "current_job": c.current_job,
                "status": c.status,
                "contact_count": c.contact_count,
                "last_contacted": c.last_contacted.isoformat() if c.last_contacted else None,
                "created_at": c.created_at.isoformat()
            } for c in candidates
        ]
    }

@app.post("/api/candidates")
async def create_candidate(candidate_data: dict, db: Session = Depends(get_db)):
    existing = db.query(Candidate).filter(Candidate.email == candidate_data.get("email")).first()
    if existing:
        raise HTTPException(status_code=400, detail="Candidate with this email already exists")
    
    candidate = Candidate(
        email=candidate_data.get("email"),
        phone=candidate_data.get("phone"),
        first_name=candidate_data.get("first_name"),
        last_name=candidate_data.get("last_name"),
        specialty=candidate_data.get("specialty"),
        current_job=candidate_data.get("current_job")
    )
    
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    
    return {
        "success": True,
        "id": candidate.id,
        "message": "Candidate created successfully"
    }

@app.put("/api/candidates/{candidate_id}")
async def update_candidate(candidate_id: int, candidate_data: dict, db: Session = Depends(get_db)):
    """Recruiters can manually update candidate information"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Update fields if provided
    if 'first_name' in candidate_data:
        candidate.first_name = candidate_data['first_name']
    if 'last_name' in candidate_data:
        candidate.last_name = candidate_data['last_name']
    if 'email' in candidate_data:
        candidate.email = candidate_data['email']
    if 'phone' in candidate_data:
        candidate.phone = candidate_data['phone']
    if 'specialty' in candidate_data:
        candidate.specialty = candidate_data['specialty']
    if 'current_job' in candidate_data:
        candidate.current_job = candidate_data['current_job']
    if 'status' in candidate_data:
        candidate.status = candidate_data['status']
    if 'contact_count' in candidate_data:
        candidate.contact_count = candidate_data['contact_count']
    
    db.commit()
    
    return {
        "success": True,
        "message": "Candidate updated successfully",
        "candidate": {
            "id": candidate.id,
            "first_name": candidate.first_name,
            "last_name": candidate.last_name,
            "status": candidate.status,
            "contact_count": candidate.contact_count
        }
    }

@app.post("/api/candidates/{candidate_id}/reset")
async def reset_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Reset a single candidate to 'new' status"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    candidate.status = "new"
    candidate.contact_count = 0
    candidate.last_contacted = None
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Reset {candidate.first_name} {candidate.last_name} to new status"
    }

@app.post("/api/candidates/reset-all")
async def reset_all_candidates(db: Session = Depends(get_db)):
    """Reset all candidates to 'new' status - for testing"""
    candidates = db.query(Candidate).all()
    reset_count = 0
    
    for candidate in candidates:
        candidate.status = "new"
        candidate.contact_count = 0
        candidate.last_contacted = None
        reset_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "reset_count": reset_count,
        "message": f"Reset {reset_count} candidates to 'new' status"
    }

@app.get("/api/candidates/{candidate_id}/contact-history")
async def get_candidate_contact_history(candidate_id: int, db: Session = Depends(get_db)):
    """Get candidate's full contact history"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    conversations = db.query(Conversation).filter(
        Conversation.candidate_id == candidate_id
    ).order_by(Conversation.created_at.desc()).all()
    
    return {
        "candidate": {
            "id": candidate.id,
            "name": f"{candidate.first_name} {candidate.last_name}",
            "contact_count": candidate.contact_count,
            "status": candidate.status,
            "last_contacted": candidate.last_contacted.isoformat() if candidate.last_contacted else None
        },
        "contact_history": [
            {
                "id": conv.id,
                "channel": conv.channel,
                "message_type": conv.message_type,
                "content": conv.content,
                "sent_at": conv.created_at.isoformat(),
                "status": conv.status
            } for conv in conversations
        ]
    }

# ==================== OUTREACH CAMPAIGNS ====================

@app.post("/api/campaigns/outreach")
async def start_outreach_campaign(campaign_data: dict, db: Session = Depends(get_db)):
    """Start REAL outreach campaign with 3-contact limit"""
    specialty_filter = campaign_data.get("specialty")
    channel = campaign_data.get("channel", "email")
    max_contact_limit = 3
    
    # Get candidates with less than 3 contacts
    query = db.query(Candidate).filter(
        Candidate.status.in_(["new", "contacted"]),
        Candidate.contact_count < max_contact_limit
    )
    
    if specialty_filter:
        query = query.filter(Candidate.specialty.ilike(f"%{specialty_filter}%"))
    
    candidates = query.all()
    
    campaign_results = []
    for candidate in candidates:
        # Generate personalized message
        if channel == "sms":
            message = f"Hi {candidate.first_name}! Your {candidate.specialty} experience caught our eye at MetaSense. We have matching roles! Register: https://www.metasenseinc.com/register"
            subject = "Healthcare Opportunities"
        else:
            message = f"""Hello {candidate.first_name},

I'm reaching out from MetaSense about {candidate.specialty} opportunities matching your background.

We connect healthcare professionals with great roles at hospitals and clinics.

Register your profile: https://www.metasenseinc.com/register

Best regards,
The MetaSense Team"""
            subject = f"Healthcare Opportunities for {candidate.specialty} Professionals"
        
        # SEND FOR REAL
        send_success = False
        if channel == "sms" and candidate.phone:
            send_success = send_real_sms(candidate.phone, message)
        elif channel == "email" and candidate.email:
            send_success = send_real_email(candidate.email, subject, message)
        
        if send_success:
            # Update contact tracking
            candidate.contact_count += 1
            candidate.last_contacted = datetime.utcnow()
            
            if candidate.contact_count >= max_contact_limit:
                candidate.status = "max_contacts_reached"
            else:
                candidate.status = "contacted"
        
        # Log the outreach
        conversation = Conversation(
            candidate_id=candidate.id,
            channel=channel,
            message_type="outbound",
            content=message,
            status="sent" if send_success else "failed"
        )
        db.add(conversation)
        
        campaign_results.append({
            "candidate_id": candidate.id,
            "name": f"{candidate.first_name} {candidate.last_name}",
            "email": candidate.email,
            "phone": candidate.phone,
            "specialty": candidate.specialty,
            "current_contact_count": candidate.contact_count,
            "max_contacts": max_contact_limit,
            "channel": channel,
            "sent_success": send_success
        })
        
        time.sleep(2)
    
    db.commit()
    
    successful_sends = len([r for r in campaign_results if r["sent_success"]])
    
    return {
        "success": True,
        "campaign": {
            "target_specialty": specialty_filter,
            "channel": channel,
            "max_contact_limit": max_contact_limit,
            "candidates_contacted": len(campaign_results),
            "successful_sends": successful_sends,
            "failed_sends": len(campaign_results) - successful_sends
        },
        "results": campaign_results
    }

# ==================== TESTING & SAMPLE DATA ====================

@app.post("/api/test/setup-sample-data")
async def setup_sample_data(db: Session = Depends(get_db)):
    """Create sample candidates for testing"""
    sample_candidates = [
        {
            "email": "nurse.mary@example.com",
            "phone": "+1215550101",
            "first_name": "Mary",
            "last_name": "Johnson", 
            "specialty": "Registered Nurse",
            "current_job": "ICU Nurse"
        },
        {
            "email": "therapist.david@example.com", 
            "phone": "+1215550102",
            "first_name": "David",
            "last_name": "Chen",
            "specialty": "Physical Therapist",
            "current_job": "Senior PT"
        },
        {
            "email": "tech.sarah@example.com",
            "phone": "+1215550103", 
            "first_name": "Sarah",
            "last_name": "Williams",
            "specialty": "Radiology Tech",
            "current_job": "MRI Technician"
        }
    ]
    
    added_count = 0
    for candidate_data in sample_candidates:
        existing = db.query(Candidate).filter(Candidate.email == candidate_data["email"]).first()
        if not existing:
            candidate = Candidate(**candidate_data)
            db.add(candidate)
            added_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "added_count": added_count,
        "message": f"Added {added_count} sample candidates"
    }

# ==================== DASHBOARD & ANALYTICS ====================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    total_candidates = db.query(Candidate).count()
    new_candidates = db.query(Candidate).filter(Candidate.status == "new").count()
    contacted_candidates = db.query(Candidate).filter(Candidate.status == "contacted").count()
    max_contacted = db.query(Candidate).filter(Candidate.status == "max_contacts_reached").count()
    total_conversations = db.query(Conversation).count()
    
    return {
        "total_candidates": total_candidates,
        "new_candidates": new_candidates,
        "contacted_candidates": contacted_candidates,
        "max_contacted_candidates": max_contacted,
        "total_conversations": total_conversations
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)