#!/usr/bin/env python3
"""
Conversation Monitor for MetaSense Inc. Recruitment System

This CLI tool allows recruiters to VIEW what the AI agent is saying
to candidates in real-time, without requiring approval before sending.
"""

import os
import sys
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import SessionLocal, Candidate, Conversation
import requests

class ConversationMonitor:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.db = SessionLocal()
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def display_header(self):
        """Display application header"""
        print("\n" + "="*70)
        print("🏥 MetaSense Inc. - Conversation Monitor")
        print("="*70)
    
    def get_recent_conversations(self, limit=20):
        """Fetch recent conversations from database"""
        return self.db.query(Conversation).order_by(
            Conversation.created_at.desc()
        ).limit(limit).all()
    
    def get_ready_candidates(self):
        """Get candidates ready for recruiter connection"""
        return self.db.query(Candidate).filter(
            Candidate.status == "ready_for_recruiter"
        ).order_by(Candidate.last_contacted.desc()).all()
    
    def display_recent_conversations(self, limit=20):
        """Display recent AI conversations"""
        conversations = self.get_recent_conversations(limit)
        
        if not conversations:
            print("\n📭 No conversations yet.")
            return
        
        print(f"\n📨 Recent Conversations (Last {min(limit, len(conversations))})")
        print("-" * 70)
        
        current_candidate_id = None
        for conv in conversations:
            candidate = self.db.query(Candidate).filter(
                Candidate.id == conv.candidate_id
            ).first()
            
            # Show candidate header when switching candidates
            if current_candidate_id != conv.candidate_id:
                current_candidate_id = conv.candidate_id
                print(f"\n👤 {candidate.first_name} {candidate.last_name} ({candidate.specialty})")
                print(f"   Status: {candidate.status}")
            
            # Show message
            icon = "💬" if conv.message_type == "inbound" else "🤖"
            sender = "Candidate" if conv.message_type == "inbound" else "AI Agent"
            time_str = conv.created_at.strftime("%m/%d %H:%M")
            
            print(f"\n   {icon} [{sender}] - {time_str}")
            print(f"   {conv.content[:100]}..." if len(conv.content) > 100 else f"   {conv.content}")
    
    def display_ready_candidates(self):
        """Display candidates ready for recruiter connection"""
        ready = self.get_ready_candidates()
        
        if not ready:
            print("\n✅ No candidates waiting for recruiter connection.")
            return
        
        print(f"\n🎯 Candidates Ready for Recruiter ({len(ready)})")
        print("-" * 70)
        
        for idx, candidate in enumerate(ready, 1):
            print(f"\n[{idx}] {candidate.first_name} {candidate.last_name}")
            print(f"    📧 Email: {candidate.email}")
            print(f"    📱 Phone: {candidate.mobile_phone}")
            print(f"    💼 {candidate.profession} - {candidate.specialty}")
            print(f"    📍 {candidate.city}, {candidate.state}")
            
            # Get last message
            last_msg = self.db.query(Conversation).filter(
                Conversation.candidate_id == candidate.id
            ).order_by(Conversation.created_at.desc()).first()
            
            if last_msg:
                time_str = last_msg.created_at.strftime("%Y-%m-%d %H:%M")
                print(f"    ⏰ Last contact: {time_str}")
    
    def view_candidate_conversation(self, candidate_id):
        """Display full conversation for a specific candidate"""
        candidate = self.db.query(Candidate).filter(
            Candidate.id == candidate_id
        ).first()
        
        if not candidate:
            print("\n❌ Candidate not found")
            return
        
        self.clear_screen()
        self.display_header()
        
        print(f"\n📋 Full Conversation: {candidate.first_name} {candidate.last_name}")
        print("="*70)
        print(f"Email: {candidate.email}")
        print(f"Phone: {candidate.mobile_phone}")
        print(f"Profession: {candidate.profession} - {candidate.specialty}")
        print(f"Status: {candidate.status}")
        print("-" * 70)
        
        conversations = self.db.query(Conversation).filter(
            Conversation.candidate_id == candidate_id
        ).order_by(Conversation.created_at.asc()).all()
        
        if not conversations:
            print("\nNo messages yet.")
        
        for conv in conversations:
            icon = "💬" if conv.message_type == "inbound" else "🤖"
            sender = "Candidate" if conv.message_type == "inbound" else "AI Agent"
            time_str = conv.created_at.strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n{icon} [{sender}] - {time_str}")
            print(f"{'─' * 70}")
            print(conv.content)
            print(f"{'─' * 70}")
        
        input("\nPress Enter to continue...")
    
    def run(self):
        """Main application loop"""
        while True:
            self.clear_screen()
            self.display_header()
            
            print("\n" + "="*70)
            print("OPTIONS:")
            print("  [1] View Recent Conversations")
            print("  [2] View Candidates Ready for Recruiter")
            print("  [3] View Specific Candidate Conversation")
            print("  [R] Refresh")
            print("  [Q] Quit")
            print("="*70)
            
            choice = input("\nYour choice: ").strip().upper()
            
            if choice == "Q":
                break
            elif choice == "R":
                continue
            elif choice == "1":
                self.clear_screen()
                self.display_header()
                self.display_recent_conversations()
                input("\nPress Enter to continue...")
            elif choice == "2":
                self.clear_screen()
                self.display_header()
                self.display_ready_candidates()
                input("\nPress Enter to continue...")
            elif choice == "3":
                candidate_id = input("\nEnter candidate ID: ").strip()
                try:
                    self.view_candidate_conversation(int(candidate_id))
                except ValueError:
                    print("\n❌ Invalid candidate ID")
                    input("\nPress Enter to continue...")
            else:
                print("\n❌ Invalid choice")
                input("\nPress Enter to continue...")
        
        print("\n👋 Thank you for using MetaSense Conversation Monitor!")
        self.db.close()

def main():
    """Entry point"""
    manager = ConversationMonitor()
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
