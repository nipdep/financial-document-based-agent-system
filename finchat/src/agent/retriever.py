from typing import Optional

from cgcore.llm.base import BaseLlm
from cgcore.embedder.base import BaseEmbedder
from cgcore.vectordb.base import BaseVectorDB
from cgcore.utils.utils import paragraph_list_to_str
import asyncio
from icecream import ic

class Retriever:
    def __init__(self,
                 db: BaseVectorDB,
                 embedder: BaseEmbedder,
                 llm: Optional[BaseLlm]=None):
        self.db = db
        self.embedder = embedder
        self.llm = llm

    async def simple_retrieve(self, prompt: str) -> str:
        input_query_embedding = self.embedder.embed(prompt)
        relevant_docs = await self.db.vector_search(input_query_embedding)
        return relevant_docs
    
        
    
