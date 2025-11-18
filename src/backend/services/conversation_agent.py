import os
import logging
from openai import OpenAI
from sqlalchemy.orm import Session
from ..models.database import Conversation, Candidate
import re

class ConversationAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.logger = logging.getLogger(__name__)
    
    def generate_response(self, db: Session, candidate_id: int, incoming_message: str, channel: str) -> str:
        """Generate AI response to candidate message"""
        
        # Get candidate info
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return "Thank you for your message! Please contact us at careers@metasenseinc.com"
        
        # Get conversation history
        history = db.query(Conversation).filter(
            Conversation.candidate_id == candidate_id
        ).order_by(Conversation.created_at.desc()).limit(5).all()
        
        # Build context-aware prompt
        prompt = self._build_response_prompt(candidate, incoming_message, history, channel)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Log both messages
            self._log_conversation(db, candidate_id, channel, 'inbound', incoming_message)
            self._log_conversation(db, candidate_id, channel, 'outbound', response_text)
            
            # Update candidate engagement
            self._update_engagement(db, candidate, incoming_message)
            
            return response_text
            
        except Exception as e:
            self.logger.error(f"OpenAI failed: {e}")
            return self._get_fallback_response(candidate, channel)
    
    def _build_response_prompt(self, candidate, incoming_message, history, channel):
        """Build intelligent prompt for response generation"""
        
        history_text = ""
        for conv in reversed(history):  # Show in chronological order
            role = "Candidate" if conv.message_type == 'inbound' else "Recruiter"
            history_text += f"{role}: {conv.content}\n"
        
        prompt = f"""
        You are a friendly recruiter for MetaSense Inc., a healthcare staffing agency.
        
        Candidate: {candidate.first_name} {candidate.last_name}
        Specialty: {candidate.specialty or 'Healthcare'}
        Channel: {channel}
        
        Conversation History:
        {history_text}
        
        New Message from Candidate:
        "{incoming_message}"
        
        Write a natural, helpful response that:
        1. Acknowledges their message
        2. Answers any questions
        3. Gently guides them to register: https://www.metasenseinc.com/register
        4. Sounds personal and professional
        5. Adapts to conversation context
        
        Keep it concise and warm.
        
        Response:
        """
        return prompt
    
    def _log_conversation(self, db: Session, candidate_id: int, channel: str, 
                         message_type: str, content: str):
        """Log conversation to database"""
        conversation = Conversation(
            candidate_id=candidate_id,
            channel=channel,
            message_type=message_type,
            content=content
        )
        db.add(conversation)
        db.commit()
    
    def _update_engagement(self, db: Session, candidate, message: str):
        """Update candidate engagement level"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['interested', 'yes', 'sure', 'okay', 'great']):
            candidate.status = 'interested'
        elif any(word in message_lower for word in ['not interested', 'no thanks', 'stop']):
            candidate.status = 'not_interested'
        else:
            candidate.status = 'engaged'
        
        db.commit()
    
    def _get_fallback_response(self, candidate, channel: str) -> str:
        """Fallback response when AI fails"""
        if channel == 'sms':
            return f"Hi {candidate.first_name}! Thanks for your message. I'd love to help you explore healthcare opportunities. Please register at: https://www.metasenseinc.com/register"
        else:
            return f"""Hello {candidate.first_name},

Thank you for your message! I'd be happy to help you explore healthcare opportunities with MetaSense Inc.

To get started and match you with suitable positions, please register at: https://www.metasenseinc.com/register

Once you've created your profile, our team will review your background and reach out with positions that align with your experience.

Best regards,
The MetaSense Team"""