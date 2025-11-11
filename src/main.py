# integrated_recruiter.py
import csv
import os
import time
import logging
from datetime import datetime
from database import ConversationDB
from response_agent import ResponseAgent
from email_handler import EmailResponseHandler
from sms_handler import SMSResponseHandler

# ------------------- Your Existing Email Functions (Updated) -------------------
def send_email(to_email, subject, body, candidate_id=None):
    """Send email and log to conversation database"""
    # Your existing email sending code here
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.ionos.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        # LOG TO DATABASE if candidate_id provided
        if candidate_id:
            db.log_conversation(candidate_id, 'email', 'outbound', body)
        
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False

# ------------------- Your Existing SMS Functions (Updated) -------------------
def send_sms(to_number, message, candidate_id=None):
    """Send SMS and log to conversation database"""
    try:
        client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        
        message_obj = client.messages.create(
            body=message,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=to_number
        )
        
        # LOG TO DATABASE if candidate_id provided
        if candidate_id:
            db.log_conversation(candidate_id, 'sms', 'outbound', message)
        
        print(f"SMS sent to {to_number} (SID: {message_obj.sid})")
        return True
    except Exception as e:
        print(f"SMS failed to {to_number}: {e}")
        return False

# ------------------- Enhanced Process Contacts with Database Integration -------------------
def process_contacts_with_memory(csv_file, specialty_filter=None, channel="both"):
    """
    Process contacts with conversation memory
    channel: "email", "sms", or "both"
    """
    contacts = read_contacts(csv_file)
    matched_any = False
    
    for contact in contacts:
        contact_specialty = contact.get("SPECIALTY", "").strip().lower()
        
        # Filter by specialty if specified
        if specialty_filter and specialty_filter.lower() not in contact_specialty:
            continue
        
        matched_any = True
        first_name = contact["FIRST NAME"]
        last_name = contact["LAST NAME"]
        email = contact["EMAIL"]
        phone = contact.get("MOBILE PHONE", "").strip()
        
        # Add candidate to database and get ID
        candidate_id = db.add_candidate(contact)
        print(f"Added {first_name} {last_name} to database (ID: {candidate_id})")
        
        # Generate message content
        if channel in ["email", "both"] and email and "@" in email:
            email_body = generate_email(first_name, last_name)
            subject = f"Healthcare Opportunities for {first_name} - MetaSense Inc."
            
            # Send email with candidate ID for logging
            success = send_email(email, subject, email_body, candidate_id)
            if success:
                print(f"Email logged for {first_name} {last_name}")
            
            time.sleep(2)
        
        if channel in ["sms", "both"] and phone:
            sms_message = generate_text_message(first_name, last_name, contact.get("CURRENT JOB", "N/A"))
            
            # Send SMS with candidate ID for logging
            success = send_sms(phone, sms_message, candidate_id)
            if success:
                print(f"SMS logged for {first_name} {last_name}")
            
            time.sleep(2)
    
    if not matched_any:
        print(f"No contacts matched the specialty: '{specialty_filter}'")

# ------------------- Response Monitoring System -------------------
def start_response_monitoring():
    """Start monitoring for candidate responses"""
    print("Starting response monitoring system...")
    
    email_handler = EmailResponseHandler()
    sms_handler = SMSResponseHandler()
    
    while True:
        try:
            print(f"Checking for responses... {datetime.now()}")
            email_handler.check_responses()
            sms_handler.check_sms_responses()
            
            # Wait 5 minutes between checks
            time.sleep(300)
            
        except KeyboardInterrupt:
            print("⏹Monitoring stopped by user")
            break
        except Exception as e:
            print(f"Monitoring error: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

# ------------------- Interactive Menu System -------------------
def show_menu():
    print("\n" + "="*50)
    print("🤖 META SENSE RECRUITMENT AGENT")
    print("="*50)
    print("1. Send Email Campaign")
    print("2. Send SMS Campaign") 
    print("3. Send Both Email & SMS")
    print("4. Start Response Monitoring")
    print("5. View Conversation History")
    print("6. Exit")
    print("="*50)

def get_conversation_history():
    """View conversation history for a candidate"""
    email = input("Enter candidate email: ").strip()
    
    conn = db._get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.id, c.first_name, c.last_name 
        FROM candidates c WHERE c.email = ?
    ''', (email,))
    
    candidate = cursor.fetchone()
    
    if candidate:
        candidate_id, first_name, last_name = candidate
        print(f"\nConversation history for {first_name} {last_name}:")
        
        history = db.get_conversation_history(candidate_id)
        for msg in history:
            icon = "" if msg['message_type'] == 'outbound' else "💬"
            channel = msg['channel'].upper()
            print(f"{icon} [{channel}] {msg['timestamp']}: {msg['content'][:100]}...")
    else:
        print("Candidate not found")
    
    conn.close()

# ------------------- Main Execution -------------------
if __name__ == "__main__":
    # Initialize database and agent
    db = ConversationDB()
    logging.basicConfig(level=logging.INFO)
    
    print("🤖 MetaSense Recruitment Agent Initialized!")
    
    while True:
        show_menu()
        choice = input("Select option (1-6): ").strip()
        
        if choice == "1":
            csv_file = "test_contact.csv"
            specialty = input("Enter specialty filter (or press Enter for all): ").strip()
            specialty = specialty if specialty else None
            process_contacts_with_memory(csv_file, specialty, channel="email")
            
        elif choice == "2":
            csv_file = "test_contact.csv" 
            specialty = input("Enter specialty filter (or press Enter for all): ").strip()
            specialty = specialty if specialty else None
            process_contacts_with_memory(csv_file, specialty, channel="sms")
            
        elif choice == "3":
            csv_file = "test_contact.csv"
            specialty = input("Enter specialty filter (or press Enter for all): ").strip()
            specialty = specialty if specialty else None
            process_contacts_with_memory(csv_file, specialty, channel="both")
            
        elif choice == "4":
            print("Starting response monitoring in background...")
            start_response_monitoring()
            
        elif choice == "5":
            get_conversation_history()
            
        elif choice == "6":
            print("Goodbye!")
            break
            
        else:
            print("Invalid option")
        
        input("\nPress Enter to continue...")