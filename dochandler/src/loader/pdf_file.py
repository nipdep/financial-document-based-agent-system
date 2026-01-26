import hashlib

try:
    from langchain_community.document_loaders import PyPDFLoader
except ImportError:
    raise ImportError(
        'PDF File requires extra dependencies. Install with `pip install --upgrade "chatgenie[dataloaders]"`'
    ) from None
    
from dochandler.src.loader.base_loader import BaseLoader
from cgcore.utils.utils import clean_string


import hashlib
import os
import aiohttp
import asyncio
from pathlib import Path
from typing import Dict, Optional, Any


class PdfFileLoader(BaseLoader):
    def __init__(self, config: Any = None):
        """
        Initialize loader. 
        Checks config to decide between 'Legacy PyPDF' or 'Dockling Server'.
        """
        self.config = config
        
        # 1. Check if we should use Dockling (Default to False to preserve old behavior unless asked)
        self.use_dockling = getattr(config, "use_dockling", True)
        
        # 2. Dockling Configuration
        self.server_url = getattr(config, "dockling_server_url", "http://localhost:8080/documents/convert")
        image_scale = getattr(config, "dockling_image_scale", 4)
        extract_tables = getattr(config, "dockling_extract_tables", False)
        
        self.dockling_params = {
            "extract_tables_as_images": str(extract_tables).lower(),
            "image_resolution_scale": image_scale
        }

    async def load_data(self, src: str) -> Dict:
        """
        Main Entry Point (Async).
        Dispatches to either Dockling or PyPDF based on config.
        """
        if self.use_dockling:
            print(f"Loading '{os.path.basename(src)}' via Dockling Server...")
            return await self._load_with_dockling(src)
        else:
            print(f"Loading '{os.path.basename(src)}' via PyPDFLoader (Legacy)...")
            return await asyncio.to_thread(self._load_with_pypdf, src)

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
                                      content_type='application/pdf')
                
                    async with session.post(self.server_url, params=self.dockling_params, data=form_data) as response:
                        response.raise_for_status()
                        data = await response.json()
                
                markdown_text = data.get("markdown", "")
                if not markdown_text:
                    raise ValueError("Dockling server returned empty markdown.")

        except Exception as e:
            raise RuntimeError(f"Dockling processing failed: {e}")

        path_obj = Path(src)
        output_md_path = path_obj.with_suffix('.md')
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        doc_id = hashlib.sha256((markdown_text + src).encode()).hexdigest()

        return {
            "doc_id": doc_id,
            "data": [
                {
                    "content": markdown_text,
                    "meta_data": {
                        "url": src,
                        "processed_path": str(output_md_path),
                        "parser": "dockling_remote"
                    }
                }
            ]
        }
    
    def _load_with_pypdf(self, src: str) -> Dict:
        """Original synchronous logic for PyPDFLoader"""
        loader = PyPDFLoader(src)
        data = []
        all_content = []
        
        # Original logic
        pages = loader.load_and_split()
        if not len(pages):
            raise ValueError("No data found")
            
        for page in pages:
            content = page.page_content
            content = clean_string(content)
            meta_data = page.metadata
            meta_data["url"] = src
            data.append(
                {
                    "content": content,
                    "meta_data": meta_data,
                }
            )
            all_content.append(content)
            
        doc_id = hashlib.sha256(
            (" ".join(all_content) + src).encode()).hexdigest()
            
        return {
            "doc_id": doc_id,
            "data": data,
        }