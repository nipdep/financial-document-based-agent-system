from uuid import UUID
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Dict, List, Tuple

# --- Pydantic Models & Agent Class ---
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    history: List[Dict[str, str]]
    
class SessionData(BaseModel):
    agent_id: int
    # <<< FIX: Add 'updated_at' for sliding window expiration.
    # It defaults to the creation time.
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))