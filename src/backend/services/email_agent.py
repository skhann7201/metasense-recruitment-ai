import random
from .base_agent import BaseConversationAgent
from .email_templates import MetaSenseTemplates

class EmailConversationAgent(BaseConversationAgent):
    def generate_response(self, candidate, incoming_message: str, conversation_history: list) -> str:
        """Generate AI response to candidate email"""
        
        recruiter_name = random.choice(MetaSenseTemplates.RECRUITERS)
        
        prompt = f"""
        You are {recruiter_name}, a professional healthcare recruiter at MetaSense Inc. in Voorhees, NJ.
        
        COMPANY: MetaSense Inc. - Healthcare Staffing & Recruitment
        LOCATION: Voorhees, New Jersey
        SPECIALTY: Healthcare staffing for hospitals, clinics, and facilities
        ROLE: Healthcare Recruiter
        
        CANDIDATE INFORMATION:
        {self.get_candidate_context(candidate)}
        
        CONVERSATION HISTORY:
        {self._format_conversation_history(conversation_history)}
        
        CANDIDATE'S LATEST MESSAGE:
        "{incoming_message}"
        
        Generate a professional recruiter response that:
        1. Maintains MetaSense's professional healthcare recruiting brand
        2. Addresses their specific questions or concerns
        3. Provides value and builds relationship
        4. Suggests appropriate next steps (phone call, application, etc.)
        5. Uses professional but approachable tone
        6. If they mention salary, discuss ranges generally without commitments
        7. If they mention location, highlight NJ opportunities but be open to other states
        8. Focus on healthcare industry opportunities
        9. Keep response concise but comprehensive (3-4 paragraphs max)
        
        Important: You are a real recruiter - be human, build rapport, but maintain professionalism.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional healthcare recruiter at MetaSense Inc. in Voorhees, NJ. Be helpful, professional, and focused on matching candidates with healthcare opportunities. Build relationships while maintaining professionalism."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip() + MetaSenseTemplates.get_recruiter_signature(recruiter_name)
        
        except Exception as e:
            return self._get_fallback_recruiter_response(recruiter_name)

    def _get_fallback_recruiter_response(self, recruiter_name: str) -> str:
        return f"""Thank you for your message. I appreciate you taking the time to respond.

I'd be happy to help you with any questions about healthcare opportunities at MetaSense. We work with various healthcare facilities and have positions that might match your background and interests.

Please feel free to share what you're looking for in your next role, and I can connect you with relevant opportunities that align with your goals.

""" + MetaSenseTemplates.get_recruiter_signature(recruiter_name)