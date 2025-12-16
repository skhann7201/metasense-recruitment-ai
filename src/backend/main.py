from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import os
from sqlalchemy import func
import smtplib
import time
import secrets
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database imports
from models.database import get_db, Candidate, Conversation, Campaign, PendingResponse, Base, engine
from services.conversation_orchestrator import ConversationOrchestrator
from services.email_templates import MetaSenseTemplates

# Force database schema creation
print("🔄 Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Database tables created successfully!")
print("🏥 MetaSense Inc. Recruitment System Ready")

app = FastAPI(
    title="MetaSense Recruitment API",
    description="AI-powered healthcare recruitment system for MetaSense Inc.",
    version="2.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility Functions
def generate_unsubscribe_token() -> str:
    """Generate a secure random token for unsubscribe links"""
    return secrets.token_urlsafe(32)

def unsubscribe_candidate_db(candidate: Candidate, db: Session):
    """Unsubscribe candidate from communications"""
    candidate.subscribed = False
    candidate.unsubscribed_at = datetime.utcnow()
    candidate.status = "unsubscribed"
    db.commit()

# Real Email/SMS Functions
def send_real_email(to_email: str, subject: str, body: str) -> bool:
    """Send actual email using your existing email code"""
    try:
        msg = MIMEMultipart()
        msg["From"] = os.getenv("IONOS_EMAIL")
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html" if "<" in body else "plain"))

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
    return {"message": "MetaSense Inc. Healthcare Recruitment API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "company": "MetaSense Inc.", "database": "connected"}

# ==================== UNSUBSCRIBE SYSTEM ====================

@app.get("/unsubscribe/{token}")
async def unsubscribe_candidate(token: str, db: Session = Depends(get_db)):
    """Handle unsubscribe requests"""
    candidate = db.query(Candidate).filter(Candidate.unsubscribe_token == token).first()
    
    if not candidate:
        return HTMLResponse("""
        <html>
            <head><title>MetaSense Inc. - Unsubscribe</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f8f9fa;">
                <div style="max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #2c5aa0;">MetaSense Inc.</h2>
                    <h3>Unsubscribe Request</h3>
                    <p>Invalid unsubscribe link. You may have already been unsubscribed or the link has expired.</p>
                    <p>For immediate assistance, please contact us at <strong>+1 (856) 412-6100</strong>.</p>
                    <a href="https://www.metasenseinc.com" style="color: #2c5aa0; text-decoration: none;">Return to MetaSense Inc.</a>
                </div>
            </body>
        </html>
        """)
    
    # Mark as unsubscribed
    unsubscribe_candidate_db(candidate, db)
    
    return HTMLResponse(f"""
    <html>
        <head><title>Unsubscribe Successful - MetaSense Inc.</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f8f9fa;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #2c5aa0;">MetaSense Inc.</h2>
                <h3 style="color: #28a745;">Unsubscribe Successful</h3>
                <p>You have been unsubscribed from MetaSense recruitment communications.</p>
                <p>We're sorry to see you go! You will no longer receive emails or texts from us.</p>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Email:</strong> {candidate.email}</p>
                    <p><strong>Name:</strong> {candidate.first_name} {candidate.last_name}</p>
                </div>
                <p>If this was a mistake or you'd like to resubscribe, please contact us at <strong>+1 (856) 412-6100</strong>.</p>
                <a href="https://www.metasenseinc.com" style="color: #2c5aa0; text-decoration: none; font-weight: bold;">Return to MetaSense Inc.</a>
            </div>
        </body>
    </html>
    """)

# ==================== CANDIDATE MANAGEMENT ====================

@app.get("/api/candidates/count")
async def get_candidates_count(db: Session = Depends(get_db)):
    count = db.query(Candidate).count()
    return {"total_candidates": count, "company": "MetaSense Inc."}

@app.get("/api/candidates")
async def get_candidates(db: Session = Depends(get_db)):
    candidates = db.query(Candidate).order_by(Candidate.created_at.desc()).all()
    return {
        "company": "MetaSense Inc.",
        "candidates": [
            {
                "id": c.id,
                "first_name": c.first_name,
                "last_name": c.last_name,
                "email": c.email,
                "home_phone": c.home_phone,
                "mobile_phone": c.mobile_phone,
                "profession": c.profession,
                "specialty": c.specialty,
                "current_job": c.current_job,
                "city": c.city,
                "state": c.state,
                "zip_code": c.zip_code,
                "status": c.status,
                "contact_count": c.contact_count,
                "subscribed": c.subscribed,
                "last_contacted_by": c.last_contacted_by,
                "priority_level": c.priority_level,
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
        # Personal Information
        first_name=candidate_data.get("first_name"),
        last_name=candidate_data.get("last_name"),
        email=candidate_data.get("email"),
        home_phone=candidate_data.get("home_phone"),
        mobile_phone=candidate_data.get("mobile_phone"),
        
        # Professional Information
        profession=candidate_data.get("profession"),
        specialty=candidate_data.get("specialty"),
        current_job=candidate_data.get("current_job"),
        
        # Location Information
        city=candidate_data.get("city"),
        state=candidate_data.get("state"),
        zip_code=candidate_data.get("zip_code"),
        
        # Subscription
        unsubscribe_token=generate_unsubscribe_token(),
        subscribed=True
    )
    
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    
    return {
        "success": True,
        "id": candidate.id,
        "message": "Candidate created successfully",
        "company": "MetaSense Inc."
    }

@app.post("/api/candidates/{candidate_id}/unsubscribe")
async def manual_unsubscribe(candidate_id: int, db: Session = Depends(get_db)):
    """Manually unsubscribe a candidate"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    unsubscribe_candidate_db(candidate, db)
    
    return {
        "success": True,
        "message": f"Unsubscribed {candidate.first_name} {candidate.last_name}",
        "company": "MetaSense Inc."
    }

# ==================== OUTREACH CAMPAIGNS ====================

@app.post("/api/campaigns/outreach")
async def start_outreach_campaign(campaign_data: dict, db: Session = Depends(get_db)):
    """Start professional outreach campaign for MetaSense Inc."""
    specialty_filter = campaign_data.get("specialty")
    channel = campaign_data.get("channel", "email")
    recruiter_name = campaign_data.get("recruiter", random.choice(MetaSenseTemplates.RECRUITERS))
    max_contact_limit = 3
    
    # Professional targeting for healthcare recruiting
    query = db.query(Candidate).filter(
        Candidate.status.in_(["new", "contacted"]),
        Candidate.contact_count < max_contact_limit,
        Candidate.subscribed == True
    )
    
    if specialty_filter:
        query = query.filter(Candidate.specialty.ilike(f"%{specialty_filter}%"))
    
    candidates = query.all()
    
    campaign_results = []
    for candidate in candidates:
        # Use professional MetaSense templates
        if channel == "sms":
            message = MetaSenseTemplates.get_sms_template(candidate)
            subject = "Healthcare Opportunities with MetaSense"
        else:
            message = MetaSenseTemplates.get_initial_email(candidate, specialty_filter)
            subject = f"Healthcare {candidate.specialty} Opportunities - MetaSense Inc."
        
        # SEND FOR REAL
        send_success = False
        if channel == "sms" and candidate.mobile_phone:
            send_success = send_real_sms(candidate.mobile_phone, message)
        elif channel == "email" and candidate.email:
            send_success = send_real_email(candidate.email, subject, message)
        
        if send_success:
            # Update contact tracking
            candidate.contact_count += 1
            candidate.last_contacted = datetime.utcnow()
            candidate.last_contacted_by = recruiter_name
            
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
            "mobile_phone": candidate.mobile_phone,
            "profession": candidate.profession,
            "specialty": candidate.specialty,
            "current_contact_count": candidate.contact_count,
            "max_contacts": max_contact_limit,
            "channel": channel,
            "recruiter": recruiter_name,
            "sent_success": send_success
        })
        
        # Professional pacing
        time.sleep(2)
    
    db.commit()
    
    successful_sends = len([r for r in campaign_results if r["sent_success"]])
    
    return {
        "success": True,
        "company": "MetaSense Inc.",
        "campaign": {
            "target_specialty": specialty_filter,
            "channel": channel,
            "recruiter": recruiter_name,
            "max_contact_limit": max_contact_limit,
            "candidates_contacted": len(campaign_results),
            "successful_sends": successful_sends,
            "failed_sends": len(campaign_results) - successful_sends
        },
        "results": campaign_results
    }

# ==================== AI RESPONSE HANDLERS ====================

@app.post("/api/webhooks/email-reply")
async def handle_email_reply(webhook_data: dict, db: Session = Depends(get_db)):
    """Handle incoming email replies from candidates"""
    try:
        # Extract email data
        sender_email = webhook_data.get("from")
        subject = webhook_data.get("subject", "")
        message_body = webhook_data.get("text", "")
        message_id = webhook_data.get("message_id", "")
        
        # Find candidate by email
        candidate = db.query(Candidate).filter(Candidate.email == sender_email).first()
        if not candidate:
            print(f"❌ No candidate found for email: {sender_email}")
            return {"status": "ignored", "reason": "Candidate not found"}
        
        # Check if candidate is unsubscribed
        if not candidate.subscribed:
            print(f"❌ Candidate {sender_email} is unsubscribed, ignoring message")
            return {"status": "ignored", "reason": "Candidate unsubscribed"}
        
        # Check for unsubscribe keywords in message
        unsubscribe_keywords = ["unsubscribe", "stop", "remove", "cancel", "opt out"]
        if any(keyword in message_body.lower() for keyword in unsubscribe_keywords):
            unsubscribe_candidate_db(candidate, db)
            print(f"✅ Candidate {sender_email} unsubscribed via email request")
            return {
                "success": True,
                "action": "unsubscribed",
                "message": "Candidate unsubscribed based on email content",
                "company": "MetaSense Inc."
            }
        
        # Get conversation history
        conversation_history = db.query(Conversation).filter(
            Conversation.candidate_id == candidate.id
        ).order_by(Conversation.created_at.desc()).limit(10).all()
        
        # Generate AI response
        orchestrator = ConversationOrchestrator()
        ai_response = orchestrator.generate_response(
            channel="email",
            candidate=candidate,
            incoming_message=message_body,
            conversation_history=conversation_history
        )
        
        # Log incoming message
        incoming_conv = Conversation(
            candidate_id=candidate.id,
            channel="email",
            message_type="inbound",
            content=message_body,
            message_id=message_id,
            status="received"
        )
        db.add(incoming_conv)
        
        # Queue response for approval instead of auto-sending
        reply_subject = f"Re: {subject}" if not subject.startswith("Re:") else subject
        pending_response = PendingResponse(
            candidate_id=candidate.id,
            channel="email",
            incoming_message=message_body,
            generated_content=ai_response,
            status="pending",
            subject=reply_subject,
            recipient_email=sender_email
        )
        db.add(pending_response)
        
        # Update candidate status
        candidate.status = "engaged"
        candidate.last_contacted = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "candidate_id": candidate.id,
            "pending_response_id": pending_response.id,
            "message": "AI response generated and queued for approval",
            "company": "MetaSense Inc."
        }
        
    except Exception as e:
        print(f"❌ Error handling email reply: {e}")
        raise HTTPException(status_code=500, detail="Error processing email reply")

@app.post("/api/webhooks/sms-reply")
async def handle_sms_reply(webhook_data: dict, db: Session = Depends(get_db)):
    """Handle incoming SMS replies from candidates"""
    try:
        # Extract SMS data (Twilio webhook format)
        from_phone = webhook_data.get("From", "")
        message_body = webhook_data.get("Body", "")
        message_sid = webhook_data.get("MessageSid", "")
        
        # Find candidate by mobile phone
        candidate = db.query(Candidate).filter(Candidate.mobile_phone == from_phone).first()
        if not candidate:
            print(f"❌ No candidate found for phone: {from_phone}")
            return {"status": "ignored", "reason": "Candidate not found"}
        
        # Check if candidate is unsubscribed
        if not candidate.subscribed:
            print(f"❌ Candidate {from_phone} is unsubscribed, ignoring message")
            return {"status": "ignored", "reason": "Candidate unsubscribed"}
        
        # Check for unsubscribe keywords in message
        unsubscribe_keywords = ["stop", "unsubscribe", "cancel", "end", "quit"]
        if any(keyword in message_body.lower() for keyword in unsubscribe_keywords):
            unsubscribe_candidate_db(candidate, db)
            print(f"✅ Candidate {from_phone} unsubscribed via SMS request")
            return {
                "success": True,
                "action": "unsubscribed",
                "message": "Candidate unsubscribed based on SMS content",
                "company": "MetaSense Inc."
            }
        
        # Get conversation history
        conversation_history = db.query(Conversation).filter(
            Conversation.candidate_id == candidate.id
        ).order_by(Conversation.created_at.desc()).limit(10).all()
        
        # Generate AI response
        orchestrator = ConversationOrchestrator()
        ai_response = orchestrator.generate_response(
            channel="sms",
            candidate=candidate,
            incoming_message=message_body,
            conversation_history=conversation_history
        )
        
        # Log incoming message
        incoming_conv = Conversation(
            candidate_id=candidate.id,
            channel="sms",
            message_type="inbound",
            content=message_body,
            message_id=message_sid,
            status="received"
        )
        db.add(incoming_conv)
        
        # Queue response for approval instead of auto-sending
        pending_response = PendingResponse(
            candidate_id=candidate.id,
            channel="sms",
            incoming_message=message_body,
            generated_content=ai_response,
            status="pending",
            recipient_phone=from_phone
        )
        db.add(pending_response)
        
        # Update candidate status
        candidate.status = "engaged"
        candidate.last_contacted = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "candidate_id": candidate.id,
            "pending_response_id": pending_response.id,
            "message": "AI response generated and queued for approval",
            "company": "MetaSense Inc."
        }
        
    except Exception as e:
        print(f"❌ Error handling SMS reply: {e}")
        raise HTTPException(status_code=500, detail="Error processing SMS reply")

# ==================== RESPONSE APPROVAL WORKFLOW ====================

@app.get("/api/responses/pending")
async def get_pending_responses(db: Session = Depends(get_db)):
    """Get all pending responses awaiting approval"""
    pending = db.query(PendingResponse).filter(
        PendingResponse.status == "pending"
    ).order_by(PendingResponse.created_at.desc()).all()
    
    results = []
    for response in pending:
        candidate = db.query(Candidate).filter(Candidate.id == response.candidate_id).first()
        results.append({
            "id": response.id,
            "candidate": {
                "id": candidate.id,
                "name": f"{candidate.first_name} {candidate.last_name}",
                "email": candidate.email,
                "mobile_phone": candidate.mobile_phone,
                "specialty": candidate.specialty
            },
            "channel": response.channel,
            "incoming_message": response.incoming_message,
            "generated_content": response.generated_content,
            "subject": response.subject,
            "created_at": response.created_at.isoformat()
        })
    
    return {
        "success": True,
        "count": len(results),
        "pending_responses": results,
        "company": "MetaSense Inc."
    }

@app.post("/api/responses/{response_id}/approve")
async def approve_response(response_id: int, approval_data: dict, db: Session = Depends(get_db)):
    """Approve and send a pending response"""
    pending = db.query(PendingResponse).filter(PendingResponse.id == response_id).first()
    if not pending:
        raise HTTPException(status_code=404, detail="Pending response not found")
    
    if pending.status != "pending":
        raise HTTPException(status_code=400, detail="Response has already been processed")
    
    # Get the content to send (edited or original)
    content_to_send = pending.edited_content if pending.edited_content else pending.generated_content
    reviewer_name = approval_data.get("reviewer_name", "Unknown Recruiter")
    
    # Send the response based on channel
    send_success = False
    if pending.channel == "email":
        send_success = send_real_email(pending.recipient_email, pending.subject, content_to_send)
    elif pending.channel == "sms":
        send_success = send_real_sms(pending.recipient_phone, content_to_send)
    
    if send_success:
        # Log the outgoing message
        outgoing_conv = Conversation(
            candidate_id=pending.candidate_id,
            channel=pending.channel,
            message_type="outbound",
            content=content_to_send,
            status="sent"
        )
        db.add(outgoing_conv)
        
        # Update pending response status
        pending.status = "sent"
        pending.reviewed_by = reviewer_name
        pending.reviewed_at = datetime.utcnow()
        pending.sent_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Response approved and sent successfully",
            "response_id": response_id,
            "company": "MetaSense Inc."
        }
    else:
        pending.status = "failed"
        pending.reviewed_by = reviewer_name
        pending.reviewed_at = datetime.utcnow()
        db.commit()
        
        raise HTTPException(status_code=500, detail="Failed to send response")

@app.post("/api/responses/{response_id}/reject")
async def reject_response(response_id: int, rejection_data: dict, db: Session = Depends(get_db)):
    """Reject a pending response without sending"""
    pending = db.query(PendingResponse).filter(PendingResponse.id == response_id).first()
    if not pending:
        raise HTTPException(status_code=404, detail="Pending response not found")
    
    if pending.status != "pending":
        raise HTTPException(status_code=400, detail="Response has already been processed")
    
    reviewer_name = rejection_data.get("reviewer_name", "Unknown Recruiter")
    
    pending.status = "rejected"
    pending.reviewed_by = reviewer_name
    pending.reviewed_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Response rejected successfully",
        "response_id": response_id,
        "company": "MetaSense Inc."
    }

@app.put("/api/responses/{response_id}/edit")
async def edit_response(response_id: int, edit_data: dict, db: Session = Depends(get_db)):
    """Edit a pending response before approval"""
    pending = db.query(PendingResponse).filter(PendingResponse.id == response_id).first()
    if not pending:
        raise HTTPException(status_code=404, detail="Pending response not found")
    
    if pending.status != "pending":
        raise HTTPException(status_code=400, detail="Response has already been processed")
    
    new_content = edit_data.get("edited_content")
    if not new_content:
        raise HTTPException(status_code=400, detail="No edited content provided")
    
    pending.edited_content = new_content
    db.commit()
    
    return {
        "success": True,
        "message": "Response edited successfully",
        "response_id": response_id,
        "edited_content": new_content,
        "company": "MetaSense Inc."
    }

# ==================== TESTING & SAMPLE DATA ====================

@app.post("/api/test/setup-sample-data")
async def setup_sample_data(db: Session = Depends(get_db)):
    """Create sample healthcare candidates for testing"""
    sample_candidates = [
        {
            "first_name": "Maria",
            "last_name": "Rodriguez",
            "email": "maria.rodriguez@example.com",
            "home_phone": "+1215550101",
            "mobile_phone": "+1215550111",
            "profession": "Registered Nurse",
            "specialty": "Emergency Room",
            "current_job": "ER Nurse",
            "city": "Camden",
            "state": "NJ",
            "zip_code": "08102"
        },
        {
            "first_name": "James",
            "last_name": "Wilson",
            "email": "james.wilson@example.com",
            "home_phone": "+1215550102",
            "mobile_phone": "+1215550112",
            "profession": "Physical Therapist",
            "specialty": "Orthopedics",
            "current_job": "Senior PT",
            "city": "Cherry Hill",
            "state": "NJ",
            "zip_code": "08002"
        },
        {
            "first_name": "Lisa",
            "last_name": "Thompson",
            "email": "lisa.thompson@example.com",
            "home_phone": "+1215550103",
            "mobile_phone": "+1215550113",
            "profession": "Radiology Technician",
            "specialty": "MRI Technology",
            "current_job": "MRI Tech",
            "city": "Voorhees",
            "state": "NJ",
            "zip_code": "08043"
        }
    ]
    
    added_count = 0
    for candidate_data in sample_candidates:
        existing = db.query(Candidate).filter(Candidate.email == candidate_data["email"]).first()
        if not existing:
            candidate = Candidate(
                **candidate_data,
                unsubscribe_token=generate_unsubscribe_token(),
                subscribed=True
            )
            db.add(candidate)
            added_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "added_count": added_count,
        "message": f"Added {added_count} sample healthcare candidates",
        "company": "MetaSense Inc."
    }

# ==================== DASHBOARD & ANALYTICS ====================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    total_candidates = db.query(Candidate).count()
    new_candidates = db.query(Candidate).filter(Candidate.status == "new").count()
    contacted_candidates = db.query(Candidate).filter(Candidate.status == "contacted").count()
    engaged_candidates = db.query(Candidate).filter(Candidate.status == "engaged").count()
    max_contacted = db.query(Candidate).filter(Candidate.status == "max_contacts_reached").count()
    unsubscribed_count = db.query(Candidate).filter(Candidate.subscribed == False).count()
    total_conversations = db.query(Conversation).count()
    
    # Healthcare specialty breakdown
    top_specialties = db.query(Candidate.specialty, func.count(Candidate.specialty))\
                   .group_by(Candidate.specialty)\
                   .order_by(func.count(Candidate.specialty).desc())\
                   .limit(5).all()
    
    return {
        "company": "MetaSense Inc.",
        "stats": {
            "total_candidates": total_candidates,
            "new_candidates": new_candidates,
            "contacted_candidates": contacted_candidates,
            "engaged_candidates": engaged_candidates,
            "max_contacted_candidates": max_contacted,
            "unsubscribed_candidates": unsubscribed_count,
            "total_conversations": total_conversations
        },
        "top_specialties": [{"specialty": spec, "count": count} for spec, count in top_specialties]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)