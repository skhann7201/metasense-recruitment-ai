# email_handler.py
import imaplib
import email
from email.header import decode_header
import re
from response_agent import ResponseAgent
from database import ConversationDB
import logging

class EmailResponseHandler:
    def __init__(self):
        self.agent = ResponseAgent()
        self.db = ConversationDB()
        self.logger = logging.getLogger(__name__)
    
    def check_responses(self):
        """Check for email responses from candidates"""
        # This would connect to your email via IMAP
        # For now, here's the structure:
        
        try:
            # Connect to email server (example with Gmail)
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
            mail.select("inbox")
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            
            for email_id in email_ids:
                self._process_email_response(mail, email_id)
                
            mail.close()
            mail.logout()
            
        except Exception as e:
            self.logger.error(f"Email checking failed: {e}")
    
    def _process_email_response(self, mail, email_id):
        """Process individual email response"""
        try:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            email_body = msg_data[0][1]
            msg = email.message_from_bytes(email_body)
            
            # Extract email details
            subject = self._decode_header(msg["Subject"])
            from_email = self._extract_email(msg["From"])
            body = self._extract_body(msg)
            
            # Find candidate in database
            candidate_id = self._find_candidate_by_email(from_email)
            
            if candidate_id:
                # Generate AI response
                response = self.agent.generate_response(
                    candidate_id, 
                    body, 
                    'email',
                    {'subject': subject, 'from_email': from_email}
                )
                
                # Send response (using your existing email function)
                self._send_email_response(from_email, subject, response)
                
                self.logger.info(f"Processed email response from {from_email}")
            
        except Exception as e:
            self.logger.error(f"Failed to process email {email_id}: {e}")
    
    def _find_candidate_by_email(self, email_address: str) -> Optional[int]:
        """Find candidate ID by email address"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM candidates WHERE email = ?', (email_address,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None