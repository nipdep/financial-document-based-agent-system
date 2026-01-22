from uuid import UUID, uuid4
from typing import Dict, List

class ChatbotAgent:
    def __init__(self):
        self.id = uuid4()
        self.conversation_history: List[Dict[str, str]] = []

    def process_message(self, user_message: str) -> str:
        self.conversation_history.append({"role": "user", "content": user_message})
        response_text = f"Agent {str(self.id)[:4]} processed: '{user_message}'"
        self.conversation_history.append({"role": "agent", "content": response_text})
        return response_text