import csv
import hashlib
import os
import aiohttp
import asyncio
from io import StringIO
from urllib.parse import urlparse
from typing import Dict, Any

import requests
from src.dochandler.src.loader.base_loader import BaseLoader

class CsvLoader(BaseLoader):
    def __init__(self, config: Any = None):
        self.config = config
        self.use_dockling = getattr(config, "use_dockling", True)
        self.server_url = getattr(config, "dockling_server_url", "http://localhost:8080/documents/convert")

    async def load_data(self, src: str) -> Dict:
        """Main Entry Point for .csv files."""
        if self.use_dockling:
            # Note: Dockling is great at turning CSV tables into readable Markdown tables
            return await self._load_with_dockling(src)
        else:
            return await asyncio.to_thread(self._load_with_legacy, src)

    async def _load_with_dockling(self, src: str) -> Dict:
        # Check if local file or URL (Simplified for local file use to match your PDF example)
        if not os.path.exists(src):
             raise FileNotFoundError(f"File not found: {src}")

        try:
            async with aiohttp.ClientSession() as session:
                form_data = aiohttp.FormData()
                with open(src, "rb") as f:
                    form_data.add_field('document', 
                                      f, 
                                      filename=os.path.basename(src),
                                      content_type='text/csv')
                
                    async with session.post(self.server_url, data=form_data) as response:
                        response.raise_for_status()
                        data = await response.json()
                
                markdown_text = data.get("markdown", "")

        except Exception as e:
            raise RuntimeError(f"Dockling processing failed for CSV: {e}")

        doc_id = hashlib.sha256((markdown_text + src).encode()).hexdigest()
        return {
            "doc_id": doc_id,
            "data": [{"content": markdown_text, "meta_data": {"url": src, "parser": "dockling_remote_csv"}}]
        }

    def _load_with_legacy(self, content: str) -> Dict:
        """Original synchronous logic for CSV parsing"""
        result = []
        lines = []
        # We need a wrapper because the original _get_file_content wasn't an instance method
        with self._get_file_content(content) as file:
            first_line = file.readline()
            delimiter = self._detect_delimiter(first_line)
            file.seek(0)
            reader = csv.DictReader(file, delimiter=delimiter)
            for i, row in enumerate(reader):
                line = ", ".join([f"{field}: {value}" for field, value in row.items()])
                lines.append(line)
                result.append({"content": line, "meta_data": {"url": content, "row": i + 1}})
        
        doc_id = hashlib.sha256((content + " ".join(lines)).encode()).hexdigest()
        return {"doc_id": doc_id, "data": result}

    @staticmethod
    def _detect_delimiter(first_line):
        delimiters = [",", "\t", ";", "|"]
        counts = {delimiter: first_line.count(delimiter) for delimiter in delimiters}
        return max(counts, key=counts.get)

    @staticmethod
    def _get_file_content(content):
        url = urlparse(content)
        if url.scheme in ["http", "https"]:
            response = requests.get(content)
            response.raise_for_status()
            return StringIO(response.text)
        else:
            path = url.path if url.scheme == "file" else content
            return open(path, newline="", encoding="utf-8")