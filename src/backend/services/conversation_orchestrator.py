from .email_agent import EmailConversationAgent
from .sms_agent import SMSConversationAgent

class ConversationOrchestrator:
    def __init__(self):
        self.email_agent = EmailConversationAgent()
        self.sms_agent = SMSConversationAgent()
    
    def generate_response(self, channel: str, candidate, incoming_message: str, conversation_history: list) -> str:
        """Route to appropriate agent based on channel"""
        if channel == "email":
            return self.email_agent.generate_response(candidate, incoming_message, conversation_history)
        elif channel == "sms":
            return self.sms_agent.generate_response(candidate, incoming_message, conversation_history)
        else:
            raise ValueError(f"Unsupported channel: {channel}")