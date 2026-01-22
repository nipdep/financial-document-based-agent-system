from pydantic import BaseModel, Field
from typing import Dict, List, Tuple
from datetime import datetime, timedelta, timezone
import asyncio
from uuid import UUID, uuid4
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from contextlib import asynccontextmanager


from app.src.data_type import SessionData
# MODIFIED: Added a creation timestamp to track session age.
class SessionData(BaseModel):
    agent_id: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: InMemoryBackend[UUID, SessionData],
        auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self): return self._identifier
    @property
    def backend(self): return self._backend
    @property
    def auto_error(self): return self._auto_error
    @property
    def auth_http_exception(self): return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        return True