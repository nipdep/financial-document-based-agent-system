import requests
import hashlib
import os
from typing import Dict, List, Optional
from pathlib import Path

# Assuming these base classes exist in your structure
from chatgenie.loaders.base_loader import BaseLoader
from chatgenie.helper.json_serializable import register_deserializable

@register_deserializable

class DocklingLoader(BaseLoader):
    def __init__(self,server_url: str = "http://localhost:8080/documents/convert",image_scale: int = 4, 
                 extract_tables: bool = False):
        
        """ Initialize the Dockling server with serve configuration """
        
        self.server_url= server_url
        self.params = {
                                "extract_tables_as_images": "false",
                                "image_resolution_scale": 4
                            }
    def _save_markdown(self,original_path: str, markdown_content: str) -> str:
       """ Saves the markdown content to a file with the same name as the PDF
        but with a .md extension """
       
       path_obj = Path(original_path)
       output_md_path = path_obj.with_suffix('.md')
       with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
       return str(output_md_path)
    def load_data(self,file_path: str) -> Dict:
        """
        Sends file to Dockling server, saves MD, and returns content 
        compatible with the RAG pipeline.
        """
        if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # 1. Send to Server
        try:
                with open(file_path, "rb") as f:
                    files = {"document": (file_path, f, "application/pdf")}
                    response = requests.post(self.server_url, params=self.params, files=files)
                
                response.raise_for_status() # Raise error for bad status codes
                data = response.json()
                
                # Extract markdown
                markdown_text = data.get("markdown", "")
                
                if not markdown_text:
                    raise ValueError("Dockling server returned empty markdown.")

        except requests.exceptions.RequestException as e:
                raise RuntimeError(f"Failed to connect to Dockling server: {e}")

        # 2. Save Markdown locally
        saved_md_path = self._save_markdown(file_path, markdown_text)

        # 3. Format Data for Chunker
            
        doc_id = hashlib.sha256((markdown_text + file_path).encode()).hexdigest()
        
        return {
            "doc_id": doc_id,
            "data": [
                {
                    "content": markdown_text,
                    "meta_data": {
                        "source": file_path,
                        "processed_path": saved_md_path,
                        "parser": "dockling_remote"
                    }
                }
            ]
        }