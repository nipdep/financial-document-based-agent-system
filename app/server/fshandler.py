import os
import uuid
from app.server.schemas.document import AddDocumentSchema
from src.dochandler.main import ExTrRAGDocHandler
class FSHandler:
    def __init__(self, agent, **kwargs):
        self.agent = agent
        self.temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def save_to_tempdir(self, file, filename):
        """
        Save the file to a temporary directory.
        """
        temp_file_path = os.path.join(self.temp_dir, filename)
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file)
        return temp_file_path
    
    def delete_from_tempdir(self, filename):
        """
        Delete the file from the temporary directory.
        """
        temp_file_path = os.path.join(self.temp_dir, filename)
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        else:
            print(f"Temporary file '{filename}' not found.")

    def _get_doc_handler(self):
        """
        Creates a DocHandler that writes to the SAME database as the current agent.
        """
        return ExTrRAGDocHandler(
            llm=self.agent.llm,
            embedder=self.agent.embedder,
            db=self.agent.db,
            memory="none"
        )
        
        
    async def add(self, file: bytes, filename: str,agent_id=None):
        """
        Add a document to the file system.
        """
        print(f"[DEBUG] Adding document for agent_id: {agent_id}")
        unq_fname = f"{uuid.uuid4().hex}_{filename}"
        
        # Save the file to a temporary directory
        temp_file_path = self.save_to_tempdir(file, unq_fname)
        try:
            doc_handler = self._get_doc_handler()

            await doc_handler.add_document(
                source=temp_file_path,
                metadata={
                    "original_filename": filename,
                    "unq_filename": unq_fname,
                    "agent_id": agent_id
                }
            )
            try:
                print(f"[DEBUG] Adding document for agent_id: {agent_id} in collection: {self.agent.db.collection_name}")
                count = self.agent.db.count()
                print(f"[DEBUG] Collection '{self.agent.db.collection_name}' now has {count} chunks.")
            except Exception as e:
                print(f"[DEBUG] Could not check vectorstore count: {e}")
                    # Clean up the temporary file
            self.delete_from_tempdir(unq_fname)
            
            return {"status": "success", "unq_filename": unq_fname, "filename": filename}
        except Exception as e:
            print(f"[ERROR] Ingestion failed: {e}")
            raise e
        finally:
            self.delete_from_tempdir(unq_fname)
    
    def add_permanent_document(self, file: bytes, filename: str):
        """
        Add a document specifically to the permanent agent's permanent collection.
        """
        print(f"[DEBUG] Adding document: {filename}")
        unq_fname = f"permanent_{uuid.uuid4().hex}_{filename}"
        
        # Save the file to a temporary directory
        temp_file_path = self.save_to_tempdir(file, unq_fname)
        try:
            self.agent.add_document(
                source=temp_file_path,
                metadata={
                    "original_filename": filename,
                    "unq_filename": unq_fname,
                    "document_type": "permanent_document"
                }
            )
            
            try:
                print(f"[DEBUG] Document added to collection: {self.agent.db.collection_name}")
                count = self.agent.db.count()
                print(f"[DEBUG] Collection now has {count} chunks.")
            except Exception as e:
                print(f"[DEBUG] Could not check tax vectorstore count: {e}")
                
            # Clean up the temporary file
            self.delete_from_tempdir(unq_fname)
            
            return {"status": "success", "unq_filename": unq_fname, "filename": filename}
        except Exception as e:
            print(f"[ERROR] Permanent ingestion failed: {e}")
            raise e
        finally:
            self.delete_from_tempdir(unq_fname)
        