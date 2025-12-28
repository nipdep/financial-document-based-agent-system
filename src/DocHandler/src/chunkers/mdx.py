from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from chatgenie.chunkers.base_chunker import BaseChunker
from chatgenie.config.add_config import ChunkerConfig
from chatgenie.helper.json_serializable import register_deserializable
from typing import Optional, Dict, Any 

@register_deserializable
class MdxChunker(BaseChunker):
    def __init__(self, config=None):
        # Default to 1000 characters per chunk
        self.chunk_size = config.chunk_size if config else 1000
        self.chunk_overlap = config.chunk_overlap if config else 200
        
        # tries to split on paragraphs (\n\n) first, then lines (\n), then spaces.
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""] 
        )

    def create_chunks(self, loader, source) -> Dict[str, Any]:
        # 1. LOAD: Get the huge Markdown string from DocklingLoader
        raw_data = loader.load_data(source)
        
        # Extract the single huge string
        full_text = raw_data['data'][0]['content']
        base_metadata = raw_data['data'][0]['meta_data']
        doc_id = raw_data['doc_id']

        # create_documents expects a list of texts and list of metadatas
        splits = self.splitter.create_documents(
            texts=[full_text], 
            metadatas=[base_metadata]
        )

        #FORMAT: Prepare standard dictionary
        ids = []
        documents = []
        metadatas = []

        for i, split in enumerate(splits):
            ids.append(f"{doc_id}_{i}")
            documents.append(split.page_content)
            metadatas.append(split.metadata)

        return {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas,
            "doc_id": doc_id
        }