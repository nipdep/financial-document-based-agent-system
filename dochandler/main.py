from pydantic import BaseModel, Field
from typing import List
from langchain_classic.memory import ConversationBufferMemory, ConversationBufferWindowMemory

from dochandler.src.agent.loader import Loader
from dochandler.src.agent.judge import Judge

from icecream import ic

class ExTrRAGDocHandler:
    def __init__(self, llm, db, embedder, memory="none", history=False):
        self.llm = llm
        self.db = db
        self.embedder = embedder
        self.memory = memory
        if history:
            self.history = []

        self._setup()
        
    def _setup(self):
        # create question generator agent 
        class Questions(BaseModel): # XXX: need to improve
            questions: List[str] = Field(description="3 The questions related to the paragraph")
        question_generator = Judge(llm=self.llm, rule=Questions)
        # build the document loader 
        self.loader = Loader(db=self.db, embedder=self.embedder, llm=question_generator)
        # loader.extr_load(source="data/obesity.txt")

    def add_document(self, source, metadata={}):
        self.loader.extr_load(source, metadata)