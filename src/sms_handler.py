# sms_handler.py
from twilio.rest import Client
from response_agent import ResponseAgent
from database import ConversationDB
import os
import logging

class SMSResponseHandler:
    def __init__(self):
        self.agent = ResponseAgent()
        self.db = ConversationDB()
        self.client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        self.logger = logging.getLogger(__name__)
    
    def check_sms_responses(self):
        """Check for SMS responses from candidates"""
        try:
            # Get recent messages (last 24 hours)
            messages = self.client.messages.list(
                date_sent='2024-01-01',  # Adjust date as needed
                to=os.getenv('TWILIO_PHONE_NUMBER')
            )
            
            for message in messages:
                if message.direction == 'inbound':
                    self._process_sms_response(message)
                    
        except Exception as e:
            self.logger.error(f"SMS response checking failed: {e}")
    
    def _process_sms_response(self, message):
        """Process individual SMS response"""
        try:
            from_number = message.from_
            message_body = message.body
            
            # Find candidate in database
            candidate_id = self._find_candidate_by_phone(from_number)
            
            if candidate_id:
                # Generate AI response
                response = self.agent.generate_response(
                    candidate_id, 
                    message_body, 
                    'sms'
                )
                
                # Send SMS response
                self._send_sms_response(from_number, response)
                
                self.logger.info(f"Processed SMS response from {from_number}")
            
        except Exception as e:
            self.logger.error(f"Failed to process SMS from {message.from_}: {e}")
    
    def _find_candidate_by_phone(self, phone_number: str) -> Optional[int]:
        """Find candidate ID by phone number"""
        # Clean phone number for matching
        clean_phone = re.sub(r'[^\d+]', '', phone_number)
        
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM candidates WHERE phone = ?', (clean_phone,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def _send_sms_response(self, to_number: str, message: str):
        """Send SMS response via Twilio"""
        try:
            self.client.messages.create(
                body=message,
                from_=os.getenv('TWILIO_PHONE_NUMBER'),
                to=to_number
            )
            self.logger.info(f"Sent SMS response to {to_number}")
        except Exception as e:
            self.logger.error(f"Failed to send SMS to {to_number}: {e}")