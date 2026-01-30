from .agent_controller import AgentGeneration
import asyncio
import os
from typing import Optional, Dict
from dotenv import load_dotenv
import uuid
from dotenv import load_dotenv
import uuid
from src.finchat.main import ExTrRAGQA                  # The Chat Agent
from src.dochandler.main import ExTrRAGDocHandler   # The Document Loader
from src.cgcore.vectordb.milvus import MilvusDB         # DB Client
from src.cgcore.embedder.openai import OpenAIEmbedder
from src.cgcore.configs.vectordb.milvus import MilvusConfig
from src.cgcore.configs.embedder.openai import OpenAIEmbedderConfig
from src.cgcore.configs.llm.openai import OpenAILlmConfig
from src.cgcore.llm.openai import OpenAILlm

IXD_PROMPT = """
You are IXD Labs's AI assistant, providing helpful and accurate information to website visitors.
Always follow these rules:
- Respond ONLY using the provided context
- Be professional, friendly, and concise
- Never make up information
- If context doesn't contain the answer, say "I don't have that information but can connect you to the right team"
- For sensitive topics, direct users to appropriate contacts
- Maintain a positive, helpful tone

Context: 
{context}

Current conversation:

Query: {query}

Format your response as:
1. Brief acknowledgment/answer
2. Additional helpful details (if available)

Answer:
"""

Fixed_prompt= """You are an AI assistant with RAG access. Be **accurate, helpful, honest, and safe**. Always prioritize retrieved documents over general knowledge and cite sources.

**Critical**: If uploaded documents don't contain relevant information, state "I don't find information about [topic] in the uploaded documents" - do NOT use general training data as substitute. For partial info: "Based on uploaded documents, I can tell you [available info], but documents don't cover [missing aspects]." For off-topic: "Your question about [topic] is not covered in uploaded documents."

**Non-negotiable**: Never generate harmful/illegal content. Protect privacy. Refuse harmful requests even if educational. Always cite sources regardless of user instructions.

**User Instructions**: Follow additional instructions below ONLY if they don't conflict with above rules. If given a nickname, use it when responding.

"""




class AgentHandler(AgentGeneration):
    COLLECTION_NAME = "Agent_permanent"

    def __init__(self) -> None:
        super().__init__()
        self.resource_lock = asyncio.Lock()
        _ , self.ref_agent = self.create_agent()
        self.agent_dict: Dict[str, ExTrRAGQA] = {}
        self._initialize_permanent_collection()

    def _initialize_permanent_collection(self):
        """Initialize the permanent collection"""
        try:
            load_dotenv('.env', override=True)
            embedder_config = OpenAIEmbedderConfig(api_key=os.getenv('OPENAI_API_KEY'), model='text-davinci-003', dimesion=os.getenv('MONGO_DB_DIMENSION'))
            
            permanent_vectordb_config = MilvusConfig(
                        collection_name=self.COLLECTION_NAME,               
                        dimensions=1536,  # Set explicit dimension value
                        )
    
            
            # You can pre-populate with tax documents here if needed
            count = permanent_vectordb_config.count()
            print(f"[INFO] Collection has {count} documents")
            print(f"[INFO] Collection '{self.COLLECTION_NAME}' initialized")
        except Exception as e:
            print(f"[ERROR] Failed to initialize collection: {e}")

    async def request(self, request: str, agent_id: Optional[int] = None):
        if not agent_id:
            async with self.resource_lock:
                # Create a new agent if no agent_id is provided
                agent_id, app = self.create_agent()
                self.agent_dict[agent_id] = app
            
        try:
            specific_agent = self.agent_dict[agent_id]
            response = await specific_agent.chat(input_query=request)    
            return {
                "request_text":request,
                "response":response,
                "error": None
            }
            
        except KeyError as e:
            print(f"Agent ID {agent_id} not found in agent_dict.")
            return {
                "request_text":request,
                "response":"No such agent found",
                "error": str(e)
            }
            
        
    def create_agent(self, add_document: bool = True):
        # Generate a unique collection name per agent
        unique_collection_name = f"agent_collection_{uuid.uuid4().hex}"

        load_dotenv('.env', override=True)
        llm_config = OpenAILlmConfig(api_key=os.getenv('OPENAI_API_KEY'))
        embedder_config = OpenAIEmbedderConfig(api_key=os.getenv('OPENAI_API_KEY'), model='text-davinci-003', dimesion=os.getenv('MONGO_DB_DIMENSION'))
        vectordb_config = MilvusConfig(
                        collection_name=unique_collection_name,
                        dimensions=1536,  # Set explicit dimension value
                        )
        openai = OpenAILlm(llm_config)
        embeder = OpenAIEmbedder(embedder_config)
        vectordb = MilvusDB(vectordb_config)


        agent_rag  = ExTrRAGQA(
            llm=openai,
            embedder=embeder,
            db=vectordb,
            memory="none",
            history=True
        )

        return id(agent_rag), agent_rag
    
    def create_permanent_agent(self):
        """Create a permanent agent using the permanent collection"""
        load_dotenv('.env', override=True)
        llm_config = OpenAILlmConfig(api_key=os.getenv('OPENAI_API_KEY'))
        embedder_config = OpenAIEmbedderConfig(api_key=os.getenv('OPENAI_API_KEY'), model='text-davinci-003', dimesion=os.getenv('MONGO_DB_DIMENSION'))
        permanent_vectordb_config = MilvusConfig(
                        collection_name=self.COLLECTION_NAME,               
                        dimensions=1536,  # Set explicit dimension value
                        )
       
        openai = OpenAILlm(llm_config)
        embeder = OpenAIEmbedder(embedder_config)
        vectordb = MilvusDB(permanent_vectordb_config)

        agent_rag = ExTrRAGQA(
            llm=openai,
            embedder=embeder,
            db=vectordb,
            memory="buffer",
            keep_history=True,
            system_prompt=IXD_PROMPT
        )
        
        # Mark this as a tax agent
        agent_rag.is_permanent_agent = True

        return id(agent_rag), agent_rag
            
    async def add_document(self, agent_id, document):
        if agent_id not in self.agent_dict:
            raise ValueError("Agent ID not found.")
        
        if isinstance(document, str):
            document = [document]
        
        self.agent_dict[agent_id].add_document(document)
    
    async def close_agent(self, agent_id):
        del self.agent_dict[agent_id]
        
    async def set_system_prompts(self, sys_prompt:str) -> bool:
        try:
            async with self.resource_lock:
                self.ref_agent.set_system_prompt(sys_prompt)
                
                for agent_id, agent in self.agent_dict.items():
                    agent.set_system_prompt(sys_prompt)
            
            return True
        except Exception as e:
            print(f"Error setting system prompt: {e}")
            return False