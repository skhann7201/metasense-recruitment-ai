#!/usr/bin/env python3
"""
Interactive Response Manager for MetaSense Inc. Recruitment System

This CLI tool allows recruiters to review, edit, and approve AI-generated
responses to candidate messages before they are sent.
"""

import os
import sys
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import SessionLocal, Candidate, PendingResponse, Conversation
import requests

class InteractiveResponseManager:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.db = SessionLocal()
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def display_header(self):
        """Display application header"""
        print("\n" + "="*70)
        print("🏥 MetaSense Inc. - Interactive Response Manager")
        print("="*70)
    
    def get_pending_responses(self):
        """Fetch all pending responses from database"""
        return self.db.query(PendingResponse).filter(
            PendingResponse.status == "pending"
        ).order_by(PendingResponse.created_at.desc()).all()
    
    def display_pending_list(self, pending_responses):
        """Display list of pending responses"""
        if not pending_responses:
            print("\n✅ No pending responses! All caught up.")
            return False
        
        print(f"\n📋 Pending Responses: {len(pending_responses)}")
        print("-" * 70)
        
        for idx, response in enumerate(pending_responses, 1):
            candidate = self.db.query(Candidate).filter(
                Candidate.id == response.candidate_id
            ).first()
            
            print(f"\n[{idx}] ID: {response.id} | {response.channel.upper()}")
            print(f"    Candidate: {candidate.first_name} {candidate.last_name}")
            print(f"    Specialty: {candidate.specialty}")
            if response.channel == "email":
                print(f"    Email: {response.recipient_email}")
            else:
                print(f"    Phone: {response.recipient_phone}")
            print(f"    Created: {response.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
    
    def display_response_details(self, response):
        """Display detailed view of a pending response"""
        self.clear_screen()
        self.display_header()
        
        candidate = self.db.query(Candidate).filter(
            Candidate.id == response.candidate_id
        ).first()
        
        print(f"\n📧 Response Details (ID: {response.id})")
        print("="*70)
        
        # Candidate Info
        print(f"\n👤 CANDIDATE INFORMATION:")
        print(f"   Name: {candidate.first_name} {candidate.last_name}")
        print(f"   Profession: {candidate.profession}")
        print(f"   Specialty: {candidate.specialty}")
        print(f"   Location: {candidate.city}, {candidate.state}")
        if response.channel == "email":
            print(f"   Email: {response.recipient_email}")
        else:
            print(f"   Phone: {response.recipient_phone}")
        
        # Channel & Subject
        print(f"\n📱 CHANNEL: {response.channel.upper()}")
        if response.subject:
            print(f"   Subject: {response.subject}")
        
        # Incoming Message
        print(f"\n💬 CANDIDATE'S MESSAGE:")
        print("-" * 70)
        print(response.incoming_message)
        print("-" * 70)
        
        # AI Generated Response
        print(f"\n🤖 AI-GENERATED RESPONSE:")
        print("-" * 70)
        content = response.edited_content if response.edited_content else response.generated_content
        print(content)
        print("-" * 70)
        
        if response.edited_content:
            print("\n⚠️  This response has been edited")
    
    def edit_response_interactive(self, response):
        """Allow user to edit the response"""
        print("\n✏️  EDIT MODE")
        print("-" * 70)
        print("Current response:")
        current_content = response.edited_content if response.edited_content else response.generated_content
        print(current_content)
        print("-" * 70)
        
        print("\nEnter your edited response (type 'END' on a new line when done):")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        
        new_content = "\n".join(lines).strip()
        
        if new_content:
            response.edited_content = new_content
            self.db.commit()
            print("\n✅ Response updated successfully!")
        else:
            print("\n❌ No changes made (empty content)")
        
        input("\nPress Enter to continue...")
    
    def approve_and_send(self, response, reviewer_name):
        """Approve and send the response"""
        try:
            response_data = {
                "reviewer_name": reviewer_name
            }
            
            api_response = requests.post(
                f"{self.api_url}/api/responses/{response.id}/approve",
                json=response_data
            )
            
            if api_response.status_code == 200:
                print("\n✅ Response approved and sent successfully!")
                return True
            else:
                print(f"\n❌ Failed to send response: {api_response.text}")
                return False
        except Exception as e:
            print(f"\n❌ Error sending response: {e}")
            return False
    
    def reject_response(self, response, reviewer_name):
        """Reject the response without sending"""
        try:
            response_data = {
                "reviewer_name": reviewer_name
            }
            
            api_response = requests.post(
                f"{self.api_url}/api/responses/{response.id}/reject",
                json=response_data
            )
            
            if api_response.status_code == 200:
                print("\n✅ Response rejected successfully!")
                return True
            else:
                print(f"\n❌ Failed to reject response: {api_response.text}")
                return False
        except Exception as e:
            print(f"\n❌ Error rejecting response: {e}")
            return False
    
    def review_response(self, response, reviewer_name):
        """Interactive review session for a single response"""
        while True:
            self.display_response_details(response)
            
            print("\n" + "="*70)
            print("OPTIONS:")
            print("  [A] Approve & Send")
            print("  [E] Edit Response")
            print("  [R] Reject (Don't Send)")
            print("  [B] Back to List")
            print("="*70)
            
            choice = input("\nYour choice: ").strip().upper()
            
            if choice == "A":
                confirm = input("\n⚠️  Send this response? (yes/no): ").strip().lower()
                if confirm == "yes":
                    if self.approve_and_send(response, reviewer_name):
                        input("\nPress Enter to continue...")
                        return
            
            elif choice == "E":
                self.edit_response_interactive(response)
                # Refresh response from DB
                self.db.refresh(response)
            
            elif choice == "R":
                confirm = input("\n⚠️  Reject this response? (yes/no): ").strip().lower()
                if confirm == "yes":
                    if self.reject_response(response, reviewer_name):
                        input("\nPress Enter to continue...")
                        return
            
            elif choice == "B":
                return
            
            else:
                print("\n❌ Invalid choice. Please try again.")
                input("\nPress Enter to continue...")
    
    def run(self):
        """Main application loop"""
        print("\n🏥 Welcome to MetaSense Interactive Response Manager")
        reviewer_name = input("Enter your name: ").strip()
        
        if not reviewer_name:
            reviewer_name = "Recruiter"
        
        while True:
            self.clear_screen()
            self.display_header()
            
            pending_responses = self.get_pending_responses()
            
            if not self.display_pending_list(pending_responses):
                print("\nPress Enter to refresh or 'Q' to quit...")
                choice = input().strip().upper()
                if choice == "Q":
                    break
                continue
            
            print("\n" + "="*70)
            print("Enter response number to review, 'R' to refresh, or 'Q' to quit")
            choice = input("\nYour choice: ").strip().upper()
            
            if choice == "Q":
                break
            elif choice == "R":
                continue
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(pending_responses):
                        self.review_response(pending_responses[idx], reviewer_name)
                    else:
                        print("\n❌ Invalid number")
                        input("\nPress Enter to continue...")
                except ValueError:
                    print("\n❌ Invalid input")
                    input("\nPress Enter to continue...")
        
        print("\n👋 Thank you for using MetaSense Response Manager!")
        self.db.close()

def main():
    """Entry point"""
    manager = InteractiveResponseManager()
    try:
        manager.run()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
        manager.db.close()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        manager.db.close()
        sys.exit(1)

if __name__ == "__main__":
    main()
