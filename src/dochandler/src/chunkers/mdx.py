from typing import Optional, Dict, Any, List
import asyncio
# CHANGE: Import the Markdown splitter instead of the Recursive one
from langchain_text_splitters import MarkdownHeaderTextSplitter

from src.dochandler.src.chunkers.base_chunker import BaseChunker

class MdxChunker(BaseChunker):
    def __init__(self, config=None):
        
        self.config = config
        
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        
        self.splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False 
        )

    async def create_chunks(self, loader, source) -> Dict[str, Any]:
       
        raw_data = await loader.load_data(source)
        
        # Extract the single huge string
        full_text = raw_data['data'][0]['content']
        base_metadata = raw_data['data'][0]['meta_data']
        doc_id = raw_data['doc_id']

        # Split based on Markdown Headers (#, ##, ###)
        splits = self.splitter.split_text(full_text)

        # Prepare standard dictionary
        ids = []
        documents = []
        metadatas = []

        for i, split in enumerate(splits):
            ids.append(f"{doc_id}_{i}")
            
            # The content is the text of the section
            documents.append(split.page_content)
            
            # MarkdownHeaderSplitter puts the headers into metadata (e.g., {'Header 1': 'Introduction'})
            
            combined_metadata = base_metadata.copy()
            combined_metadata.update(split.metadata)
            
            metadatas.append(combined_metadata)

        return {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas,
            "doc_id": doc_id
        }