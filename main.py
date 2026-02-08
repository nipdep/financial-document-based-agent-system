import os
import sqlite3
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, BackgroundTasks, Depends, Response,Header
from fastapi.middleware.cors import CORSMiddleware
from app.server.fshandler import FSHandler

from uuid import UUID, uuid4
from typing import Dict, List, Tuple, Optional

# Import fastapi-sessions components
from app.server.schemas.agent import AgentChatSchema, CreateAgentSchema
from app.src.jwt_manager import jwt_manager,JWTSessionData,get_jwt_session_no_update

# Import your existing server components
import app.server as server
from app.server.memory_agent import AgentHandler
from app.server.fshandler import FSHandler
from app.src.data_type import FeedbackRequest, TestSummary, TestDetail
from app.server.schemas.agent import AgentChatSchema
from app.src.session_manager import SessionData, BasicVerifier
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
load_dotenv(".env", override=True)

# --- In-Memory Storage for Agents (Session Management) ---
AGENT_STORE: Dict[int, Tuple[object, datetime]] = {}
AGENTS_LOCK = asyncio.Lock()

AGENTS = server.AGENTS


async def cleanup_expired_data():
    """
    Periodically cleans up expired agents and sessions based on inactivity.
    """
    while True:
        await asyncio.sleep(300) #5 minutes
        # Get expired JWT sessions
        expired_tokens = jwt_manager.get_expired_sessions()
        
        
        if expired_tokens:
            async with AGENTS_LOCK:
                for token in expired_tokens:
                    session_data = jwt_manager.sessions.get(token)
                    if session_data:
                        agent_id_to_delete = session_data.agent_id
                        print(f"[DEBUG] Cleaning up expired agent {agent_id_to_delete}")
                        if agent_id_to_delete in AGENT_STORE:
                            agent_instance, _ = AGENT_STORE[agent_id_to_delete]
                            try:
                                # Same cleanup logic as before
                                if hasattr(agent_instance, 'db') and hasattr(agent_instance.db, 'collection_name'):
                                    collection_name = agent_instance.db.collection_name
                                    if collection_name != "Agent_permanent":  
                                        collection_deleted = await agent_instance.db.delete_collection()
                                        if collection_deleted:
                                            print(f"Agent {agent_id_to_delete}: Regular collection '{collection_name}' deleted")
                                        else:
                                            print(f"Agent {agent_id_to_delete}: Failed to delete collection")
                                    else:
                                        print(f"Agent {agent_id_to_delete}: permanent collection '{collection_name}' preserved")
                                else:
                                    print(f"Agent {agent_id_to_delete}: No collection info, skipping cleanup")
                                    
                            except Exception as e:
                                print(f"[ERROR] Failed to cleanup agent {agent_id_to_delete}: {e}")
                            
                            del AGENT_STORE[agent_id_to_delete]
                            if agent_id_to_delete in AGENTS.agent_dict:
                                del AGENTS.agent_dict[agent_id_to_delete]
                    
                    # Delete from JWT manager
                    jwt_manager.delete_session(token)
        
        if expired_tokens:
            print(f"Cleaned up {len(expired_tokens)} expired sessions and their agents.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting background cleanup task...")
    await server.ensure_permanent_collection_ready()
    asyncio.create_task(cleanup_expired_data())
    yield
    print("Application shutting down.")


app = FastAPI(lifespan=lifespan, debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
def read_root():
    return True

@app.post("/create_agent")
async def create_agent(payload: CreateAgentSchema):  
    """Create new agent (regular or tax) and session"""    
    # Tax agent creation logic
    if payload.is_permanent_agent:
        agent_id, agent_instance = AGENTS.create_permanent_agent()
        agent_instance.set_system_prompt(server.IXD_PROMPT)
        agent_type = "permanent"
        print(f"[DEBUG] Created permanent agent with ID: {agent_id}")

         # Store agent in both systems with thread safety
        async with AGENTS_LOCK:
            AGENTS.agent_dict[agent_id] = agent_instance
            AGENT_STORE[agent_id] = (agent_instance, datetime.now(timezone.utc))
        
        # Create JWT token instead of session
        token = jwt_manager.create_token(agent_id)
        
        return {
            "msg": "Agent created", 
            "agent_id": agent_id,
            "token": token,  # Return JWT token
            "agent_type": agent_type,
            "time": datetime.now(timezone.utc).isoformat()
        }

    else:
        agent_id, agent_instance = AGENTS.create_agent()
        agent_type = "regular"
        print(f"[DEBUG] Created REGULAR agent with ID: {agent_id}")

        async with AGENTS_LOCK:
            AGENTS.agent_dict[agent_id] = agent_instance
            AGENT_STORE[agent_id] = (agent_instance, datetime.now(timezone.utc))
        
            ## Create JWT token instead of session
        token = jwt_manager.create_token(agent_id)
        
        return {
            "msg": "Agent created", 
            "agent_id": agent_id,
            "token": token,  # Return JWT token
            "agent_type": agent_type,
        }


@app.post("/chat")
async def chat(
    payload: AgentChatSchema,
    session_data: JWTSessionData = Depends(get_jwt_session_no_update)
):
    """Chat with agent using session authentication"""
    agent_id = session_data.agent_id
    agent = None
    
    # Use lock when reading shared data
    async with AGENTS_LOCK:
        if agent_id not in AGENTS.agent_dict:
            return {
                "request_text": payload.request_text,
                "response": "No such agent found",
                "error": "Agent not found for this session"
            }
        agent_instance = AGENTS.agent_dict[agent_id]
    
    try:
        response = await AGENTS.request(payload.request_text, agent_id)
        return response
    except Exception as e:
        return {
            "request_text": payload.request_text,
            "response": "Error occurred during chat",
            "error": str(e)
        }

@app.post("/add_document")
async def add_document(
    file: UploadFile = File(...),
    authorization: str = Header(None)
):
    """Add document to agent using session authentication"""
     # Get current token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
   
    current_token = authorization.split(" ")[1]
    
    # Verify current session (but don't update timer)
    session_data = jwt_manager.verify_token_no_update(current_token)  
    agent_id = session_data.agent_id
    
    async with AGENTS_LOCK:
        if agent_id not in AGENTS.agent_dict:
            return {
                "msg": "Agent not found for this session",
                "error": "No agent found"
            }
        agent_instance = AGENTS.agent_dict[agent_id]
    
    try:
        file_bytes = await file.read()
        filename = file.filename
        
        file_handler = FSHandler(agent=agent_instance)
        result = await file_handler.add(file=file_bytes, filename=filename, agent_id=agent_id)
        new_token = jwt_manager.refresh_token(current_token)
        return {
        "msg": "Document added successfully",
        "new_token": new_token, 
        "time": datetime.now(timezone.utc).isoformat()
    }
    except Exception as e:
        return {
            "msg": "Failed to add document",
            "error": str(e)
        }

@app.post("/system_prompt")
async def set_system_prompt(
    system_prompt: str = Form(...),
    session_data: JWTSessionData = Depends(get_jwt_session_no_update)
):
    """Set system prompt for agent using session authentication"""
    agent_id = session_data.agent_id
    
    if not system_prompt:
        return {
            "msg": "System prompt cannot be empty",
            "error": "Empty prompt"
        }
    
    async with AGENTS_LOCK:
        if agent_id not in AGENTS.agent_dict:
            return {
                "msg": "Agent not found for this session",
                "error": "No agent found"
            }
        agent_instance = AGENTS.agent_dict[agent_id]
    
    # Set system prompt directly instead of calling server function
    try:
        combined_prompt = f"{server.Fixed_prompt.strip()}\n{system_prompt.strip()}"
        agent_instance.set_system_prompt(combined_prompt)
        print(f"[DEBUG] Combined prompt for agent {agent_id}:\n{combined_prompt}")
        print(f"[INFO] System prompt set for agent ID: {agent_id}")
        return {"msg": "System prompt updated"}
    except Exception as e:
        print(f"[ERROR] Failed to set prompt: {e}")
        return {
            "msg": "Failed to update system prompt",
            "error": str(e)
        }
    
@app.post("/test_chat")
async def test_chat(
    payload: AgentChatSchema,
    session_data: JWTSessionData = Depends(get_jwt_session_no_update)
):
    """
    Dedicated endpoint for the 'Test' tab. 
    Future-proofed for returning citations and debug info.
    """
    agent_id = session_data.agent_id
    
    async with AGENTS_LOCK:
        if agent_id not in AGENTS.agent_dict:
            return {
                "request_text": payload.request_text,
                "response": "No such agent found",
                "error": "Agent not found"
            }
        agent_instance = AGENTS.agent_dict[agent_id]
    
    try:
       
        response_data = await AGENTS.request(payload.request_text, agent_id)
        
        # 2. Structure the response for the Test UI
        # Currently identical to chat, but easy to expand later:
        return {
            "response": response_data.get("response"),
            "request_text": payload.request_text,
            "error": None,
        }
        
    except Exception as e:
        return {
            "request_text": payload.request_text,
            "response": "Error occurred during testing",
            "error": str(e)
        }

@app.post("/save_feedback")
async def save_feedback(
    payload: FeedbackRequest,
    session_data: JWTSessionData = Depends(get_jwt_session_no_update)
):
    """Save feedback for a chat response"""
    try:
        conn = sqlite3.connect("chatbot_feedback.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        timestamp = int(datetime.now(timezone.utc).timestamp())
        
        cursor.execute("""
            INSERT INTO test (agent_id, timestamp, prompt, response, response_feedback, comment)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (payload.agent_id, timestamp, payload.prompt, payload.response, payload.response_feedback, payload.comment))
        
        test_id = cursor.lastrowid
        
        if payload.sources:
            chunk_data = [
                (test_id, source.citation_index, source.content, source.chunk_feedback)
                for source in payload.sources
            ]
            cursor.executemany("""
                INSERT INTO chunks (test_id, citation_index, content, chunk_feedback)
                VALUES (?, ?, ?, ?)
            """, chunk_data)
            
        conn.commit()
        conn.close()
        return {"msg": "Feedback saved successfully"}
    except Exception as e:
        print(f"[ERROR] Failed to save feedback: {e}")
        return {
            "msg": "Failed to save feedback",
            "error": str(e)
        }

@app.get("/tests/{agent_id}", response_model=List[TestSummary])
async def get_agent_tests(agent_id: int):
    """List all tests for a specific agent"""
    try:
        conn = sqlite3.connect("chatbot_feedback.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, prompt, timestamp, response_feedback FROM test WHERE agent_id = ? ORDER BY timestamp DESC", 
            (agent_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [
            TestSummary(
                id=row[0], 
                prompt=row[1], 
                timestamp=row[2], 
                response_feedback=row[3]
            ) for row in rows
        ]
    except Exception as e:
        print(f"[ERROR] Failed to fetch tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test_details/{test_id}", response_model=TestDetail)
async def get_test_details(test_id: int):
    """Get detailed information for a specific test"""
    try:
        conn = sqlite3.connect("chatbot_feedback.db")
        cursor = conn.cursor()
        
        # Fetch test details
        cursor.execute(
            "SELECT id, agent_id, timestamp, prompt, response, response_feedback, comment FROM test WHERE id = ?", 
            (test_id,)
        )
        test_row = cursor.fetchone()
        
        if not test_row:
            conn.close()
            raise HTTPException(status_code=404, detail="Test not found")
            
        # Fetch associated chunks
        cursor.execute(
            "SELECT citation_index, content, chunk_feedback FROM chunks WHERE test_id = ? ORDER BY citation_index ASC", 
            (test_id,)
        )
        chunk_rows = cursor.fetchall()
        conn.close()
        
        chunks = [
            {"citation_index": row[0], "content": row[1], "chunk_feedback": row[2]} 
            for row in chunk_rows
        ]
        
        return TestDetail(
            id=test_row[0],
            agent_id=test_row[1],
            timestamp=test_row[2],
            prompt=test_row[3],
            response=test_row[4],
            response_feedback=test_row[5],
            comment=test_row[6],
            chunks=chunks
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[ERROR] Failed to fetch test details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/end_session")
async def end_session(
    authorization: str = Header(None)  # Changed this line

):
    """End session and cleanup with tax collection preservation"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    session_data = jwt_manager.sessions.get(token)
    if session_data:
        agent_id = session_data.agent_id
        
        async with AGENTS_LOCK:
            if agent_id in AGENT_STORE:
                agent_instance, _ = AGENT_STORE[agent_id]
                try:
                    # Preserve perment collection, only delete regular agent collections
                    if hasattr(agent_instance, 'db') and hasattr(agent_instance.db, 'collection_name'):
                        if agent_instance.db.collection_name != server.AGENTS.COLLECTION_NAME:
                            collection_deleted = await agent_instance.db.delete_collection()
                            if collection_deleted:
                                print(f"Agent {agent_id}: Regular agent collection deleted")
                            else:
                                print(f"Agent {agent_id}: Failed to delete regular collection")
                        else:
                            print(f"Agent {agent_id}:permanent agent collection preserved")
                    else:
                        # Fallback cleanup if attributes don't exist
                        collection_deleted = agent_instance.db.delete_collection()
                        if collection_deleted:
                            print(f"Agent {agent_id}: Session completely cleaned up")
                        else:
                            print(f"Agent {agent_id}: Failed to cleanup session")
                            
                except Exception as ve:
                    print(f"[ERROR] Failed to cleanup agent {agent_id}: {ve}")

                # Remove from both storage systems
                del AGENT_STORE[agent_id]
                if agent_id in AGENTS.agent_dict:
                    del AGENTS.agent_dict[agent_id]
    
    jwt_manager.delete_session(token)
    return {"msg": "Session and agent completely deleted."}
