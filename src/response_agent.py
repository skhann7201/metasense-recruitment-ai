# response_agent.py
import os
import logging
from openai import OpenAI
from database import ConversationDB
from typing import Dict, Optional

class ResponseAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.db = ConversationDB()
        self.logger = logging.getLogger(__name__)
    
    def generate_response(self, candidate_id: int, incoming_message: str, 
                         channel: str, context: Dict = None) -> str:
        """Generate intelligent response to candidate message"""
        
        # Get conversation history
        history = self.db.get_conversation_history(candidate_id)
        
        # Get candidate info
        candidate_info = self._get_candidate_info(candidate_id)
        
        # Build context-aware prompt
        prompt = self._build_response_prompt(
            candidate_info, 
            incoming_message, 
            history, 
            channel,
            context
        )
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Log the interaction
            self.db.log_conversation(candidate_id, channel, 'inbound', incoming_message)
            self.db.log_conversation(candidate_id, channel, 'outbound', response_text)
            
            # Update candidate status based on response
            self._update_candidate_engagement(candidate_id, incoming_message)
            
            return response_text
            
        except Exception as e:
            self.logger.error(f"OpenAI response generation failed: {e}")
            return self._get_fallback_response(incoming_message, channel)
    
    def _build_response_prompt(self, candidate_info: Dict, incoming_message: str, 
                              history: List[Dict], channel: str, context: Dict) -> str:
        """Build intelligent prompt for response generation"""
        
        # Build conversation history context
        history_context = ""
        for msg in history[-5:]:  # Last 5 messages
            role = "Candidate" if msg['message_type'] == 'inbound' else "Recruiter"
            history_context += f"{role}: {msg['content']}\n"
        
        prompt = f"""
        You are a friendly, professional recruiter for MetaSense Inc., a healthcare staffing agency.
        
        Candidate: {candidate_info['first_name']} {candidate_info['last_name']}
        Specialty: {candidate_info.get('specialty', 'Not specified')}
        Current Role: {candidate_info.get('current_job', 'Not specified')}
        Channel: {channel}
        
        Recent Conversation:
        {history_context}
        
        New Message from Candidate:
        "{incoming_message}"
        
        Your task: Write a natural, helpful response that:
        1. Acknowledges their message appropriately
        2. Answers any questions they have
        3. Gently guides them toward registration: https://www.metasenseinc.com/register
        4. Maintains professional but friendly tone
        5. Adapts to the conversation context
        
        Important:
        - Keep it concise but personal
        - Don't be pushy or salesy
        - If they're interested, provide clear next steps
        - If they have questions, answer helpfully
        - Always be encouraging and supportive
        
        Response (write as if you're texting/emailing directly to them):
        """
        
        return prompt
    
    def _get_candidate_info(self, candidate_id: int) -> Dict:
        """Get candidate information from database"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT first_name, last_name, specialty, current_job, status 
            FROM candidates WHERE id = ?
        ''', (candidate_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'first_name': row[0],
                'last_name': row[1],
                'specialty': row[2],
                'current_job': row[3],
                'status': row[4]
            }
        return {}
    
    def _update_candidate_engagement(self, candidate_id: int, message: str):
        """Update candidate engagement level based on their response"""
        positive_indicators = ['interested', 'yes', 'sure', 'okay', 'great', 'thanks', 'when', 'how']
        negative_indicators = ['not interested', 'no thanks', 'stop', 'unsubscribe']
        
        message_lower = message.lower()
        
        if any(indicator in message_lower for indicator in positive_indicators):
            self.db.update_candidate_status(candidate_id, 'interested')
        elif any(indicator in message_lower for indicator in negative_indicators):
            self.db.update_candidate_status(candidate_id, 'not_interested')
        else:
            self.db.update_candidate_status(candidate_id, 'engaged')
    
    def _get_fallback_response(self, incoming_message: str, channel: str) -> str:
        """Fallback response when AI fails"""
        if channel == 'sms':
            return "Thanks for your message! I'd be happy to help you explore healthcare opportunities. Could you please register at https://www.metasenseinc.com/register so we can find the best roles for you?"
        else:
            return """Thank you for your message!

I'd be happy to help you explore healthcare opportunities with MetaSense Inc. To get started and match you with suitable positions, please register at: https://www.metasenseinc.com/register

Once you've created your profile, our team will review your background and reach out with positions that align with your experience.

Best regards,
The MetaSense Team"""