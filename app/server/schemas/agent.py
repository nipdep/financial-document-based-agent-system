from datetime import datetime
from pydantic import BaseModel, EmailStr, constr
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

class AgentChatSchema(BaseModel):
    request_text: str
    agent_id: int | None = None
    
    class Config:
        from_attributes = True
        
# Define request body model
class ChatMessage(BaseModel):
    message: str
        
class CreateAgentSchema(BaseModel):
    is_permanent_agent: bool = False
    
    class Config:
        from_attributes = True


class AgentResponse(AgentChatSchema):
    request_text:str
    agent_id: int | None = None
    response: str | None = None