import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from fastapi import HTTPException, Depends, Header
from pydantic import BaseModel

class JWTSessionData(BaseModel):
    agent_id: int
    created_at: datetime
    updated_at: datetime

class JWTManager:
    def __init__(self, secret_key: str, expiration_seconds: int = 900):
        self.secret_key = secret_key
        self.expiration_seconds = expiration_seconds
        self.algorithm = "HS256"
        # In-memory storage for session data (for cleanup purposes)
        self.sessions: Dict[str, JWTSessionData] = {}

    def create_token(self, agent_id: int) -> str:
        """Create JWT token with agent_id and timestamps"""
        now = datetime.now(timezone.utc)
        payload = {
            "agent_id": agent_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "exp": now + timedelta(seconds=self.expiration_seconds)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        # Store session data for cleanup
        session_data = JWTSessionData(
            agent_id=agent_id,
            created_at=now,
            updated_at=now
        )
        self.sessions[token] = session_data
        
        return token

    def refresh_token(self, old_token: str) -> str:
        """Generate new token with same agent_id but fresh expiration"""
        try:
            # Decode old token to get agent info
            old_payload = jwt.decode(old_token, self.secret_key, algorithms=[self.algorithm])
            agent_id = old_payload["agent_id"]
            
            # Create new token with same agent_id but fresh timing
            new_token = self.create_token(agent_id)
            
            # Remove old token from sessions
            if old_token in self.sessions:
                del self.sessions[old_token]
                
            return new_token
            
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token for refresh")
        
    def verify_token_no_update(self, token: str) -> JWTSessionData:
        """Verify JWT token WITHOUT updating timestamp"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            now = datetime.now(timezone.utc)
            if token in self.sessions:
                last_activity = self.sessions[token].updated_at
                session_data = self.sessions[token]  # Use existing data
            else:
                last_activity = datetime.fromisoformat(payload["updated_at"])
                session_data = JWTSessionData(
                    agent_id=payload["agent_id"],
                    created_at=datetime.fromisoformat(payload["created_at"]),
                    updated_at=last_activity
                )
            
            # Check expiration but DON'T update timestamp
            time_since_activity = now - last_activity
            if time_since_activity.total_seconds() > self.expiration_seconds:
                # if token in self.sessions:
                #     del self.sessions[token]
                raise HTTPException(status_code=401, detail="Session expired")
            
            return session_data
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    def update_session(self, token: str) -> None:
        """Update session timestamp"""
        if token in self.sessions:
            self.sessions[token].updated_at = datetime.now(timezone.utc)

    def delete_session(self, token: str) -> None:
        """Delete session from memory"""
        if token in self.sessions:
            del self.sessions[token]

    def get_expired_sessions(self) -> list[str]:
        """Get list of expired session tokens"""
        now = datetime.now(timezone.utc)
        expiration_delta = timedelta(seconds=self.expiration_seconds)
        expired_tokens = []
        
        for token, session_data in self.sessions.items():
            if now - session_data.updated_at > expiration_delta:
                expired_tokens.append(token)
        
        return expired_tokens

# Global JWT manager instance
jwt_manager = JWTManager(
    secret_key=os.getenv("SESSION_PRIVATE_KEY", "secret-key"),
    expiration_seconds=900 # 15 minutes
)

def get_jwt_session_no_update(authorization: str = Header(None)) -> JWTSessionData:
    """Get JWT session WITHOUT updating timestamp"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.split(" ")[1]
    return jwt_manager.verify_token_no_update(token)

