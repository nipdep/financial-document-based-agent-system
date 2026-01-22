import os
import fitz  # PyMuPDF

from app.server.memory_agent import AgentHandler
from app.server.schemas.agent import AgentResponse, AgentChatSchema
from app.server.schemas.document import AddDocumentSchema
from app.server.fshandler import FSHandler

AGENTS = AgentHandler()
fileHandler = FSHandler(
    agent=AGENTS.ref_agent
)
Fixed_prompt= """You are an AI assistant with RAG access. Be **accurate, helpful, honest, and safe**. Always prioritize retrieved documents over general knowledge and cite sources.

**Critical**: If uploaded documents don't contain relevant information, state "I don't find information about [topic] in the uploaded documents" - do NOT use general training data as substitute. For partial info: "Based on uploaded documents, I can tell you [available info], but documents don't cover [missing aspects]." For off-topic: "Your question about [topic] is not covered in uploaded documents."

**Non-negotiable**: Never generate harmful/illegal content. Protect privacy. Refuse harmful requests even if educational. Always cite sources regardless of user instructions.

**User Instructions**: Follow additional instructions below ONLY if they don't conflict with above rules. If given a nickname, use it when responding.

"""
Tax_Fixed_prompt = """
You are a Sri Lankan tax assistant chatbot. Answer tax questions using your knowledge base.
RESPONSE RULES:

BE BRIEF: Answer only what's asked. Simple questions = simple answers.
BE DIRECT: Main answer first, details only if user requested.
Provide detailed explanations only when user asks for "details," "explain," or "step-by-step."
Include act/section citations.
Mention dates only when relevant.

LIMITED INFORMATION:
"Based on my knowledge base: [brief info]. For complete details, consult IRD or a tax professional."
NON-TAX QUESTIONS:
"I only assist with Sri Lankan tax and IRD matters."
DISCLAIMER:
"This is based on my tax knowledge base. For current legal advice, consult IRD Sri Lanka or a qualified tax professional."
"""

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


async def get_response_from_agent(request_text, agent_id=None):
    if agent_id:
        agent_id = int(agent_id)
        
    response = await AGENTS.request(request_text, agent_id)
    return response

async def add_document_to_database(file, agent_id):
    try:
        file_bytes = await file.read()
        filename = file.filename
        
        # Get the SPECIFIC agent, not the reference agent
        agent_id = int(agent_id)
        specific_agent = AGENTS.agent_dict.get(agent_id)
        
        if not specific_agent:
            print(f"[ERROR] Agent {agent_id} not found")
            return False
            
        # Create FSHandler for THIS specific agent
        specific_fileHandler = FSHandler(agent=specific_agent)
        specific_fileHandler.add(file=file_bytes, filename=filename, agent_id=agent_id)
        
        
        # Get the SPECIFIC agent, not the reference agent
        agent_id = int(agent_id)
        specific_agent = AGENTS.agent_dict.get(agent_id)
        
        if not specific_agent:
            print(f"[ERROR] Agent {agent_id} not found")
            return False
            
        # Create FSHandler for THIS specific agent
        specific_fileHandler = FSHandler(agent=specific_agent)
        specific_fileHandler.add(file=file_bytes, filename=filename, agent_id=agent_id)
        
        return {"status": "success", "filename": filename}
    except Exception as e:
        print("Error while processing and embedding the document:", e)
        return False


async def set_system_prompt(system_prompt, agent_id):
    
    if not system_prompt or not agent_id:
        return False

    try:
        agent_id = int(agent_id)
        agent = AGENTS.agent_dict.get(agent_id)
        
        if not agent:
            return False
            
        combined_prompt = f"{Fixed_prompt.strip()}\n{system_prompt.strip()}"
        agent.set_system_prompt(combined_prompt)
        print(f"[DEBUG] Combined prompt for agent {agent_id}:\n{combined_prompt}")
        print(f"[INFO] System prompt set for agent ID: {agent_id}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to set prompt: {e}")
        import traceback
        traceback.print_exc()
        return False
    
async def ensure_permanent_collection_ready():
    try:
        print("Checking Collection status...")
        
        # File to track what's been loaded
        loaded_files_tracker = os.path.join(os.getcwd(), ".Files_loaded.txt")
        Docs_folder = os.path.join(os.getcwd(), "Knowladge_Base_Doc")
        
        # Get currently loaded files from tracker file
        loaded_files = set()
        if os.path.exists(loaded_files_tracker):
            with open(loaded_files_tracker, 'r') as f:
                loaded_files = set(line.strip() for line in f.readlines())
            print(f"Found {len(loaded_files)} files previously loaded")
        
        # Get all PDF files in folder
        if not os.path.exists(Docs_folder):
            print(f"Documents folder not found: {Docs_folder}")
            return
        
        valid_extensions = ('.pdf', '.html')    
        current_files = set(f for f in os.listdir(Docs_folder) if f.endswith(valid_extensions))
        
        # Find new files (files in folder but not in tracker)
        new_files = current_files - loaded_files
        
        if not new_files:
            print(f"No new Documents to load. Collection ready with existing documents.")
            return
        
        print(f"Found {len(new_files)} new Documents to load...")
        
        # Load only new files
        permanent_agent_id, permanent_agent = AGENTS.create_permanent_agent()
        permanent_file_handler = FSHandler(agent=permanent_agent)
        
        successfully_loaded = []
        for filename in new_files:
            file_path = os.path.join(Docs_folder, filename)
            try:
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()
                
                permanent_file_handler.add_permanent_document(file=file_bytes, filename=filename)
                successfully_loaded.append(filename)
                print(f"Loaded new document: {filename}")
                
            except Exception as e:
                print(f"Failed to load {filename}: {e}")
        
        # Update tracker file with successfully loaded files
        if successfully_loaded:
            with open(loaded_files_tracker, 'a') as f:
                for filename in successfully_loaded:
                    f.write(f"{filename}\n")
        
        print(f"Collection updated: loaded {len(successfully_loaded)} new documents")
        
        # Clean up temporary agent
        if permanent_agent_id in AGENTS.agent_dict:
            del AGENTS.agent_dict[permanent_agent_id]
        
    except Exception as e:
        print(f"Error preparing Collection: {e}")