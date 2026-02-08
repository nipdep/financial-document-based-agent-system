from uuid import UUID
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Dict, List, Tuple, Optional

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

class FeedbackChunk(BaseModel):
    citation_index: int
    content: str
    chunk_feedback: str

class FeedbackRequest(BaseModel):
    agent_id: int
    prompt: str
    response: str
    response_feedback: str
    comment: Optional[str] = None
    sources: List[FeedbackChunk]

class TestSummary(BaseModel):
    id: int
    prompt: str
    timestamp: int
    response_feedback: str

class TestDetail(BaseModel):
    id: int
    agent_id: int
    timestamp: int
    prompt: str
    response: str
    response_feedback: str
    comment: Optional[str] = None
    chunks: List[FeedbackChunk]