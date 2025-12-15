from typing import Optional, List, Dict, Tuple, Union

from chatgenie.llm.base import BaseLlm
from chatgenie.embedder.base import BaseEmbedder
from chatgenie.vectordb.base import BaseVectorDB
from chatgenie.config.rag.base import BaseRAGConfig

class BaseRAG:
    def __init__(
            self,
            llm: Optional[BaseLlm] = None,
            embdedder: Optional[BaseEmbedder] = None,
            vector_db: Optional[BaseVectorDB] = None,
    ):
        self.llm = llm
        self.embedder = embdedder
        self.vector_db = vector_db

        self._setup()

    def _setup(self):
        raise NotImplementedError

    def add_document(self, source, metadata: Optional[Dict] = None, dry_run: bool = False):
        raise NotImplementedError
    
    def chat(self, input_query, history=None):
        raise NotImplementedError
    
