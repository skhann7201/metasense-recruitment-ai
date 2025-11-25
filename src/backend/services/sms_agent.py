import random
from .base_agent import BaseConversationAgent
from .email_templates import MetaSenseTemplates

class SMSConversationAgent(BaseConversationAgent):
    def generate_response(self, candidate, incoming_message: str, conversation_history: list) -> str:
        """Generate AI response to candidate SMS"""
        
        recruiter_name = random.choice(MetaSenseTemplates.RECRUITERS)
        
        prompt = f"""
        You are {recruiter_name}, a healthcare recruiter at MetaSense Inc. Texting a candidate.
        
        CANDIDATE:
        {self.get_candidate_context(candidate)}
        
        CONVERSATION HISTORY:
        {self._format_conversation_history(conversation_history)}
        
        CANDIDATE'S TEXT:
        "{incoming_message}"
        
        Generate a friendly, casual SMS response that:
        1. Is very short (1-2 sentences max, under 160 characters)
        2. Uses conversational, friendly language
        3. Answers their question directly if they asked one
        4. Keeps the conversation going naturally
        5. If they seem interested, suggest a quick call or application
        6. If they ask about opportunities, mention healthcare roles briefly
        7. Sign with just your first name
        8. NO formal greetings or closings beyond your name
        
        Be human and conversational - this is a text message!
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a friendly healthcare recruiter texting a candidate. Keep it very casual, short, and conversational. Use emojis sparingly if appropriate."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=60,
                temperature=0.8
            )
            
            # Ensure it's short enough for SMS
            message = response.choices[0].message.content.strip()
            if len(message) > 150:
                message = message[:147] + "..."
                
            return message + f" -{recruiter_name}"
        
        except Exception as e:
            return self._get_fallback_sms_response(recruiter_name)
    
    def _get_fallback_sms_response(self, recruiter_name: str) -> str:
        return f"Thanks for your message! I'd be happy to help. What type of healthcare role are you looking for? -{recruiter_name}"