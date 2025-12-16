#!/usr/bin/env python3
"""
Demo script to show the interactive approval workflow in action

This script simulates the flow:
1. A candidate sends a message
2. AI generates a response  
3. Response is queued for approval
4. Recruiter can review/edit/approve via API or CLI
"""

import requests
import json
from datetime import datetime

API_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def demo_workflow():
    """Demonstrate the complete interactive workflow"""
    
    print_section("🏥 MetaSense Interactive Approval Workflow Demo")
    
    # Step 1: Simulate incoming candidate email
    print_section("STEP 1: Candidate Sends Email")
    
    webhook_data = {
        "from": "maria.rodriguez@example.com",
        "subject": "Re: Healthcare Opportunities",
        "text": "Hi! I'm very interested in learning more about the ER positions. What locations do you have available?",
        "message_id": "msg_demo_123"
    }
    
    print("Candidate: maria.rodriguez@example.com")
    print(f"Subject: {webhook_data['subject']}")
    print(f"Message: {webhook_data['text']}")
    
    print("\n➡️  Sending to webhook handler...")
    
    try:
        response = requests.post(
            f"{API_URL}/api/webhooks/email-reply",
            json=webhook_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Message received and processed")
            print(f"   Pending Response ID: {result.get('pending_response_id')}")
            print(f"   Status: {result.get('message')}")
            pending_id = result.get('pending_response_id')
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        print("Make sure the backend server is running on http://localhost:8000")
        return
    
    # Step 2: Check pending responses
    print_section("STEP 2: Check Pending Responses")
    
    try:
        response = requests.get(f"{API_URL}/api/responses/pending")
        if response.status_code == 200:
            result = response.json()
            print(f"📋 Pending Responses: {result['count']}")
            
            if result['count'] > 0:
                for item in result['pending_responses']:
                    print(f"\n   ID: {item['id']}")
                    print(f"   Candidate: {item['candidate']['name']}")
                    print(f"   Channel: {item['channel']}")
                    print(f"   Message: {item['incoming_message'][:60]}...")
                    print(f"   AI Response: {item['generated_content'][:60]}...")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Step 3: Edit the response (optional)
    print_section("STEP 3: Edit Response (Optional)")
    
    print("Original AI Response:")
    print("-" * 70)
    if result['count'] > 0:
        original = result['pending_responses'][0]['generated_content']
        print(original)
    print("-" * 70)
    
    # Simulate editing
    edited_content = """Hi Maria,

Thank you so much for your interest in our ER positions! I'm excited to connect with you.

We currently have excellent ER opportunities available in the Camden and Cherry Hill area, 
with competitive compensation and flexible scheduling options.

I'd love to discuss these in detail with you. Are you available for a quick call this week? 
I can also send you the full job descriptions if you'd like to review them first.

Looking forward to speaking with you!

Best regards,
Sarah Johnson
Healthcare Recruiter
MetaSense Inc.
Phone: (856) 412-6100"""
    
    try:
        response = requests.put(
            f"{API_URL}/api/responses/{pending_id}/edit",
            json={"edited_content": edited_content}
        )
        
        if response.status_code == 200:
            print("\n✏️  Response edited successfully!")
            print("\nEdited Response:")
            print("-" * 70)
            print(edited_content)
            print("-" * 70)
        else:
            print(f"❌ Error editing: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Step 4: Approve and send
    print_section("STEP 4: Approve & Send Response")
    
    print("Would you like to approve and send this response?")
    print("(In the CLI tool, the recruiter would click [A] to approve)")
    
    try:
        response = requests.post(
            f"{API_URL}/api/responses/{pending_id}/approve",
            json={"reviewer_name": "Sarah Johnson"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ {result['message']}")
            print(f"   Response ID: {result['response_id']}")
            print(f"   The email has been sent to the candidate!")
        else:
            print(f"❌ Error approving: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Step 5: Verify it's no longer pending
    print_section("STEP 5: Verify Response Processed")
    
    try:
        response = requests.get(f"{API_URL}/api/responses/pending")
        if response.status_code == 200:
            result = response.json()
            print(f"📋 Remaining Pending Responses: {result['count']}")
            
            if result['count'] == 0:
                print("✅ All responses have been processed!")
            else:
                print(f"   {result['count']} responses still awaiting review")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print_section("✅ Demo Complete!")
    print("\nWhat happened:")
    print("1. ✅ Candidate sent an email")
    print("2. ✅ AI generated a response")
    print("3. ✅ Response was QUEUED (not auto-sent)")
    print("4. ✅ Recruiter reviewed and edited the response")
    print("5. ✅ Recruiter approved → Response sent to candidate")
    print("6. ✅ Conversation logged in database")
    print("\nThis is the INTERACTIVE workflow! 🎉")

if __name__ == "__main__":
    print("\n🚀 Starting Interactive Approval Workflow Demo...")
    print("\n⚠️  Make sure the backend API is running:")
    print("   cd src/backend && python main.py")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
        demo_workflow()
    except KeyboardInterrupt:
        print("\n\n👋 Demo cancelled. Goodbye!")
