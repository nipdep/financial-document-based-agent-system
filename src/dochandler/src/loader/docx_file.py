import hashlib
import os
import aiohttp
import asyncio
from pathlib import Path
from typing import Dict, Any

try:
    from langchain_community.document_loaders import Docx2txtLoader
except ImportError:
    raise ImportError(
        'Docx file requires extra dependencies. Install with `pip install --upgrade "chatgenie[dataloaders]"`' #XXX: @DevinDeSilva why this error suggest to install `chatgenie` (which doesn't pip resolve) when langchain-community is no loading
    ) from None

from src.dochandler.src.loader.base_loader import BaseLoader

class DocxFileLoader(BaseLoader):
    def __init__(self, config: Any = None):
        self.config = config
        self.use_dockling = getattr(config, "use_dockling", True)
        self.server_url = getattr(config, "dockling_server_url", "http://localhost:8080/documents/convert")
        
    async def load_data(self, src: str) -> Dict:
        """Main Entry Point for .docx files."""
        if self.use_dockling:
            print(f"Loading '{os.path.basename(src)}' via Dockling Server...")
            return await self._load_with_dockling(src)
        else:
            print(f"Loading '{os.path.basename(src)}' via Docx2txt (Legacy)...")
            return await asyncio.to_thread(self._load_with_legacy, src)

    async def _load_with_dockling(self, src: str) -> Dict:
        if not os.path.exists(src):
            raise FileNotFoundError(f"File not found: {src}")

        try:
            async with aiohttp.ClientSession() as session:
                form_data = aiohttp.FormData()
                with open(src, "rb") as f:
                    form_data.add_field('document', 
                                      f, 
                                      filename=os.path.basename(src),
                                      content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                
                    async with session.post(self.server_url, data=form_data) as response:
                        response.raise_for_status()
                        data = await response.json()
                
                markdown_text = data.get("markdown", "")
                if not markdown_text:
                    raise ValueError("Dockling server returned empty markdown.")

        except Exception as e:
            raise RuntimeError(f"Dockling processing failed for DOCX: {e}")

        doc_id = hashlib.sha256((markdown_text + src).encode()).hexdigest()

        return {
            "doc_id": doc_id,
            "data": [
                {
                    "content": markdown_text,
                    "meta_data": {
                        "url": src,
                        "parser": "dockling_remote_docx"
                    }
                }
            ]
        }

    def _load_with_legacy(self, url: str) -> Dict:
        loader = Docx2txtLoader(url)
        data = loader.load()
        content = data[0].page_content
        meta_data = data[0].metadata
        meta_data["url"] = url
        
        doc_id = hashlib.sha256((content + url).encode()).hexdigest()
        return {
            "doc_id": doc_id,
            "data": [{"content": content, "meta_data": meta_data}],
        }