from typing import Dict, Optional
import hashlib

from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory

from chatgenie.data.config import Config
from chatgenie.utils.data_type import DataType
from chatgenie.config.add_config import AddConfig
from chatgenie.utils.data_type import detect_datatype
from chatgenie.utils.data_formatter import DataFormatter
from chatgenie.chunkers.base_chunker import BaseChunker
from chatgenie.utils.utils import paragraph_list_to_str
from chatgenie.utils.prompt_template import *

from icecream import ic

class BaseAgent:
    def __init__(self, llm, db, embedder, memory="none", memory_size=0):
        self.llm = llm
        self.db = db
        self.embedder = embedder
        self.memory = self._select_memory(memory, memory_size)

    def _select_memory(self, memory, memory_size):
        if memory == "none":
            return None
        elif memory == "buffer":
            return ConversationBufferMemory()
        elif memory == "window_buffer":
            return ConversationBufferWindowMemory(k=memory_size)
        else:
            raise ValueError(f"Invalid memory type: {memory}")

    def query(self, input_query):
        
        # embed the input query
        input_query_embedding = self.embedder.embed(input_query)
        # retrieve the relevant documents from the database
        relavent_docs = self.db.query(input_query_embedding)
    
        # XXX: we can rerank the relavent docs here
        context = paragraph_list_to_str([doc['content'] for doc in relavent_docs])
        # get the answer from the llm
        if self.memory:
            template = DEFAULT_PROMPT_WITH_HISTORY
            memory = self.memory.load_memory_variables({})['history']
            prompt = fill_template(template, input_query, context, memory)
        else:
            template = DOCS_SITE_DEFAULT_PROMPT
            prompt = fill_template(template, input_query, context)

        answer = self.llm.generate(prompt)
        
        # update memory 
        if self.memory:
            self.memory.save_context({"input_query": input_query}, {"output": answer})

        return answer
    
    def add_document(self, 
            source, 
            data_type: Optional[DataType] = None,
            metadata: Optional[Dict] = None,
            config: Optional[AddConfig] = None, # FIXME: this is not usable at the point
            dry_run: bool = False): # XXX: to improve 
        
        if config is None:
            config = AddConfig()

        if data_type:
            data_type = DataType(data_type)
        else:
            data_type = detect_datatype(source)

        data_formatter = DataFormatter(data_type, config)
        chunks = data_formatter.chunker.create_chunks(data_formatter.loader, source)

        ic(chunks['ids'])
        records = []
        for i, chunk_id in enumerate(chunks["ids"]):
            records.append(
                {
                    "_id": chunk_id,
                    "content": chunks["documents"][i],
                    "meta_data": chunks["metadatas"][i] | metadata,
                    "text_embedding": self.embedder.embed(chunks["documents"][i])
                }
            )
            
        # ic(records)
        self.db.batch_insert(records)


    

    

