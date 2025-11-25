import os
import openai
from sqlalchemy.orm import Session
from models.database import Candidate, Conversation

class BaseConversationAgent:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def _format_conversation_history(self, history: list) -> str:
        """Format conversation history for the prompt"""
        if not history:
            return "No previous conversation."
        
        formatted = []
        for conv in history[-5:]:  # Last 5 messages for context
            sender = "Candidate" if conv.message_type == "inbound" else "Recruiter"
            formatted.append(f"{sender}: {conv.content}")
        
        return "\n".join(formatted)
    
    def get_candidate_context(self, candidate: Candidate) -> str:
        """Get candidate information for context"""
        return f"""
        Candidate: {candidate.first_name} {candidate.last_name}
        Profession: {candidate.profession}
        Specialty: {candidate.specialty}
        Current Job: {candidate.current_job}
        Location: {candidate.city}, {candidate.state}
        Contact Count: {candidate.contact_count}
        Status: {candidate.status}
        """