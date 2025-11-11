# recruitment_orchestrator.py
import time
import schedule
from email_handler import EmailResponseHandler
from sms_handler import SMSResponseHandler
from database import ConversationDB
import logging

class RecruitmentOrchestrator:
    def __init__(self):
        self.email_handler = EmailResponseHandler()
        self.sms_handler = SMSResponseHandler()
        self.db = ConversationDB()
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self):
        """Start monitoring for candidate responses"""
        self.logger.info("Starting Recruitment Agent Monitoring...")
        
        # Schedule regular checks
        schedule.every(5).minutes.do(self._check_responses)
        schedule.every(1).hours.do(self._generate_daily_report)
        
        while True:
            schedule.run_pending()
            time.sleep(120)  #Check every minute
    
    def _check_responses(self):
        """Check for responses on all channels"""
        self.logger.info("Checking for candidate responses...")
        
        try:
            self.email_handler.check_responses()
            self.sms_handler.check_sms_responses()
        except Exception as e:
            self.logger.error(f"Response checking failed: {e}")
    
    def _generate_daily_report(self):
        """Generate daily activity report"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        # Get today's stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_conversations,
                COUNT(DISTINCT candidate_id) as active_candidates,
                SUM(CASE WHEN message_type = 'inbound' THEN 1 ELSE 0 END) as inbound_messages
            FROM conversations 
            WHERE DATE(created_at) = DATE('now')
        ''')
        
        stats = cursor.fetchone()
        conn.close()
        
        self.logger.info(f"Daily Report: {stats[0]} conversations, "
                        f"{stats[1]} active candidates, {stats[2]} inbound messages")