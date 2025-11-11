import csv
import os
import time
import requests
import base64
import sqlite3
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI

# ------------------- Load environment variables -------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
ZOOM_PHONE_NUMBER = os.getenv("ZOOM_PHONE_NUMBER")

# ------------------- Initialize Clients -------------------
client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------- Logging Setup -------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'sms_agent_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ------------------- Agentic SMS Recruiting System -------------------
class SMSRecruitingAgent:
    def __init__(self):
        self.memory_db = self._init_memory()
        self.campaign_goals = {
            "daily_message_limit": 100,
            "target_response_rate": 0.12,
            "optimal_send_times": ["09:00", "12:00", "15:00", "17:00"]
        }
        self.performance_metrics = {
            "total_sent": 0,
            "total_failed": 0,
            "response_rate": 0.0,
            "last_campaign": None
        }
        
    def _init_memory(self):
        """Initialize agent memory database"""
        conn = sqlite3.connect('sms_agent_memory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sms_interactions (
                id INTEGER PRIMARY KEY,
                candidate_phone TEXT,
                candidate_name TEXT,
                message_content TEXT,
                message_length INTEGER,
                send_time DATETIME,
                delivery_status TEXT,
                response_received BOOLEAN DEFAULT 0,
                response_content TEXT,
                fit_score REAL,
                priority_level TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_strategies (
                id INTEGER PRIMARY KEY,
                strategy_name TEXT,
                template_type TEXT,
                performance_score REAL,
                usage_count INTEGER,
                last_used DATETIME
            )
        ''')
        
        # Insert default strategies
        cursor.execute('''
            INSERT OR IGNORE INTO message_strategies 
            (strategy_name, template_type, performance_score, usage_count)
            VALUES 
            ('high_touch', 'personalized', 0.8, 0),
            ('professional', 'standard', 0.7, 0),
            ('broad_reach', 'generic', 0.5, 0)
        ''')
        
        conn.commit()
        return conn

    def analyze_candidate(self, contact: Dict) -> Dict:
        """Agent analyzes candidate and decides messaging strategy"""
        fit_score = self._calculate_sms_fit_score(contact)
        strategy = self._select_sms_strategy(contact, fit_score)
        
        # DEBUG: Log the analysis decision
        logger.info(f"🔍 Analyzing {contact.get('FIRST NAME', 'Unknown')}: "
                   f"fit_score={fit_score:.2f}, should_contact={fit_score > 0.2}")
        
        return {
            "should_contact": fit_score > 0.2,  # Lowered threshold for testing
            "fit_score": fit_score,
            "priority": self._assign_priority(fit_score),
            "optimal_time": self._calculate_optimal_time(),
            "message_strategy": strategy,
            "risk_level": self._assess_risk(contact)
        }

    def _calculate_sms_fit_score(self, contact: Dict) -> float:
        """Calculate how suitable candidate is for SMS outreach"""
        score = 0.0
        
        # Phone number validation (MOST IMPORTANT)
        phone = contact.get("MOBILE PHONE", "").strip()
        if self._is_valid_phone(phone):
            score += 0.6  # Increased weight for valid phone
            logger.info(f"📱 Valid phone number: +{score:.1f}")
        else:
            logger.info(f"📱 Invalid phone number: {phone}")
            return 0.0  # Invalid phone = no contact
        
        # Name presence
        first_name = contact.get("FIRST NAME", "").strip()
        if first_name:
            score += 0.2
            logger.info(f"👤 Has first name: +0.2")
        
        # Specialty relevance - BROADENED CRITERIA
        specialty = contact.get("SPECIALTY", "").lower()
        current_job = contact.get("CURRENT JOB", "").lower()
        
        # Expanded to include tech and other roles
        high_demand_roles = [
            "nurse", "therapist", "technician", "physician", "medical", "health",
            "tech", "developer", "engineer", "software", "IT", "data", "analyst",
            "admin", "administrative", "coordinator", "specialist"
        ]
        
        role_text = f"{specialty} {current_job}".lower()
        if any(role in role_text for role in high_demand_roles):
            score += 0.3
            logger.info(f"🎯 Relevant role '{specialty}': +0.3")
        elif specialty or current_job:
            score += 0.1  # Any specified role is better than none
            logger.info(f"🎯 General role '{specialty}': +0.1")
            
        # Experience level bonus
        if any(level in current_job for level in ["senior", "lead", "manager", "director"]):
            score += 0.1
            logger.info(f"Senior role: +0.1")
            
        logger.info(f"Final fit score for {first_name}: {score:.2f}")
        return min(score, 1.0)

    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format - more flexible"""
        if not phone:
            return False
        
        # Clean the phone number
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # More flexible patterns
        patterns = [
            r'^\+1\d{10}$',  # +1XXXXXXXXXX
            r'^1\d{10}$',    # 1XXXXXXXXXX
            r'^\d{10}$',     # XXXXXXXXXX
            r'^\+?\d{11,15}$'  # International formats
        ]
        
        for pattern in patterns:
            if re.match(pattern, clean_phone):
                return True
                
        logger.warning(f"📞 Phone validation failed for: {phone} (cleaned: {clean_phone})")
        return False

    def _select_sms_strategy(self, contact: Dict, fit_score: float) -> Dict:
        """Select optimal messaging strategy based on candidate profile"""
        specialty = contact.get("SPECIALTY", "").lower()
        current_job = contact.get("CURRENT JOB", "").lower()
        
        if fit_score > 0.6:
            return {
                "type": "high_touch",
                "tone": "highly_personalized",
                "include_specialty": True,
                "include_company": True,
                "urgency": "high",
                "follow_up_hours": 24
            }
        elif fit_score > 0.3:
            return {
                "type": "professional", 
                "tone": "professional",
                "include_specialty": True,
                "include_company": True,
                "urgency": "medium",
                "follow_up_hours": 48
            }
        else:
            return {
                "type": "broad_reach",
                "tone": "friendly_general",
                "include_specialty": False,
                "include_company": True,
                "urgency": "low",
                "follow_up_hours": 72
            }

    def _assign_priority(self, fit_score: float) -> str:
        """Assign priority level based on fit score"""
        if fit_score > 0.6:
            return "high"
        elif fit_score > 0.3:
            return "medium"
        else:
            return "low"

    def _calculate_optimal_time(self) -> str:
        """Calculate optimal send time"""
        return "09:00"

    def _assess_risk(self, contact: Dict) -> str:
        """Assess risk level of contacting this candidate"""
        phone = contact.get("MOBILE PHONE", "")
        if not self._is_valid_phone(phone):
            return "high"
        
        # Check if previously contacted (reduce spam)
        if self._was_previously_contacted(phone):
            logger.info(f"Previously contacted: {phone}")
            return "medium"
            
        return "low"

    def _was_previously_contacted(self, phone: str) -> bool:
        """Check if phone number was previously contacted"""
        try:
            cursor = self.memory_db.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM sms_interactions WHERE candidate_phone = ?",
                (phone,)
            )
            count = cursor.fetchone()[0]
            return count > 0
        except:
            return False

    def generate_strategic_sms(self, contact: Dict, strategy: Dict) -> str:
        """Generate strategic SMS message based on agent's analysis"""
        first_name = contact.get("FIRST NAME", "").strip()
        specialty = contact.get("SPECIALTY", "").strip() or "skilled"
        current_job = contact.get("CURRENT JOB", "").strip() or "professional"
        
        prompt = self._build_sms_prompt(first_name, specialty, current_job, strategy)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=120,
                temperature=0.7
            )
            message = response.choices[0].message.content.strip()
            
            # Ensure message is SMS-appropriate length
            if len(message) > 300:
                message = message[:297] + "..."
                
            return message
            
        except Exception as e:
            logger.warning(f"OpenAI API failed, using fallback: {e}")
            return self._get_fallback_sms(first_name, specialty, current_job, strategy)

    def _build_sms_prompt(self, first_name: str, specialty: str, current_job: str, strategy: Dict) -> str:
        """Build strategic prompt for SMS generation"""
        base_url = "https://www.metasenseinc.com/register/"
        
        tone_instructions = {
            "highly_personalized": "Make it sound very personal and tailored to their specific background",
            "professional": "Keep it professional but friendly",
            "friendly_general": "Make it warm and approachable"
        }
        
        prompt = f"""
        Write a short recruiting text message to {first_name}, a {specialty} professional currently working as {current_job}.
        
        Requirements:
        - Tone: {tone_instructions[strategy['tone']]}
        - Mention MetaSense Inc briefly
        - Include this shortened URL: {base_url}
        - Maximum 300 characters
        - Sound like a personal message from a recruiter
        - {f"Reference their {specialty} experience specifically" if strategy['include_specialty'] else "Keep it general"}
        - Clear call-to-action to register
        
        Make it compelling but not pushy.
        """
        
        return prompt

    def _get_fallback_sms(self, first_name: str, specialty: str, current_job: str, strategy: Dict) -> str:
        """Fallback SMS template"""
        base_url = "https://www.metasenseinc.com/register/"
        
        if strategy['tone'] == "highly_personalized":
            return f"Hi {first_name}! Your {specialty} background caught our eye at MetaSense. We have roles matching your skills! Learn more: {base_url}"
        elif strategy['tone'] == "professional":
            return f"Hello {first_name}, MetaSense Inc here. We have opportunities for {specialty} professionals like you. Register to explore: {base_url}"
        else:
            return f"Hi {first_name}! MetaSense has healthcare opportunities. Upload your resume to get matched: {base_url}"

    def process_campaign(self, contacts: List[Dict], specialty_filter: Optional[str] = None) -> Dict:
        """Execute agent-driven SMS campaign"""
        campaign_results = {
            "high_priority_sent": 0,
            "medium_priority_sent": 0,
            "low_priority_sent": 0,
            "failed": 0,
            "skipped": 0
        }
        
        prioritized_contacts = self._prioritize_contacts(contacts, specialty_filter)
        
        # DEBUG: Show what we found
        total_prioritized = sum(len(prioritized_contacts[p]) for p in ["high", "medium", "low"])
        logger.info(f"🎯 Total candidates for contact: {total_prioritized}")
        
        for priority_group in ["high", "medium", "low"]:
            group_contacts = prioritized_contacts[priority_group]
            logger.info(f"Processing {len(group_contacts)} {priority_group} priority contacts")
            
            for contact, analysis in group_contacts:
                if (campaign_results["high_priority_sent"] + 
                    campaign_results["medium_priority_sent"] + 
                    campaign_results["low_priority_sent"] >= self.campaign_goals["daily_message_limit"]):
                    logger.info("Daily message limit reached")
                    break
                    
                success = self._send_agentic_sms(contact, analysis)
                if success:
                    campaign_results[f"{priority_group}_priority_sent"] += 1
                    logger.info(f"Successfully sent to {contact.get('FIRST NAME', 'Unknown')}")
                else:
                    campaign_results["failed"] += 1
                    logger.error(f"Failed to send to {contact.get('FIRST NAME', 'Unknown')}")
                
                time.sleep(2)  # Rate limiting
        
        self._update_performance_metrics(campaign_results)
        return campaign_results

    def _prioritize_contacts(self, contacts: List[Dict], specialty_filter: Optional[str] = None) -> Dict:
        """Analyze and prioritize all contacts"""
        prioritized = {"high": [], "medium": [], "low": []}
        skipped_count = 0
        
        for contact in contacts:
            # Apply specialty filter if provided
            if specialty_filter:
                contact_specialty = contact.get("SPECIALTY", "").lower()
                contact_job = contact.get("CURRENT JOB", "").lower()
                filter_text = f"{contact_specialty} {contact_job}"
                
                if specialty_filter.lower() not in filter_text:
                    logger.info(f"🔍 Filtered out by specialty: {contact.get('FIRST NAME', 'Unknown')} "
                               f"(specialty: '{contact_specialty}', filter: '{specialty_filter}')")
                    skipped_count += 1
                    continue
            
            # Agent analysis
            analysis = self.analyze_candidate(contact)
            
            if analysis["should_contact"]:
                prioritized[analysis["priority"]].append((contact, analysis))
                logger.info(f"Will contact {contact.get('FIRST NAME', 'Unknown')} "
                           f"(priority: {analysis['priority']}, score: {analysis['fit_score']:.2f})")
            else:
                skipped_count += 1
                logger.info(f"⏭Skipping {contact.get('FIRST NAME', 'Unknown')} - "
                           f"low fit score: {analysis['fit_score']:.2f}")
        
        logger.info(f"Prioritization complete: {len(prioritized['high'])} high, "
                   f"{len(prioritized['medium'])} medium, {len(prioritized['low'])} low, "
                   f"{skipped_count} skipped")
        return prioritized

    def _send_agentic_sms(self, contact: Dict, analysis: Dict) -> bool:
        """Send SMS with agent intelligence"""
        try:
            # Generate strategic message
            message = self.generate_strategic_sms(contact, analysis["message_strategy"])
            phone = contact.get("MOBILE PHONE", "").strip()
            
            logger.info(f"Sending SMS to {contact.get('FIRST NAME', 'Unknown')} at {phone}")
            logger.info(f"Message: {message}")
            
            # Send via Zoom
            success = self._send_zoom_sms(phone, message)
            
            # Record interaction
            self._record_sms_interaction(contact, message, analysis, success)
            
            return success
            
        except Exception as e:
            logger.error(f"Agent SMS failed for {contact.get('FIRST NAME', 'Unknown')}: {e}")
            return False

    def _send_zoom_sms(self, to_number: str, message: str) -> bool:
        """Send SMS via Zoom Phone API"""
        token = self._get_zoom_access_token()
        if not token:
            logger.error("No Zoom access token available")
            return False

        url = "https://api.zoom.us/v2/phone/sms"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "to_numbers": [to_number],
            "from_number": ZOOM_PHONE_NUMBER,
            "message": message
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code in (200, 201):
                logger.info(f"SMS sent successfully to {to_number}")
                return True
            else:
                logger.error(f"SMS failed to {to_number}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"SMS error to {to_number}: {e}")
            return False

    def _get_zoom_access_token(self) -> Optional[str]:
        """Get Zoom OAuth token"""
        url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={ZOOM_ACCOUNT_ID}"
        auth_string = f"{ZOOM_CLIENT_ID}:{ZOOM_CLIENT_SECRET}"
        headers = {
            "Authorization": "Basic " + base64.b64encode(auth_string.encode()).decode()
        }

        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            token = response.json()["access_token"]
            logger.info("🔑 Successfully obtained Zoom access token")
            return token
        except Exception as e:
            logger.error(f"Zoom token failed: {e}")
            return None

    def _record_sms_interaction(self, contact: Dict, message: str, analysis: Dict, success: bool):
        """Record SMS interaction in agent memory"""
        try:
            cursor = self.memory_db.cursor()
            cursor.execute('''
                INSERT INTO sms_interactions 
                (candidate_phone, candidate_name, message_content, message_length, 
                 send_time, delivery_status, fit_score, priority_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                contact.get("MOBILE PHONE"),
                f"{contact.get('FIRST NAME', '')} {contact.get('LAST NAME', '')}",
                message,
                len(message),
                datetime.now(),
                "sent" if success else "failed",
                analysis["fit_score"],
                analysis["priority"]
            ))
            self.memory_db.commit()
            logger.info(f"💾 Recorded interaction for {contact.get('FIRST NAME', 'Unknown')}")
        except Exception as e:
            logger.error(f"Failed to record interaction: {e}")

    def _update_performance_metrics(self, campaign_results: Dict):
        """Update agent performance metrics"""
        total_sent = (campaign_results["high_priority_sent"] + 
                     campaign_results["medium_priority_sent"] + 
                     campaign_results["low_priority_sent"])
        
        self.performance_metrics["total_sent"] += total_sent
        self.performance_metrics["total_failed"] += campaign_results["failed"]
        self.performance_metrics["last_campaign"] = datetime.now()
        
        logger.info(f"📊 Campaign completed: {total_sent} sent, {campaign_results['failed']} failed")

    def get_agent_report(self) -> Dict:
        """Generate agent performance report"""
        try:
            cursor = self.memory_db.cursor()
            cursor.execute("SELECT COUNT(*) FROM sms_interactions WHERE delivery_status = 'sent'")
            total_sent = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sms_interactions WHERE response_received = 1")
            total_responses = cursor.fetchone()[0]
            
            response_rate = total_responses / total_sent if total_sent > 0 else 0
            
            return {
                "total_interactions": total_sent + self.performance_metrics["total_failed"],
                "successful_messages": total_sent,
                "failed_messages": self.performance_metrics["total_failed"],
                "estimated_response_rate": response_rate,
                "last_campaign": self.performance_metrics["last_campaign"],
                "agent_goals": self.campaign_goals
            }
        except:
            return {"error": "Could not generate report"}

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'memory_db'):
            self.memory_db.close()

# ------------------- Original CSV Function -------------------
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

# ------------------- Main Execution -------------------
def main():
    """Main function to run the agentic SMS system"""
    try:
        # Initialize the SMS Agent
        agent = SMSRecruitingAgent()
        logger.info("🤖 SMS Recruiting Agent initialized")
        
        # Load contacts
        csv_file = "test_contact.csv"
        contacts = read_contacts(csv_file)
        
        if not contacts:
            logger.error("No contacts found. Please check your CSV file.")
            return
        
        # Get filter input
        specialty_filter = input("Enter specialty to filter by (or press Enter for all): ").strip()
        specialty_filter = specialty_filter if specialty_filter else None
        
        if specialty_filter:
            logger.info(f"Applying specialty filter: '{specialty_filter}'")
        
        # Run agentic campaign
        results = agent.process_campaign(contacts, specialty_filter)
        
        # Generate report
        report = agent.get_agent_report()
        
        print("\n" + "="*50)
        print("SMS AGENT CAMPAIGN REPORT")
        print("="*50)
        print(f"High Priority Sent: {results['high_priority_sent']}")
        print(f"Medium Priority Sent: {results['medium_priority_sent']}")
        print(f"Low Priority Sent: {results['low_priority_sent']}")
        print(f"Total Failed: {results['failed']}")
        print(f"Total Skipped: {results['skipped']}")
        print(f"Estimated Response Rate: {report.get('estimated_response_rate', 0):.1%}")
        print("="*50)
        
        # Clean up
        agent.close()
        
    except KeyboardInterrupt:
        logger.info("⏹Campaign interrupted by user")
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    finally:
        if 'agent' in locals():
            agent.close()

if __name__ == "__main__":
    main()