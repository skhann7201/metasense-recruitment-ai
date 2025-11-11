import csv
import os
import smtplib
import time
import sqlite3
import json
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from openai import OpenAI

# ------------------- Load environment variables --------------------
load_dotenv()
EMAIL_ADDRESS = os.getenv("IONOS_EMAIL")
EMAIL_PASSWORD = os.getenv("IONOS_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ------------------- Initialize OpenAI client -----------------------
client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------- Logging Setup --------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'recruiting_agent_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ------------------- Original CSV Function (Fixed) -------------------
def read_contacts(csv_file):
    """Read contacts from CSV file"""
    contacts = []
    try:
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                contacts.append(row)
        logger.info(f"Loaded {len(contacts)} contacts from {csv_file}")
        return contacts
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file}")
        return []
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return []

# ------------------- Original Email Function -------------------
def send_email(to_email, subject, body):
    """Send email using SMTP"""
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.ionos.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False

# ------------------- AGENTIC SYSTEM -------------------
class RecruitingAgent:
    def __init__(self):
        self.memory_db = self._init_memory()
        self.goals = {
            "response_rate": 0.15,
            "conversions": 0.05,
            "daily_capacity": 50
        }
        self.performance_history = []
        
    def _init_memory(self):
        """Initialize agent memory for learning"""
        conn = sqlite3.connect('agent_memory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidate_interactions (
                id INTEGER PRIMARY KEY,
                candidate_email TEXT,
                interaction_type TEXT,
                content TEXT,
                response_received BOOLEAN,
                response_content TEXT,
                timestamp DATETIME,
                outcome TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_memory (
                id INTEGER PRIMARY KEY,
                strategy_type TEXT,
                performance_metric REAL,
                sample_size INTEGER,
                last_used DATETIME
            )
        ''')
        
        conn.commit()
        return conn

    def analyze_candidate_fit(self, candidate_data: dict) -> dict:
        """Agent decides if and how to contact candidate"""
        fit_score = self._calculate_fit_score(candidate_data)
        contact_strategy = self._select_contact_strategy(candidate_data, fit_score)
        
        return {
            "should_contact": fit_score > 0.3,  # Lower threshold for testing
            "fit_score": fit_score,
            "recommended_channel": contact_strategy["channel"],
            "message_tone": contact_strategy["tone"],
            "priority": "high" if fit_score > 0.7 else "medium" if fit_score > 0.4 else "low"
        }

    def _calculate_fit_score(self, candidate: dict) -> float:
        """Agent evaluates candidate suitability"""
        score = 0.0
        
        # Analyze specialty match
        specialty = candidate.get("SPECIALTY", "").lower()
        high_demand_specialties = ["nurse", "therapist", "technician", "physician", "medical", "health"]
        if any(s in specialty for s in high_demand_specialties):
            score += 0.4
        elif specialty:  # Any specialty is better than none
            score += 0.2
        
        # Check for email validity
        email = candidate.get("EMAIL", "")
        if email and "@" in email:
            score += 0.3
        
        # Name presence
        if candidate.get("FIRST NAME", "").strip():
            score += 0.3
            
        return min(score, 1.0)

    def _select_contact_strategy(self, candidate: dict, fit_score: float) -> dict:
        """Agent chooses best approach based on candidate profile"""
        specialty = candidate.get("SPECIALTY", "").lower()
        
        if fit_score > 0.7:
            return {
                "channel": "email",
                "tone": "highly_personalized", 
                "follow_up_days": 3,
                "template": "premium_recruitment"
            }
        elif fit_score > 0.4:
            return {
                "channel": "email", 
                "tone": "professional",
                "follow_up_days": 7,
                "template": "standard_recruitment"
            }
        else:
            return {
                "channel": "email",
                "tone": "general",
                "follow_up_days": 14,
                "template": "newsletter_style"
            }

    def generate_adaptive_email(self, candidate: dict, strategy: dict) -> str:
        """Agent creates context-aware email content"""
        specialty = candidate.get("SPECIALTY", "healthcare")
        first_name = candidate.get("FIRST NAME", "there")
        
        prompt = f"""
        Write a professional recruiting email to {first_name} who is a {specialty} professional.
        
        Tone: {strategy['tone']}
        Goal: Get them to register at https://www.metasenseinc.com/register
        
        Make it personalized for their specialty: {specialty}
        Keep it concise and professional.
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI API failed, using fallback: {e}")
            return self._get_fallback_email(candidate, strategy)

    def _get_fallback_email(self, candidate: dict, strategy: dict) -> str:
        """Fallback email content"""
        first_name = candidate.get("FIRST NAME", "there")
        specialty = candidate.get("SPECIALTY", "healthcare")
        
        return f"""Hello {first_name},

I hope this message finds you well! I'm reaching out from MetaSense Inc., a healthcare staffing agency dedicated to connecting skilled {specialty} professionals like you with rewarding roles in hospitals, clinics, and healthcare organizations.

We currently have opportunities for {specialty} professionals, and we'd love to help you find a role that fits your experience and goals.

You can easily create a profile and upload your resume here: https://www.metasenseinc.com/register. Once registered, our team will review your background and reach out with positions that match your expertise.

Looking forward to connecting with you!

Best regards,
The MetaSense Team
"""

    def _generate_strategic_subject(self, candidate: dict, strategy: dict) -> str:
        """Generate strategic subject line based on candidate and strategy"""
        first_name = candidate.get("FIRST NAME", "")
        specialty = candidate.get("SPECIALTY", "Healthcare")
        
        if strategy["tone"] == "highly_personalized":
            return f"Opportunity for {specialty} Professional {first_name} - MetaSense Inc."
        elif strategy["tone"] == "professional":
            return f"Healthcare Opportunities for {specialty} Professionals"
        else:
            return "Exciting Healthcare Opportunities with MetaSense Inc."

    def process_campaign_strategy(self, contacts: list) -> dict:
        """Agent plans and executes campaign strategy"""
        campaign_plan = {
            "high_priority": [],
            "medium_priority": [], 
            "low_priority": [],
            "deferred": []
        }
        
        for contact in contacts:
            # Skip invalid emails
            if not contact.get("EMAIL") or "@" not in contact.get("EMAIL", ""):
                continue
                
            decision = self.analyze_candidate_fit(contact)
            
            if decision["should_contact"]:
                if decision["priority"] == "high":
                    campaign_plan["high_priority"].append((contact, decision))
                elif decision["priority"] == "medium":
                    campaign_plan["medium_priority"].append((contact, decision))
                else:
                    campaign_plan["low_priority"].append((contact, decision))
            else:
                campaign_plan["deferred"].append(contact)
        
        logger.info(f"Campaign plan: {len(campaign_plan['high_priority'])} high, "
                   f"{len(campaign_plan['medium_priority'])} medium, "
                   f"{len(campaign_plan['low_priority'])} low priority")
        
        return self._execute_priority_strategy(campaign_plan)

    def _execute_priority_strategy(self, campaign_plan: dict) -> dict:
        """Agent executes contacts in strategic order"""
        results = {
            "sent": [],
            "failed": [],
            "deferred": []
        }
        
        # Execute high priority first
        for contact, decision in campaign_plan["high_priority"]:
            if self._send_agentic_email(contact, decision):
                results["sent"].append(contact)
                time.sleep(2)  # Rate limiting
            else:
                results["failed"].append(contact)
        
        # Then medium priority
        for contact, decision in campaign_plan["medium_priority"]:
            if len(results["sent"]) < self.goals["daily_capacity"]:
                if self._send_agentic_email(contact, decision):
                    results["sent"].append(contact)
                    time.sleep(2)
                else:
                    results["failed"].append(contact)
            else:
                results["deferred"].append(contact)
        
        # Finally low priority if capacity remains
        for contact, decision in campaign_plan["low_priority"]:
            if len(results["sent"]) < self.goals["daily_capacity"]:
                if self._send_agentic_email(contact, decision):
                    results["sent"].append(contact)
                    time.sleep(2)
                else:
                    results["failed"].append(contact)
            else:
                results["deferred"].append(contact)
        
        self._learn_from_campaign(results)
        return results

    def _send_agentic_email(self, contact: dict, decision: dict) -> bool:
        """Agent-driven email sending with decision making"""
        try:
            strategy = self._select_contact_strategy(contact, decision["fit_score"])
            email_content = self.generate_adaptive_email(contact, strategy)
            subject = self._generate_strategic_subject(contact, strategy)
            
            success = send_email(contact["EMAIL"], subject, email_content)
            self._record_interaction(contact, strategy, email_content, success)
            
            return success
            
        except Exception as e:
            logger.error(f"Agent failed to process {contact.get('EMAIL', 'unknown')}: {e}")
            return False

    def _record_interaction(self, contact: dict, strategy: dict, content: str, success: bool):
        """Record interaction in agent memory"""
        try:
            cursor = self.memory_db.cursor()
            cursor.execute('''
                INSERT INTO candidate_interactions 
                (candidate_email, interaction_type, content, response_received, timestamp, outcome)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                contact.get("EMAIL"),
                "email",
                content,
                False,  # response_received
                datetime.now(),
                "sent" if success else "failed"
            ))
            self.memory_db.commit()
        except Exception as e:
            logger.error(f"Failed to record interaction: {e}")

    def _learn_from_campaign(self, results: dict):
        """Agent learns from campaign outcomes"""
        total_attempted = len(results["sent"]) + len(results["failed"])
        if total_attempted > 0:
            success_rate = len(results["sent"]) / total_attempted
            
            self.performance_history.append({
                "timestamp": datetime.now(),
                "success_rate": success_rate,
                "sent": len(results["sent"]),
                "failed": len(results["failed"]),
                "deferred": len(results["deferred"])
            })
            
            logger.info(f"Campaign completed: {len(results['sent'])} sent, "
                       f"{len(results['failed'])} failed, {len(results['deferred'])} deferred")
            
            if len(self.performance_history) > 3:
                avg_rate = sum(p["success_rate"] for p in self.performance_history[-3:]) / 3
                if avg_rate < self.goals["response_rate"] * 0.5:
                    logger.info("Agent: Adjusting strategy due to low performance")

    def get_agent_report(self) -> dict:
        """Generate agent performance insights"""
        return {
            "total_campaigns": len(self.performance_history),
            "recent_performance": self.performance_history[-3:] if self.performance_history else [],
            "current_goals": self.goals,
            "memory_entries": self._get_memory_stats()
        }

    def _get_memory_stats(self) -> int:
        """Get number of interactions in memory"""
        try:
            cursor = self.memory_db.cursor()
            cursor.execute("SELECT COUNT(*) FROM candidate_interactions")
            return cursor.fetchone()[0]
        except:
            return 0

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'memory_db'):
            self.memory_db.close()

# ------------------- Main Execution -------------------
def main():
    """Main function to run the agentic recruiting system"""
    try:
        # Initialize the AI agent
        agent = RecruitingAgent()
        logger.info("🤖 Recruiting Agent initialized")
        
        # Load contacts
        csv_file = "test_contact.csv"
        contacts = read_contacts(csv_file)
        
        if not contacts:
            logger.error("No contacts found. Please check your CSV file.")
            return
        
        logger.info(f"📋 Loaded {len(contacts)} contacts for processing")
        
        # Let the agent plan and execute the campaign
        results = agent.process_campaign_strategy(contacts)
        
        # Get intelligent report
        report = agent.get_agent_report()
        
        print("\n" + "="*50)
        print("🤖 AGENT CAMPAIGN REPORT")
        print("="*50)
        print(f"Emails Sent: {len(results['sent'])}")
        print(f"Emails Failed: {len(results['failed'])}")
        print(f"Contacts Deferred: {len(results['deferred'])}")
        print(f"Total Campaigns in Memory: {report['total_campaigns']}")
        print(f"Interactions Recorded: {report['memory_entries']}")
        print("="*50)
        
        # Clean up
        agent.close()
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    finally:
        if 'agent' in locals():
            agent.close()

if __name__ == "__main__":
    main()